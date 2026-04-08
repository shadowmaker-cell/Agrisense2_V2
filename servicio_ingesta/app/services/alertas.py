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
    severidad: str,
    usuario_id: int = None,
) -> AlertaGenerada:
    alerta = AlertaGenerada(
        usuario_id=usuario_id,
        dispositivo_id=dispositivo_id,
        id_logico=id_logico,
        tipo_metrica=tipo_metrica,
        valor_detectado=valor_detectado,
        condicion=condicion,
        severidad=severidad,
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
    alertas_detectadas: list,
    usuario_id: int = None,
) -> list:
    guardadas = []
    for condicion, severidad in alertas_detectadas:
        alerta = guardar_alerta(
            db=db,
            dispositivo_id=dispositivo_id,
            id_logico=id_logico,
            tipo_metrica=tipo_metrica,
            valor_detectado=valor,
            condicion=condicion,
            severidad=severidad,
            usuario_id=usuario_id,
        )
        guardadas.append(alerta)
    return guardadas