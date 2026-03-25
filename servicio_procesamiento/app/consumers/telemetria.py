import json
import logging
import threading
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from app.config import settings
from app.database import SessionLocal
from app.services.detector import procesar_evento_telemetria

logger = logging.getLogger(__name__)


def crear_consumidor():
    """Crea el consumidor Kafka para el tópico telemetry.raw."""
    try:
        return KafkaConsumer(
            "telemetry.raw",
            bootstrap_servers=settings.BROKER_URL,
            group_id=settings.KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            consumer_timeout_ms=1000
        )
    except KafkaError as e:
        logger.warning(f"Kafka no disponible: {e}")
        return None


def iniciar_consumidor():
    """Inicia el consumidor en un hilo separado."""
    def consumir():
        logger.info("Stream Processor iniciado — escuchando telemetry.raw")
        while True:
            consumer = crear_consumidor()
            if not consumer:
                import time
                logger.warning("Reintentando conexión a Kafka en 5s...")
                time.sleep(5)
                continue
            try:
                for mensaje in consumer:
                    try:
                        datos = mensaje.value
                        db = SessionLocal()
                        try:
                            resultado = procesar_evento_telemetria(db, datos)
                            if resultado["alertas_generadas"] > 0:
                                logger.warning(
                                    f"Procesado {datos.get('id_logico')} — "
                                    f"{resultado['alertas_generadas']} alertas: "
                                    f"{resultado['tipos_alerta']}"
                                )
                        finally:
                            db.close()
                    except Exception as e:
                        logger.error(f"Error procesando mensaje: {e}")
            except Exception as e:
                logger.error(f"Error en consumidor Kafka: {e}")
            finally:
                try:
                    consumer.close()
                except Exception:
                    pass

    hilo = threading.Thread(target=consumir, daemon=True)
    hilo.start()
    logger.info("Hilo consumidor Kafka iniciado")
    return hilo