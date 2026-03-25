from typing import List, Tuple

# ── Reglas de negocio por tipo de métrica ─────────────
# Cada regla: (función_condición, tipo_alerta, mensaje, severidad)
REGLAS = {
    "humedad_suelo": [
        (lambda v: v < 20.0,  "sequia",   "< 20% — Marchitez inminente",        "alta"),
        (lambda v: v < 10.0,  "sequia",   "< 10% — Sequía crítica",              "critica"),
        (lambda v: v > 85.0,  "hongo",    "> 85% — Riesgo severo de hongos",     "alta"),
    ],
    "ph_suelo": [
        (lambda v: v < 5.5,   "ph",       "< 5.5 — Suelo muy ácido",             "alta"),
        (lambda v: v > 7.5,   "ph",       "> 7.5 — Suelo muy alcalino",           "alta"),
    ],
    "ec_suelo": [
        (lambda v: v > 3.0,   "salinidad","< 3.0 mS/cm — Exceso de sal",         "alta"),
        (lambda v: v > 4.0,   "salinidad","> 4.0 mS/cm — Salinidad crítica",     "critica"),
    ],
    "temperatura_suelo": [
        (lambda v: v < 12.0,  "helada",   "< 12°C — Raíz en estrés por frío",   "media"),
        (lambda v: v < 5.0,   "helada",   "< 5°C — Daño radicular inminente",    "critica"),
    ],
    "temperatura_aire": [
        (lambda v: v > 35.0,  "calor",    "> 35°C — Estrés térmico",             "alta"),
        (lambda v: v > 40.0,  "calor",    "> 40°C — Daño foliar crítico",        "critica"),
        (lambda v: v < 0.0,   "helada",   "< 0°C — Helada inminente",            "critica"),
        (lambda v: v < 5.0,   "helada",   "< 5°C — Riesgo de helada",            "alta"),
    ],
    "humedad_aire": [
        (lambda v: v > 85.0,  "hongo",    "> 85% — Riesgo de enfermedades",      "alta"),
        (lambda v: v > 95.0,  "hongo",    "> 95% — Condición de hongo crítica",  "critica"),
    ],
    "luz": [
        (lambda v: v < 2000,  "luz",      "< 2000 Lux — Déficit de luz solar",   "media"),
        (lambda v: v < 500,   "luz",      "< 500 Lux — Falta crítica de luz",    "alta"),
    ],
    "velocidad_viento": [
        (lambda v: v > 40.0,  "viento",   "> 40 km/h — Daño estructural",        "critica"),
        (lambda v: v > 25.0,  "viento",   "> 25 km/h — Viento fuerte",           "media"),
    ],
    "lluvia": [
        (lambda v: v > 50.0,  "inundacion","> 50 mm/h — Riesgo de inundación",   "critica"),
        (lambda v: v > 30.0,  "inundacion","> 30 mm/h — Lluvia intensa",          "alta"),
    ],
    "ph_agua": [
        (lambda v: v < 6.0,   "ph_agua",  "< 6.0 pH — Agua muy ácida",           "alta"),
        (lambda v: v > 7.5,   "ph_agua",  "> 7.5 pH — Agua muy alcalina",        "alta"),
    ],
    "caudal": [
        (lambda v: v > 25.0,  "fuga",     "> 25 L/min — Posible fuga",            "alta"),
        (lambda v: v > 28.0,  "fuga",     "> 28 L/min — Fuga crítica",            "critica"),
    ],
    "voltaje_bateria": [
        (lambda v: v < 3.5,   "bateria",  "< 3.5V — Batería baja",               "media"),
        (lambda v: v < 3.3,   "bateria",  "< 3.3V — Apagado inminente",          "critica"),
    ],
    "potencia_solar": [
        (lambda v: v < 12.0,  "solar",    "< 12V — Panel solar deficiente",      "media"),
    ],
    "latencia_red": [
        (lambda v: v > 1000,  "red",      "> 1000ms — Latencia alta",            "media"),
        (lambda v: v > 2000,  "red",      "> 2000ms — Latencia crítica",         "alta"),
    ],
    "ciclos_bateria": [
        (lambda v: v > 500,   "bateria",  "> 500 ciclos — Degradación",          "media"),
        (lambda v: v > 800,   "bateria",  "> 800 ciclos — Reemplazo urgente",    "alta"),
    ],
}


def aplicar_reglas(
    tipo_metrica: str,
    valor: float
) -> List[Tuple[str, str, str, str]]:
    """
    Aplica las reglas de negocio para una métrica.
    Retorna lista de (tipo_alerta, condicion, severidad, nombre_regla).
    """
    alertas = []
    reglas = REGLAS.get(tipo_metrica, [])

    for condicion_fn, tipo_alerta, mensaje, severidad in reglas:
        try:
            if condicion_fn(valor):
                alertas.append((
                    tipo_alerta,
                    mensaje,
                    severidad,
                    f"regla_{tipo_metrica}_{tipo_alerta}"
                ))
        except Exception:
            pass

    return alertas