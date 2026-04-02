import numpy as np
from typing import Dict, Any


# ── Factores de consumo de agua por cultivo (L/ha/dia) ──
AGUA_POR_CULTIVO = {
    "maiz":     450, "arroz":    800, "cafe":     300,
    "platano":  500, "yuca":     250, "papa":     400,
    "tomate":   550, "cana":     600, "cacao":    350,
    "aguacate": 400, "frijol":   200, "soya":     350,
    "sorgo":    280, "palma":    700, "flores":   600,
    "default":  400,
}

# ── Rendimiento base por cultivo (kg/ha) ─────────────
RENDIMIENTO_BASE = {
    "maiz":     5000,  "arroz":    6000, "cafe":     1200,
    "platano":  20000, "yuca":     18000,"papa":     25000,
    "tomate":   40000, "cana":     80000,"cacao":    900,
    "aguacate": 8000,  "frijol":   1500, "soya":     2800,
    "sorgo":    3500,  "palma":    18000,"flores":   50000,
    "default":  5000,
}

# ── Condiciones optimas por cultivo ──────────────────
CONDICIONES_OPTIMAS = {
    "temperatura_min": 15, "temperatura_max": 32,
    "humedad_min":     40, "humedad_max":     80,
    "ph_min":          5.5,"ph_max":          7.5,
}


def calcular_features_agua(data: Dict[str, Any]) -> np.ndarray:
    """
    Genera el vector de features para prediccion de necesidades hidricas.
    Features: [humedad_suelo, temperatura, lluvia, area, factor_cultivo, deficit_humedad]
    """
    humedad        = float(data.get("humedad_suelo", 50))
    temperatura    = float(data.get("temperatura_aire", 25))
    lluvia         = float(data.get("lluvia", 0))
    area           = float(data.get("area_hectareas", 1))
    cultivo        = str(data.get("tipo_cultivo", "default")).lower()
    factor_cultivo = AGUA_POR_CULTIVO.get(cultivo, AGUA_POR_CULTIVO["default"]) / 500
    deficit        = max(0, 60 - humedad) / 60

    return np.array([[humedad, temperatura, lluvia, area, factor_cultivo, deficit]])


def calcular_features_rendimiento(data: Dict[str, Any]) -> np.ndarray:
    """
    Genera el vector de features para prediccion de rendimiento.
    Features: [area, humedad, temperatura, ph, lluvia, factor_cultivo, score_condiciones]
    """
    area           = float(data.get("area_hectareas", 1))
    humedad        = float(data.get("humedad_suelo", 60))
    temperatura    = float(data.get("temperatura_aire", 25))
    ph             = float(data.get("ph_suelo", 6.5))
    lluvia         = float(data.get("lluvia_acumulada", 0))
    cultivo        = str(data.get("tipo_cultivo", "default")).lower()
    factor_cultivo = RENDIMIENTO_BASE.get(cultivo, RENDIMIENTO_BASE["default"]) / 10000

    # Score de condiciones 0-1
    temp_ok  = 1 if CONDICIONES_OPTIMAS["temperatura_min"] <= temperatura <= CONDICIONES_OPTIMAS["temperatura_max"] else 0.5
    hum_ok   = 1 if CONDICIONES_OPTIMAS["humedad_min"]     <= humedad     <= CONDICIONES_OPTIMAS["humedad_max"]     else 0.6
    ph_ok    = 1 if CONDICIONES_OPTIMAS["ph_min"]          <= ph          <= CONDICIONES_OPTIMAS["ph_max"]          else 0.4
    score    = (temp_ok + hum_ok + ph_ok) / 3

    return np.array([[area, humedad, temperatura, ph, lluvia, factor_cultivo, score]])


def calcular_features_riesgo(data: Dict[str, Any]) -> np.ndarray:
    """
    Genera el vector de features para prediccion de riesgo.
    Features: [temperatura, humedad_aire, humedad_suelo, viento, lluvia]
    """
    temperatura = float(data.get("temperatura_aire", 20))
    hum_aire    = float(data.get("humedad_aire", 60))
    hum_suelo   = float(data.get("humedad_suelo", 50))
    viento      = float(data.get("velocidad_viento", 0))
    lluvia      = float(data.get("lluvia", 0))

    return np.array([[temperatura, hum_aire, hum_suelo, viento, lluvia]])


def identificar_factores_riesgo_rendimiento(data: Dict[str, Any]) -> list:
    """Identifica factores de riesgo para el rendimiento basados en los datos."""
    riesgos = []
    humedad     = float(data.get("humedad_suelo", 60))
    temperatura = float(data.get("temperatura_aire", 25))
    ph          = float(data.get("ph_suelo", 6.5))

    if humedad < 30:
        riesgos.append("Deficit hidrico severo — humedad del suelo por debajo del umbral critico")
    elif humedad < 45:
        riesgos.append("Estres hidrico moderado — considerar riego suplementario")

    if temperatura > 35:
        riesgos.append("Estres termico alto — temperatura supera el umbral optimo del cultivo")
    elif temperatura < 12:
        riesgos.append("Temperatura baja — riesgo de afectacion en germinacion y desarrollo")

    if ph < 5.5:
        riesgos.append("Suelo acido — bloqueo de nutrientes, considerar encalado")
    elif ph > 7.5:
        riesgos.append("Suelo alcalino — reduccion de disponibilidad de micronutrientes")

    return riesgos if riesgos else ["Condiciones dentro de rangos aceptables"]


def generar_recomendaciones_rendimiento(data: Dict[str, Any], rendimiento_predicho: float) -> list:
    """Genera recomendaciones agronomicas basadas en los datos y el rendimiento predicho."""
    recomendaciones = []
    humedad     = float(data.get("humedad_suelo", 60))
    temperatura = float(data.get("temperatura_aire", 25))
    ph          = float(data.get("ph_suelo", 6.5))
    cultivo     = str(data.get("tipo_cultivo", "maiz")).lower()
    base        = RENDIMIENTO_BASE.get(cultivo, RENDIMIENTO_BASE["default"])

    if rendimiento_predicho < base * 0.6:
        recomendaciones.append("Rendimiento bajo esperado — revisar plan de fertilizacion y riego")
    if humedad < 40:
        recomendaciones.append("Implementar riego por goteo para optimizar uso del agua")
    if ph < 5.8:
        recomendaciones.append("Aplicar cal dolomitica para corregir acidez del suelo")
    if temperatura > 33:
        recomendaciones.append("Considerar cobertura vegetal o sombreo para reducir temperatura")

    recomendaciones.append("Monitorear semanalmente con los sensores IoT para ajustar el plan")

    return recomendaciones