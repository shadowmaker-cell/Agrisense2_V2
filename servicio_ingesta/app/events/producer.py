import json
import logging
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from app.config import settings

logger = logging.getLogger(__name__)


def _get_producer():
    """Crea el productor Kafka. Si no está disponible retorna None."""
    try:
        return KafkaProducer(
            bootstrap_servers=settings.BROKER_URL,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            retries=3
        )
    except KafkaError as e:
        logger.warning(f"Kafka no disponible: {e}. Evento no publicado.")
        return None


def publish_telemetry_raw(lectura) -> None:
    """
    Publica evento telemetry.raw en Kafka.
    Consumidores: Stream Processor, ML Prediction Service.
    """
    producer = _get_producer()
    if not producer:
        return

    payload = {
        "event":            "telemetry.raw",
        "lectura_id":       lectura.id,
        "dispositivo_id":   lectura.dispositivo_id,
        "id_logico":        lectura.id_logico,
        "tipo_metrica":     lectura.tipo_metrica,
        "valor_metrica":    lectura.valor_metrica,
        "unidad":           lectura.unidad,
        "timestamp_lectura": str(lectura.timestamp_lectura),
        "bandera_calidad":  lectura.bandera_calidad,
    }
    producer.send("telemetry.raw", value=payload)
    producer.flush()
    logger.info(
        f"Evento telemetry.raw publicado — "
        f"{lectura.id_logico} / {lectura.tipo_metrica}: {lectura.valor_metrica}"
    )


def publish_alert_generated(alerta) -> None:
    """
    Publica evento alert.generated en Kafka.
    Consumidores: Notification Service, Recommendation Engine.
    """
    producer = _get_producer()
    if not producer:
        return

    payload = {
        "event":            "alert.generated",
        "alerta_id":        alerta.id,
        "dispositivo_id":   alerta.dispositivo_id,
        "id_logico":        alerta.id_logico,
        "tipo_metrica":     alerta.tipo_metrica,
        "valor_detectado":  alerta.valor_detectado,
        "condicion":        alerta.condicion,
        "severidad":        alerta.severidad,
        "generada_en":      str(alerta.generada_en),
    }
    producer.send("alert.generated", value=payload)
    producer.flush()
    logger.warning(
        f"Evento alert.generated publicado — "
        f"[{alerta.severidad.upper()}] {alerta.id_logico}: {alerta.condicion}"
    )


def publish_batch_completed(lote) -> None:
    """
    Publica evento batch.completed en Kafka.
    Consumidores: Monitoreo y observabilidad.
    """
    producer = _get_producer()
    if not producer:
        return

    payload = {
        "event":               "batch.completed",
        "lote_id":             lote.id,
        "tipo_origen":         lote.tipo_origen,
        "total_registros":     lote.total_registros,
        "registros_validos":   lote.registros_validos,
        "registros_invalidos": lote.registros_invalidos,
        "estado":              lote.estado,
        "recibido_en":         str(lote.recibido_en),
    }
    producer.send("batch.completed", value=payload)
    producer.flush()
    logger.info(f"Evento batch.completed publicado — lote_id={lote.id}")