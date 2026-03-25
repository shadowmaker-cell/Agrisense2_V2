import logging
from sqlalchemy.orm import Session
from app.models.lectura import AlertaGenerada

logger = logging.getLogger(__name__)


def guardar_alerta(
    db: Session,
    dispositivo_id: int,
    id_logico: str,
    tipo_metrica: str,
    valor_detectado: float,
    condicion: str,
    severidad: str
) -> AlertaGenerada:
    """Persiste una alerta detectada en la base de datos."""
    alerta = AlertaGenerada(
        dispositivo_id=dispositivo_id,
        id_logico=id_logico,
        tipo_metrica=tipo_metrica,
        valor_detectado=valor_detectado,
        condicion=condicion,
        severidad=severidad
    )
    db.add(alerta)
    db.flush()
    logger.warning(
        f"ALERTA [{severidad.upper()}] {id_logico} — "
        f"{tipo_metrica}: {valor_detectado} — {condicion}"
    )
    return alerta


def procesar_alertas(
    db: Session,
    dispositivo_id: int,
    id_logico: str,
    tipo_metrica: str,
    valor: float,
    alertas_detectadas: list
) -> list:
    """
    Guarda todas las alertas detectadas para una lectura.
    Retorna lista de alertas guardadas.
    """
    guardadas = []
    for condicion, severidad in alertas_detectadas:
        alerta = guardar_alerta(
            db=db,
            dispositivo_id=dispositivo_id,
            id_logico=id_logico,
            tipo_metrica=tipo_metrica,
            valor_detectado=valor,
            condicion=condicion,
            severidad=severidad
        )
        guardadas.append(alerta)
    return guardadas