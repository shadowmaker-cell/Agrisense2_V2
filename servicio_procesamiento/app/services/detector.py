import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.evento import EventoProcesado, AlertaStream, ReglaAplicada
from app.services.reglas import aplicar_reglas

logger = logging.getLogger(__name__)


def procesar_evento_telemetria(db: Session, datos: dict) -> dict:
    dispositivo_id    = datos.get("dispositivo_id")
    id_logico         = datos.get("id_logico")
    tipo_metrica      = datos.get("tipo_metrica")
    valor_metrica     = datos.get("valor_metrica")
    unidad            = datos.get("unidad")
    timestamp_lectura = datos.get("timestamp_lectura")
    usuario_id        = datos.get("usuario_id")

    try:
        ts = datetime.fromisoformat(timestamp_lectura) if timestamp_lectura else datetime.now(timezone.utc)
    except Exception:
        ts = datetime.now(timezone.utc)

    evento = EventoProcesado(
        usuario_id=usuario_id,
        dispositivo_id=dispositivo_id,
        id_logico=id_logico,
        tipo_metrica=tipo_metrica,
        valor_metrica=valor_metrica,
        unidad=unidad,
        timestamp_lectura=ts,
        tiene_alerta=False,
    )
    db.add(evento)
    db.flush()

    alertas_detectadas = aplicar_reglas(tipo_metrica, valor_metrica)
    alertas_generadas  = []

    for tipo_alerta, condicion, severidad, nombre_regla in alertas_detectadas:
        alerta = AlertaStream(
            usuario_id=usuario_id,
            dispositivo_id=dispositivo_id,
            id_logico=id_logico,
            tipo_metrica=tipo_metrica,
            valor_detectado=valor_metrica,
            condicion=condicion,
            severidad=severidad,
            tipo_alerta=tipo_alerta,
            evento_id=evento.id,
        )
        db.add(alerta)
        db.flush()
        alertas_generadas.append(alerta)

        regla = ReglaAplicada(
            nombre_regla=nombre_regla,
            dispositivo_id=dispositivo_id,
            id_logico=id_logico,
            tipo_metrica=tipo_metrica,
            valor=valor_metrica,
            resultado="disparada",
            detalle=condicion,
        )
        db.add(regla)

        logger.warning(
            f"ALERTA [{severidad.upper()}] {id_logico} — "
            f"{tipo_metrica}: {valor_metrica} — {condicion}"
        )

    if alertas_generadas:
        evento.tiene_alerta = True

    db.commit()

    return {
        "evento_id":         evento.id,
        "alertas_generadas": len(alertas_generadas),
        "tipos_alerta":      [a.tipo_alerta for a in alertas_generadas],
    }