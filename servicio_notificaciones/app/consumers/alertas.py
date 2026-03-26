import json
import logging
import threading
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from app.config import settings
from app.database import SessionLocal
from app.services.canales import procesar_alerta

logger = logging.getLogger(__name__)


def crear_consumidor():
    try:
        return KafkaConsumer(
            "alert.generated",
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
    def consumir():
        logger.info("Notification Service iniciado")
        while True:
            consumer = crear_consumidor()
            if not consumer:
                import time
                logger.warning("Reintentando conexion a Kafka en 5s...")
                time.sleep(5)
                continue
            try:
                for mensaje in consumer:
                    try:
                        datos = mensaje.value
                        evento = datos.get("event", "")
                        if evento not in ("alert.generated", "alert.frost.risk",
                                         "alert.pest.risk", "alert.drought.risk"):
                            continue
                        db = SessionLocal()
                        try:
                            resultado = procesar_alerta(db, datos)
                            logger.info(
                                f"Notificacion generada "
                                f"id={resultado['notificacion_id']} "
                                f"canal={resultado['canal']} "
                                f"estado={resultado['estado']}"
                            )
                        finally:
                            db.close()
                    except Exception as e:
                        logger.error(f"Error procesando alerta: {e}")
            except Exception as e:
                logger.error(f"Error en consumidor: {e}")
            finally:
                try:
                    consumer.close()
                except Exception:
                    pass

    hilo = threading.Thread(target=consumir, daemon=True)
    hilo.start()
    logger.info("Hilo consumidor de alertas iniciado")
    return hilo