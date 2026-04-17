def generar_desde_alerta(db: Session, datos_alerta: dict) -> dict:
    """
    Genera recomendaciones automáticamente a partir de una alerta detectada.
    """
    tipo_metrica   = datos_alerta.get("tipo_metrica", "")
    valor          = datos_alerta.get("valor", 0)
    id_logico      = datos_alerta.get("id_logico")
    parcela_id     = datos_alerta.get("parcela_id")
    usuario_id     = datos_alerta.get("usuario_id")

    METRICA_PARAM = {
        "humedad_suelo":          "humedad_suelo",
        "temperatura_aire":       "temperatura_aire",
        "temperatura_suelo":      "temperatura_suelo",
        "ph_suelo":               "ph_suelo",
        "velocidad_viento":       "velocidad_viento",
        "humedad_aire":           "humedad_aire",
        "lluvia":                 "lluvia",
        "precipitacion":          "lluvia",
        "conductividad_electrica":"ec_suelo",
    }

    data = {
        "parcela_id":    parcela_id,
        "id_logico":     id_logico,
        "usuario_id":    usuario_id,
        "tipo_cultivo":  datos_alerta.get("tipo_cultivo", "maiz"),
        "area_hectareas":datos_alerta.get("area_hectareas", 1.0),
    }

    param = METRICA_PARAM.get(tipo_metrica)
    if param:
        data[param] = valor

    return generar_recomendaciones(db, data)