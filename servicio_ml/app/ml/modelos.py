import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import os
from app.ml.features import (
    AGUA_POR_CULTIVO, RENDIMIENTO_BASE, CONDICIONES_OPTIMAS,
    calcular_features_agua, calcular_features_rendimiento, calcular_features_riesgo,
    identificar_factores_riesgo_rendimiento, generar_recomendaciones_rendimiento
)

# ── Datos sinteticos de entrenamiento ────────────────

def _generar_datos_agua(n=500):
    """Genera datos sinteticos para entrenamiento del modelo de agua."""
    np.random.seed(42)
    X, y = [], []
    for _ in range(n):
        humedad     = np.random.uniform(5, 95)
        temperatura = np.random.uniform(10, 42)
        lluvia      = np.random.uniform(0, 80)
        area        = np.random.uniform(0.5, 50)
        factor      = np.random.uniform(0.4, 1.4)
        deficit     = max(0, 60 - humedad) / 60

        # Logica agronomica para calcular agua necesaria
        base        = factor * 500 * area
        ajuste_temp = 1 + max(0, temperatura - 25) * 0.02
        ajuste_hum  = max(0, 1 - humedad / 100)
        ajuste_lluvia = max(0, 1 - lluvia / 60)
        litros      = base * ajuste_temp * ajuste_hum * ajuste_lluvia
        litros      = max(0, litros + np.random.normal(0, litros * 0.05))

        X.append([humedad, temperatura, lluvia, area, factor, deficit])
        y.append(litros)

    return np.array(X), np.array(y)


def _generar_datos_rendimiento(n=500):
    """Genera datos sinteticos para entrenamiento del modelo de rendimiento."""
    np.random.seed(42)
    X, y = [], []
    cultivos = list(RENDIMIENTO_BASE.keys())
    for _ in range(n):
        area        = np.random.uniform(0.5, 100)
        humedad     = np.random.uniform(20, 95)
        temperatura = np.random.uniform(10, 42)
        ph          = np.random.uniform(4.5, 8.5)
        lluvia      = np.random.uniform(0, 300)
        cultivo     = np.random.choice(cultivos)
        factor      = RENDIMIENTO_BASE[cultivo] / 10000

        temp_ok  = 1 if 15 <= temperatura <= 32 else 0.5
        hum_ok   = 1 if 40 <= humedad     <= 80 else 0.6
        ph_ok    = 1 if 5.5 <= ph          <= 7.5 else 0.4
        score    = (temp_ok + hum_ok + ph_ok) / 3

        base        = RENDIMIENTO_BASE[cultivo]
        rendimiento = base * score * (1 + np.random.normal(0, 0.1))
        rendimiento = max(0, rendimiento)

        X.append([area, humedad, temperatura, ph, lluvia, factor, score])
        y.append(rendimiento)

    return np.array(X), np.array(y)


def _generar_datos_riesgo(n=500):
    """Genera datos sinteticos para entrenamiento del modelo de riesgo."""
    np.random.seed(42)
    X, y = [], []
    for _ in range(n):
        temperatura = np.random.uniform(-10, 42)
        hum_aire    = np.random.uniform(10, 100)
        hum_suelo   = np.random.uniform(5, 95)
        viento      = np.random.uniform(0, 80)
        lluvia      = np.random.uniform(0, 100)

        # Logica de riesgo: 0=bajo, 1=medio, 2=alto, 3=critico
        riesgo = 0
        if temperatura < 2 or temperatura > 38:
            riesgo += 2
        if hum_suelo < 20 or lluvia > 60:
            riesgo += 1
        if viento > 40:
            riesgo += 1
        riesgo = min(3, riesgo)

        X.append([temperatura, hum_aire, hum_suelo, viento, lluvia])
        y.append(riesgo)

    return np.array(X), np.array(y)


# ── Modelos entrenados en memoria ────────────────────
_modelo_agua        = None
_modelo_rendimiento = None
_modelo_riesgo      = None


def _entrenar_modelo_agua():
    X, y = _generar_datos_agua()
    modelo = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    modelo.fit(X, y)
    return modelo


def _entrenar_modelo_rendimiento():
    X, y = _generar_datos_rendimiento()
    modelo = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
    modelo.fit(X, y)
    return modelo


def _entrenar_modelo_riesgo():
    X, y = _generar_datos_riesgo()
    modelo = Pipeline([
        ('scaler', StandardScaler()),
        ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42))
    ])
    modelo.fit(X, y)
    return modelo


def get_modelo_agua():
    global _modelo_agua
    if _modelo_agua is None:
        _modelo_agua = _entrenar_modelo_agua()
    return _modelo_agua


def get_modelo_rendimiento():
    global _modelo_rendimiento
    if _modelo_rendimiento is None:
        _modelo_rendimiento = _entrenar_modelo_rendimiento()
    return _modelo_rendimiento


def get_modelo_riesgo():
    global _modelo_riesgo
    if _modelo_riesgo is None:
        _modelo_riesgo = _entrenar_modelo_riesgo()
    return _modelo_riesgo


# ── Funciones de prediccion ──────────────────────────
NIVELES_RIESGO = {0: "bajo", 1: "medio", 2: "alto", 3: "critico"}

ACCIONES_RIESGO = {
    "helada": {
        "bajo":    ["Monitorear temperatura nocturna"],
        "medio":   ["Preparar sistemas de calefaccion", "Cubrir cultivos sensibles"],
        "alto":    ["Activar calefaccion inmediatamente", "Cosechar cultivos maduros"],
        "critico": ["Emergencia agronomica — activar todos los protocolos de proteccion"],
    },
    "sequia": {
        "bajo":    ["Monitorear niveles de humedad del suelo"],
        "medio":   ["Aumentar frecuencia de riego", "Aplicar mulch para retener humedad"],
        "alto":    ["Riego de emergencia", "Reducir densidad de cultivos"],
        "critico": ["Riego masivo de emergencia — riesgo de perdida total de cosecha"],
    },
    "hongo": {
        "bajo":    ["Mejorar ventilacion entre plantas"],
        "medio":   ["Aplicar fungicida preventivo", "Reducir riego nocturno"],
        "alto":    ["Aplicar fungicida sistemico", "Eliminar plantas afectadas"],
        "critico": ["Tratamiento intensivo inmediato — aislar sectores afectados"],
    },
    "inundacion": {
        "bajo":    ["Verificar sistema de drenaje"],
        "medio":   ["Activar bombas de drenaje", "Elevar camellones"],
        "alto":    ["Evacuar equipos del campo", "Activar canales de desfogue"],
        "critico": ["Emergencia — proteger infraestructura y personal"],
    },
}


def predecir_agua(data: dict) -> dict:
    """Predice los litros de agua necesarios para la parcela."""
    modelo   = get_modelo_agua()
    features = calcular_features_agua(data)
    litros   = float(modelo.predict(features)[0])
    litros   = max(0, litros)

    humedad = float(data.get("humedad_suelo", 50))
    if humedad < 20:
        urgencia, frecuencia = "critica", 6
    elif humedad < 35:
        urgencia, frecuencia = "alta", 12
    elif humedad < 50:
        urgencia, frecuencia = "media", 24
    else:
        urgencia, frecuencia = "baja", 48

    cultivo    = str(data.get("tipo_cultivo", "maiz")).lower()
    confianza  = 0.87 if cultivo in AGUA_POR_CULTIVO else 0.72
    explicacion = (
        f"Con humedad del suelo al {humedad:.1f}% y temperatura de "
        f"{data.get('temperatura_aire', 25):.1f}C, el cultivo de {cultivo} "
        f"requiere aproximadamente {litros:.0f} litros. "
        f"Urgencia de riego: {urgencia}."
    )

    return {
        "litros_recomendados": round(litros, 1),
        "frecuencia_horas":    frecuencia,
        "urgencia":            urgencia,
        "confianza":           confianza,
        "explicacion":         explicacion,
    }


def predecir_rendimiento(data: dict) -> dict:
    """Predice el rendimiento esperado del cultivo en kg/ha."""
    modelo   = get_modelo_rendimiento()
    features = calcular_features_rendimiento(data)
    rend_ha  = float(modelo.predict(features)[0])
    rend_ha  = max(0, rend_ha)
    area     = float(data.get("area_hectareas", 1))
    total    = rend_ha * area
    cultivo  = str(data.get("tipo_cultivo", "maiz")).lower()
    base     = RENDIMIENTO_BASE.get(cultivo, RENDIMIENTO_BASE["default"])

    if rend_ha >= base * 0.85:
        calificacion = "excelente"
    elif rend_ha >= base * 0.65:
        calificacion = "bueno"
    elif rend_ha >= base * 0.45:
        calificacion = "regular"
    else:
        calificacion = "bajo"

    factores       = identificar_factores_riesgo_rendimiento(data)
    recomendaciones = generar_recomendaciones_rendimiento(data, rend_ha)
    confianza      = 0.82 if cultivo in RENDIMIENTO_BASE else 0.68

    return {
        "rendimiento_kg_ha":    round(rend_ha, 1),
        "rendimiento_total_kg": round(total, 1),
        "calificacion":         calificacion,
        "confianza":            confianza,
        "factores_riesgo":      factores,
        "recomendaciones":      recomendaciones,
    }


def predecir_riesgo(data: dict) -> dict:
    """Predice el nivel de riesgo agronomico."""
    modelo     = get_modelo_riesgo()
    features   = calcular_features_riesgo(data)
    nivel_num  = int(modelo.predict(features)[0])
    proba      = modelo.predict_proba(features)[0]
    tipo_riesgo = str(data.get("tipo_riesgo", "helada")).lower()
    nivel      = NIVELES_RIESGO.get(nivel_num, "bajo")
    acciones   = ACCIONES_RIESGO.get(tipo_riesgo, {}).get(nivel, ["Monitorear condiciones"])
    confianza  = float(proba[nivel_num])

    return {
        "tipo_riesgo":  tipo_riesgo,
        "probabilidad": round(confianza, 3),
        "nivel":        nivel,
        "acciones":     acciones,
        "confianza":    round(confianza, 3),
    }