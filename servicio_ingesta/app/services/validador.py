from datetime import datetime, timezone
from typing import Tuple

# ── Rangos válidos por tipo de métrica ────────────────
# Basados en las tablas del proyecto
RANGOS = {
    # Suelo
    "humedad_suelo":      (0.0,   100.0),
    "ph_suelo":           (0.0,   14.0),
    "ec_suelo":           (0.0,   5.0),
    "temperatura_suelo":  (-10.0, 85.0),
    # Ambiental
    "temperatura_aire":   (-40.0, 80.0),
    "humedad_aire":       (0.0,   100.0),
    "luz":                (0.0,   65000.0),
    "velocidad_viento":   (0.0,   150.0),
    "lluvia":             (0.0,   500.0),
    # Agua
    "ph_agua":            (0.0,   14.0),
    "caudal":             (1.0,   30.0),
    "voltaje_valvula":    (0.0,   500.0),
    "consumo_bomba":      (0.0,   220.0),
    # Infraestructura
    "voltaje_bateria":    (0.0,   5.0),
    "potencia_solar":     (0.0,   50.0),
    "latencia_red":       (0.0,   2000.0),
    "ciclos_bateria":     (0.0,   1000.0),
}

# ── Umbrales de alerta por tipo de métrica ────────────
ALERTAS = {
    "humedad_suelo":     [
        (lambda v: v < 20.0,  "< 20% — Marchitez inminente",      "alta"),
        (lambda v: v > 90.0,  "> 90% — Exceso de humedad",         "media"),
    ],
    "ph_suelo":          [
        (lambda v: v < 5.5,   "< 5.5 — Suelo muy ácido (bloqueo)", "alta"),
        (lambda v: v > 7.5,   "> 7.5 — Suelo muy alcalino",        "alta"),
    ],
    "ec_suelo":          [
        (lambda v: v > 3.0,   "> 3.0 mS/cm — Exceso de sal",       "alta"),
    ],
    "temperatura_suelo": [
        (lambda v: v < 12.0,  "< 12°C — Raíz latente",             "media"),
    ],
    "temperatura_aire":  [
        (lambda v: v > 35.0,  "> 35°C — Estrés térmico",           "alta"),
        (lambda v: v < 0.0,   "< 0°C — Riesgo de helada",          "critica"),
    ],
    "humedad_aire":      [
        (lambda v: v > 85.0,  "> 85% — Riesgo de hongos",          "alta"),
    ],
    "luz":               [
        (lambda v: v < 2000,  "< 2000 Lux — Falta de luz solar",   "media"),
    ],
    "velocidad_viento":  [
        (lambda v: v > 40.0,  "> 40 km/h — Daño estructural",      "critica"),
    ],
    "lluvia":            [
        (lambda v: v > 50.0,  "> 50 mm/h — Riesgo de inundación",  "critica"),
    ],
    "ph_agua":           [
        (lambda v: v < 6.0 or v > 7.0, "pH fuera de rango óptimo 6.0-7.0", "alta"),
    ],
    "caudal":            [
        (lambda v: v > 25.0,  "> 25 L/min — Posible fuga",         "alta"),
    ],
    "voltaje_bateria":   [
        (lambda v: v < 3.3,   "< 3.3V — Apagado inminente",        "critica"),
    ],
    "potencia_solar":    [
        (lambda v: v < 12.0,  "< 12V en horas de sol",             "media"),
    ],
    "latencia_red":      [
        (lambda v: v > 2000,  "> 2000ms — Latencia crítica",        "alta"),
    ],
    "ciclos_bateria":    [
        (lambda v: v > 500,   "> 500 ciclos — Degradación",         "media"),
    ],
}


def validar_lectura(tipo_metrica: str, valor: float) -> Tuple[str, str]:
    """
    Valida una lectura contra los rangos permitidos.
    Retorna (bandera_calidad, razon_error).
    """
    rango = RANGOS.get(tipo_metrica)
    if rango is None:
        return "sospechoso", f"Métrica '{tipo_metrica}' no reconocida"

    minimo, maximo = rango
    if valor < minimo or valor > maximo:
        return "invalido", f"Valor {valor} fuera de rango [{minimo}, {maximo}]"

    return "valido", ""


def detectar_alertas(tipo_metrica: str, valor: float) -> list:
    """
    Detecta condiciones de alerta para una lectura.
    Retorna lista de (condicion, severidad).
    """
    alertas = []
    reglas = ALERTAS.get(tipo_metrica, [])
    for condicion_fn, mensaje, severidad in reglas:
        try:
            if condicion_fn(valor):
                alertas.append((mensaje, severidad))
        except Exception:
            pass
    return alertas


def normalizar_timestamp(ts=None) -> datetime:
    """Retorna timestamp actual si no se proporciona uno."""
    if ts is None:
        return datetime.now(timezone.utc)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts