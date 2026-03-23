import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from app.config import settings

logger = logging.getLogger(__name__)


def _obtener_productor():
    try:
        return KafkaProducer(
            bootstrap_servers=settings.BROKER_URL,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=3
        )
    except KafkaError as e:
        logger.warning(f"Kafka no disponible: {e}. Evento no publicado.")
        return None


def publicar_dispositivo_creado(dispositivo) -> None:
    """
    Publica evento device.created en Kafka.
    Consumidores: microservicio de ingesta y otros servicios.
    """
    productor = _obtener_productor()
    if not productor:
        return

    payload = {
        "evento":             "dispositivo.creado",
        "dispositivo_id":     dispositivo.id,
        "id_logico":          dispositivo.id_logico,
        "numero_serial":      dispositivo.numero_serial,
        "tipo_dispositivo_id": dispositivo.tipo_dispositivo_id,
        "estado":             dispositivo.estado,
        "registrado_en":      str(dispositivo.registrado_en),
    }
    productor.send("dispositivo.creado", value=payload)
    productor.flush()
    logger.info(f"Evento dispositivo.creado publicado — id={dispositivo.id}")


def publicar_dispositivo_actualizado(dispositivo) -> None:
    """
    Publica evento dispositivo.actualizado en Kafka.
    Consumidores: otros servicios que necesiten el estado actualizado.
    """
    productor = _obtener_productor()
    if not productor:
        return

    payload = {
        "evento":            "dispositivo.actualizado",
        "dispositivo_id":    dispositivo.id,
        "id_logico":         dispositivo.id_logico,
        "numero_serial":     dispositivo.numero_serial,
        "estado":            dispositivo.estado,
        "version_firmware":  dispositivo.version_firmware,
    }
    productor.send("dispositivo.actualizado", value=payload)
    productor.flush()
    logger.info(f"Evento dispositivo.actualizado publicado — id={dispositivo.id}")