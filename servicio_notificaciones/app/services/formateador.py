from typing import Dict


# ── Emojis y títulos por tipo de alerta ───────────────
FORMATO_ALERTAS = {
    "helada":     {"emoji": "🥶", "titulo": "Alerta de Helada"},
    "sequia":     {"emoji": "🌵", "titulo": "Alerta de Sequía"},
    "hongo":      {"emoji": "🍄", "titulo": "Riesgo de Hongos"},
    "calor":      {"emoji": "🌡️", "titulo": "Estrés Térmico"},
    "viento":     {"emoji": "💨", "titulo": "Viento Peligroso"},
    "inundacion": {"emoji": "🌊", "titulo": "Riesgo de Inundación"},
    "ph":         {"emoji": "⚗️",  "titulo": "pH Fuera de Rango"},
    "ph_agua":    {"emoji": "💧", "titulo": "pH del Agua Anormal"},
    "salinidad":  {"emoji": "🧂", "titulo": "Exceso de Sal"},
    "fuga":       {"emoji": "🚰", "titulo": "Posible Fuga de Agua"},
    "bateria":    {"emoji": "🔋", "titulo": "Batería Baja"},
    "solar":      {"emoji": "☀️",  "titulo": "Panel Solar Deficiente"},
    "red":        {"emoji": "📡", "titulo": "Problema de Conectividad"},
    "luz":        {"emoji": "💡", "titulo": "Déficit de Luz Solar"},
}

COLORES_SEVERIDAD = {
    "critica": "🔴",
    "alta":    "🟠",
    "media":   "🟡",
    "baja":    "🟢",
}


def formatear_notificacion(
    tipo_alerta: str,
    id_logico: str,
    tipo_metrica: str,
    valor: float,
    condicion: str,
    severidad: str
) -> Dict[str, str]:
    """
    Formatea una alerta en una notificación legible para el agricultor.
    Retorna titulo y mensaje.
    """
    formato = FORMATO_ALERTAS.get(tipo_alerta, {
        "emoji": "⚠️",
        "titulo": "Alerta del Sistema"
    })

    color = COLORES_SEVERIDAD.get(severidad, "⚠️")

    titulo = (
        f"{color} {formato['emoji']} "
        f"{formato['titulo']} — {id_logico}"
    )

    mensaje = (
        f"Sensor: {id_logico}\n"
        f"Métrica: {tipo_metrica}\n"
        f"Valor detectado: {valor}\n"
        f"Condición: {condicion}\n"
        f"Severidad: {severidad.upper()}\n"
        f"Acción recomendada: Revisar el cultivo inmediatamente."
    )

    return {"titulo": titulo, "mensaje": mensaje}


def formatear_para_canal(
    titulo: str,
    mensaje: str,
    canal: str
) -> Dict[str, str]:
    """
    Adapta el formato del mensaje según el canal de envío.
    """
    if canal == "sms":
        # SMS corto — máximo 160 caracteres
        resumen = mensaje.split("\n")[3] if "\n" in mensaje else mensaje
        return {
            "titulo": titulo[:50],
            "mensaje": f"{titulo[:30]}: {resumen[:120]}"
        }
    elif canal == "email":
        # Email con formato HTML básico
        html = f"""
        <h2>{titulo}</h2>
        <hr>
        <pre>{mensaje}</pre>
        <hr>
        <small>AgriSense — Sistema de Monitoreo de Cultivos</small>
        """
        return {"titulo": titulo, "mensaje": html}
    elif canal == "push":
        # Push notification corta
        lineas = mensaje.split("\n")
        cuerpo = lineas[3] if len(lineas) > 3 else mensaje[:100]
        return {"titulo": titulo[:50], "mensaje": cuerpo[:100]}
    else:
        # Sistema — mensaje completo
        return {"titulo": titulo, "mensaje": mensaje}