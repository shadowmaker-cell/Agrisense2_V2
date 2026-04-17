from typing import List, Tuple

REGLAS = {
    # ── SUELO ──────────────────────────────────────────
    "humedad_suelo": [
        (lambda v: v < 10.0,  "sequia",      "< 10% — Sequía crítica",               "critica"),
        (lambda v: v < 20.0,  "sequia",      "< 20% — Marchitez inminente",          "alta"),
        (lambda v: v < 30.0,  "sequia",      "< 30% — Humedad baja",                 "media"),
        (lambda v: v > 90.0,  "hongo",       "> 90% — Saturación crítica",           "critica"),
        (lambda v: v > 85.0,  "hongo",       "> 85% — Riesgo severo de hongos",      "alta"),
    ],
    "ph_suelo": [
        (lambda v: v < 4.5,   "ph",          "< 4.5 — Suelo extremadamente ácido",   "critica"),
        (lambda v: v < 5.5,   "ph",          "< 5.5 — Suelo muy ácido",              "alta"),
        (lambda v: v > 8.0,   "ph",          "> 8.0 — Suelo muy alcalino",           "critica"),
        (lambda v: v > 7.5,   "ph",          "> 7.5 — Suelo alcalino",               "alta"),
    ],
    "conductividad_electrica": [
        (lambda v: v > 4.0,   "salinidad",   "> 4.0 mS/cm — Salinidad crítica",      "critica"),
        (lambda v: v > 3.0,   "salinidad",   "> 3.0 mS/cm — Exceso de sal",          "alta"),
        (lambda v: v > 2.0,   "salinidad",   "> 2.0 mS/cm — Salinidad elevada",      "media"),
    ],
    "ec_suelo": [
        (lambda v: v > 4.0,   "salinidad",   "> 4.0 mS/cm — Salinidad crítica",      "critica"),
        (lambda v: v > 3.0,   "salinidad",   "> 3.0 mS/cm — Exceso de sal",          "alta"),
    ],
    "temperatura_suelo": [
        (lambda v: v < 5.0,   "helada",      "< 5°C — Daño radicular inminente",     "critica"),
        (lambda v: v < 12.0,  "helada",      "< 12°C — Raíz en estrés por frío",     "media"),
        (lambda v: v > 35.0,  "calor",       "> 35°C — Suelo sobrecalentado",        "alta"),
    ],
    "nitrogeno": [
        (lambda v: v < 10.0,  "nutriente",   "< 10 mg/kg — Déficit crítico de N",    "critica"),
        (lambda v: v < 20.0,  "nutriente",   "< 20 mg/kg — Déficit de nitrógeno",    "alta"),
        (lambda v: v > 500.0, "nutriente",   "> 500 mg/kg — Exceso de nitrógeno",    "media"),
    ],
    "fosforo": [
        (lambda v: v < 5.0,   "nutriente",   "< 5 mg/kg — Déficit crítico de P",     "critica"),
        (lambda v: v < 15.0,  "nutriente",   "< 15 mg/kg — Déficit de fósforo",      "alta"),
    ],
    "potasio": [
        (lambda v: v < 50.0,  "nutriente",   "< 50 mg/kg — Déficit crítico de K",    "critica"),
        (lambda v: v < 100.0, "nutriente",   "< 100 mg/kg — Déficit de potasio",     "alta"),
    ],

    # ── CLIMA ──────────────────────────────────────────
    "temperatura_aire": [
        (lambda v: v > 40.0,  "calor",       "> 40°C — Daño foliar crítico",         "critica"),
        (lambda v: v > 35.0,  "calor",       "> 35°C — Estrés térmico",              "alta"),
        (lambda v: v > 30.0,  "calor",       "> 30°C — Temperatura elevada",         "media"),
        (lambda v: v < 0.0,   "helada",      "< 0°C — Helada inminente",             "critica"),
        (lambda v: v < 5.0,   "helada",      "< 5°C — Riesgo de helada",             "alta"),
    ],
    "humedad_aire": [
        (lambda v: v > 95.0,  "hongo",       "> 95% — Condición de hongo crítica",   "critica"),
        (lambda v: v > 85.0,  "hongo",       "> 85% — Riesgo de enfermedades",       "alta"),
        (lambda v: v < 20.0,  "sequia",      "< 20% — Aire muy seco",               "media"),
    ],
    "luz": [
        (lambda v: v < 500,   "luz",         "< 500 Lux — Falta crítica de luz",     "alta"),
        (lambda v: v < 2000,  "luz",         "< 2000 Lux — Déficit de luz solar",    "media"),
        (lambda v: v > 80000, "luz",         "> 80000 Lux — Exceso de radiación",    "media"),
    ],
    "luminosidad": [
        (lambda v: v < 500,   "luz",         "< 500 Lux — Falta crítica de luz",     "alta"),
        (lambda v: v < 2000,  "luz",         "< 2000 Lux — Déficit de luz solar",    "media"),
    ],
    "velocidad_viento": [
        (lambda v: v > 40.0,  "viento",      "> 40 km/h — Daño estructural",         "critica"),
        (lambda v: v > 25.0,  "viento",      "> 25 km/h — Viento fuerte",            "alta"),
        (lambda v: v > 15.0,  "viento",      "> 15 km/h — Viento moderado",          "media"),
    ],
    "precipitacion": [
        (lambda v: v > 50.0,  "inundacion",  "> 50 mm/h — Riesgo de inundación",     "critica"),
        (lambda v: v > 30.0,  "inundacion",  "> 30 mm/h — Lluvia intensa",           "alta"),
    ],
    "lluvia": [
        (lambda v: v > 50.0,  "inundacion",  "> 50 mm/h — Riesgo de inundación",     "critica"),
        (lambda v: v > 30.0,  "inundacion",  "> 30 mm/h — Lluvia intensa",           "alta"),
    ],

    # ── AGUA ───────────────────────────────────────────
    "caudal": [
        (lambda v: v > 28.0,  "fuga",        "> 28 L/min — Fuga crítica",            "critica"),
        (lambda v: v > 25.0,  "fuga",        "> 25 L/min — Posible fuga",            "alta"),
        (lambda v: v < 0.5,   "fuga",        "< 0.5 L/min — Caudal muy bajo",        "media"),
    ],
    "nivel_agua": [
        (lambda v: v < 10.0,  "nivel",       "< 10 cm — Tanque casi vacío",          "critica"),
        (lambda v: v < 20.0,  "nivel",       "< 20 cm — Nivel bajo de agua",         "alta"),
    ],
    "ph_agua": [
        (lambda v: v < 5.5,   "ph_agua",     "< 5.5 pH — Agua muy ácida",            "critica"),
        (lambda v: v < 6.0,   "ph_agua",     "< 6.0 pH — Agua ácida",                "alta"),
        (lambda v: v > 8.5,   "ph_agua",     "> 8.5 pH — Agua muy alcalina",         "critica"),
        (lambda v: v > 7.5,   "ph_agua",     "> 7.5 pH — Agua alcalina",             "alta"),
    ],
    "orp_agua": [
        (lambda v: v < 200,   "calidad_agua","< 200 mV — ORP bajo, agua contaminada","alta"),
        (lambda v: v < 100,   "calidad_agua","< 100 mV — ORP crítico",               "critica"),
    ],

    # ── PLANTA ─────────────────────────────────────────
    "diametro_tallo": [
        (lambda v: v < 1.0,   "crecimiento", "< 1 mm — Crecimiento muy lento",       "media"),
    ],
    "humedad_hoja": [
        (lambda v: v > 90.0,  "hongo",       "> 90% — Hoja saturada, riesgo hongo",  "alta"),
        (lambda v: v < 30.0,  "sequia",      "< 30% — Hoja muy seca",               "media"),
    ],

    # ── ACTUADORES ─────────────────────────────────────
    "estado_valvula": [
        (lambda v: v > 30.0,  "actuador",    "> 30 min abierta — Revisar válvula",   "media"),
    ],
    "tiempo_apertura": [
        (lambda v: v > 60.0,  "actuador",    "> 60 min abierta — Posible falla",     "alta"),
    ],
    "consumo_amperaje": [
        (lambda v: v > 15.0,  "electrico",   "> 15A — Consumo eléctrico alto",       "alta"),
        (lambda v: v > 20.0,  "electrico",   "> 20A — Sobrecarga eléctrica",         "critica"),
    ],
    "temperatura_motor": [
        (lambda v: v > 80.0,  "calor",       "> 80°C — Motor sobrecalentado",        "critica"),
        (lambda v: v > 65.0,  "calor",       "> 65°C — Temperatura motor alta",      "alta"),
    ],
    "consumo_watts": [
        (lambda v: v > 900.0, "electrico",   "> 900W — Consumo excesivo",            "alta"),
    ],
    "velocidad_ventilador": [
        (lambda v: v < 100.0, "actuador",    "< 100 RPM — Ventilador lento",         "media"),
    ],
    "horas_uso": [
        (lambda v: v > 8000,  "mantenimiento","> 8000h — Reemplazo de lámpara",      "alta"),
        (lambda v: v > 10000, "mantenimiento",">> 10000h — Lámpara crítica",         "critica"),
    ],

    # ── COMPUTACIÓN / RED ───────────────────────────────
    "uptime": [
        (lambda v: v < 60.0,  "sistema",     "< 60s — Reinicio reciente detectado",  "media"),
    ],
    "temperatura_cpu": [
        (lambda v: v > 85.0,  "calor",       "> 85°C — CPU sobrecalentada",          "critica"),
        (lambda v: v > 70.0,  "calor",       "> 70°C — Temperatura CPU alta",        "alta"),
    ],
    "uso_cpu": [
        (lambda v: v > 95.0,  "sistema",     "> 95% — CPU saturada",                 "critica"),
        (lambda v: v > 80.0,  "sistema",     "> 80% — Uso CPU muy alto",             "alta"),
    ],
    "uso_ram": [
        (lambda v: v > 95.0,  "sistema",     "> 95% — RAM saturada",                 "critica"),
        (lambda v: v > 85.0,  "sistema",     "> 85% — Uso RAM muy alto",             "alta"),
    ],
    "espacio_disco": [
        (lambda v: v > 95.0,  "sistema",     "> 95% — Disco lleno",                  "critica"),
        (lambda v: v > 85.0,  "sistema",     "> 85% — Espacio disco bajo",           "alta"),
    ],
    "latencia": [
        (lambda v: v > 2000,  "red",         "> 2000ms — Latencia crítica",          "critica"),
        (lambda v: v > 1000,  "red",         "> 1000ms — Latencia alta",             "alta"),
        (lambda v: v > 500,   "red",         "> 500ms — Latencia elevada",           "media"),
    ],
    "latencia_red": [
        (lambda v: v > 2000,  "red",         "> 2000ms — Latencia crítica",          "critica"),
        (lambda v: v > 1000,  "red",         "> 1000ms — Latencia alta",             "alta"),
    ],
    "perdida_paquetes": [
        (lambda v: v > 10.0,  "red",         "> 10% — Pérdida de paquetes crítica",  "critica"),
        (lambda v: v > 5.0,   "red",         "> 5% — Pérdida de paquetes alta",      "alta"),
    ],

    # ── ENERGÍA ────────────────────────────────────────
    "voltaje_panel": [
        (lambda v: v < 12.0,  "solar",       "< 12V — Panel solar deficiente",       "alta"),
        (lambda v: v < 8.0,   "solar",       "< 8V — Panel solar crítico",           "critica"),
    ],
    "potencia_solar": [
        (lambda v: v < 10.0,  "solar",       "< 10W — Generación solar muy baja",    "alta"),
    ],
    "corriente_panel": [
        (lambda v: v < 0.5,   "solar",       "< 0.5A — Corriente panel baja",        "media"),
    ],
    "voltaje_bateria": [
        (lambda v: v < 3.0,   "bateria",     "< 3.0V — Batería crítica",             "critica"),
        (lambda v: v < 3.3,   "bateria",     "< 3.3V — Apagado inminente",           "critica"),
        (lambda v: v < 3.5,   "bateria",     "< 3.5V — Batería baja",               "alta"),
        (lambda v: v > 4.3,   "bateria",     "> 4.3V — Sobrecarga batería",          "critica"),
    ],
    "capacidad_restante": [
        (lambda v: v < 10.0,  "bateria",     "< 10% — Batería crítica",              "critica"),
        (lambda v: v < 20.0,  "bateria",     "< 20% — Batería baja",                "alta"),
    ],
    "ciclos_carga": [
        (lambda v: v > 800,   "bateria",     "> 800 ciclos — Reemplazo urgente",     "alta"),
        (lambda v: v > 500,   "bateria",     "> 500 ciclos — Degradación",           "media"),
    ],
    "ciclos_bateria": [
        (lambda v: v > 800,   "bateria",     "> 800 ciclos — Reemplazo urgente",     "alta"),
        (lambda v: v > 500,   "bateria",     "> 500 ciclos — Degradación",           "media"),
    ],
    "temperatura_bateria": [
        (lambda v: v > 45.0,  "calor",       "> 45°C — Batería sobrecalentada",      "critica"),
        (lambda v: v > 35.0,  "calor",       "> 35°C — Temperatura batería alta",    "alta"),
    ],
    "carga_bateria": [
        (lambda v: v < 10.0,  "bateria",     "< 10% — UPS crítico",                  "critica"),
        (lambda v: v < 20.0,  "bateria",     "< 20% — UPS batería baja",            "alta"),
    ],
    "autonomia_restante": [
        (lambda v: v < 5.0,   "bateria",     "< 5 min — Autonomía UPS crítica",      "critica"),
        (lambda v: v < 15.0,  "bateria",     "< 15 min — Autonomía UPS baja",        "alta"),
    ],
    "voltaje_entrada": [
        (lambda v: v < 100.0, "electrico",   "< 100V — Voltaje entrada bajo",        "alta"),
        (lambda v: v > 130.0, "electrico",   "> 130V — Sobretensión",                "critica"),
    ],
    "voltaje_salida": [
        (lambda v: v < 100.0, "electrico",   "< 100V — Voltaje salida bajo",         "alta"),
        (lambda v: v > 130.0, "electrico",   "> 130V — Sobretensión salida",         "critica"),
    ],
    "nivel_combustible": [
        (lambda v: v < 10.0,  "combustible", "< 10% — Combustible crítico",          "critica"),
        (lambda v: v < 20.0,  "combustible", "< 20% — Combustible bajo",             "alta"),
    ],
    "frecuencia": [
        (lambda v: v < 58.0,  "electrico",   "< 58 Hz — Frecuencia baja",            "alta"),
        (lambda v: v > 62.0,  "electrico",   "> 62 Hz — Frecuencia alta",            "alta"),
    ],
    "temperatura_inversor": [
        (lambda v: v > 70.0,  "calor",       "> 70°C — Inversor sobrecalentado",     "critica"),
        (lambda v: v > 55.0,  "calor",       "> 55°C — Temperatura inversor alta",   "alta"),
    ],
    "eficiencia": [
        (lambda v: v < 80.0,  "sistema",     "< 80% — Eficiencia inversor baja",     "media"),
        (lambda v: v < 60.0,  "sistema",     "< 60% — Eficiencia crítica",           "alta"),
    ],
    "voltaje": [
        (lambda v: v < 100.0, "electrico",   "< 100V — Voltaje bajo",                "alta"),
        (lambda v: v > 240.0, "electrico",   "> 240V — Sobretensión",                "critica"),
    ],
    "corriente_salida": [
        (lambda v: v > 20.0,  "electrico",   "> 20A — Corriente alta",               "alta"),
    ],
    "temperatura": [
        (lambda v: v > 70.0,  "calor",       "> 70°C — Temperatura crítica",         "critica"),
        (lambda v: v > 55.0,  "calor",       "> 55°C — Temperatura alta",            "alta"),
    ],
}


def aplicar_reglas(tipo_metrica: str, valor: float) -> list:
    """Aplica reglas globales para una métrica."""
    alertas = []
    for condicion_fn, tipo_alerta, mensaje, severidad in REGLAS.get(tipo_metrica, []):
        try:
            if condicion_fn(valor):
                alertas.append((tipo_alerta, mensaje, severidad, f"regla_{tipo_metrica}_{tipo_alerta}"))
        except Exception:
            pass
    return alertas


def aplicar_limites_personalizados(
    tipo_metrica: str,
    valor: float,
    limite_minimo: float = None,
    limite_maximo: float = None,
) -> list:
    """
    Aplica límites personalizados configurados por el usuario.
    Tiene prioridad sobre las reglas globales.
    """
    alertas = []
    if limite_minimo is not None and valor < limite_minimo:
        alertas.append((
            "limite_minimo",
            f"Valor {valor} por debajo del límite mínimo configurado ({limite_minimo})",
            "alta",
            f"limite_min_{tipo_metrica}"
        ))
    if limite_maximo is not None and valor > limite_maximo:
        alertas.append((
            "limite_maximo",
            f"Valor {valor} supera el límite máximo configurado ({limite_maximo})",
            "alta",
            f"limite_max_{tipo_metrica}"
        ))
    return alertas