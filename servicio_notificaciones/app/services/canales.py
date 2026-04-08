import logging
from sqlalchemy.orm import Session
from app.models.notificacion import Notificacion, LogEnvio
from app.services.formateador import formatear_notificacion, formatear_para_canal
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def crear_notificacion(
    db: Session,
    dispositivo_id: int,
    id_logico: str,
    tipo_alerta: str,
    tipo_metrica: str,
    valor: float,
    condicion: str,
    severidad: str,
    canal: str = "sistema",
    origen_evento: str = "alert.generated",
    usuario_id: int = None,
) -> Notificacion:
    contenido = formatear_notificacion(
        tipo_alerta=tipo_alerta,
        id_logico=id_logico,
        tipo_metrica=tipo_metrica,
        valor=valor,
        condicion=condicion,
        severidad=severidad
    )
    notificacion = Notificacion(
        usuario_id=usuario_id,
        dispositivo_id=dispositivo_id,
        id_logico=id_logico,
        titulo=contenido["titulo"],
        mensaje=contenido["mensaje"],
        tipo=tipo_alerta,
        severidad=severidad,
        canal=canal,
        estado="pendiente",
        origen_evento=origen_evento
    )
    db.add(notificacion)
    db.flush()
    return notificacion


def enviar_notificacion(db: Session, notificacion: Notificacion) -> bool:
    contenido_canal = formatear_para_canal(
        titulo=notificacion.titulo,
        mensaje=notificacion.mensaje,
        canal=notificacion.canal
    )
    try:
        if notificacion.canal == "sistema":
            logger.info(f"[SISTEMA] {contenido_canal['titulo']}\n{contenido_canal['mensaje']}")
            respuesta = "Notificacion registrada en sistema"
        elif notificacion.canal == "email":
            logger.info(f"[EMAIL] Enviando a usuario {notificacion.usuario_id}: {contenido_canal['titulo']}")
            respuesta = "Email simulado enviado"
        elif notificacion.canal == "sms":
            logger.info(f"[SMS] Enviando SMS: {contenido_canal['mensaje']}")
            respuesta = "SMS simulado enviado"
        elif notificacion.canal == "push":
            logger.info(f"[PUSH] Enviando push: {contenido_canal['titulo']}")
            respuesta = "Push notification simulada enviada"
        else:
            respuesta = f"Canal {notificacion.canal} no soportado"

        log = LogEnvio(
            notificacion_id=notificacion.id,
            canal=notificacion.canal,
            estado="enviado",
            respuesta=respuesta
        )
        db.add(log)
        notificacion.estado    = "enviada"
        notificacion.enviada_en = datetime.now(timezone.utc)
        db.commit()
        return True

    except Exception as e:
        log = LogEnvio(
            notificacion_id=notificacion.id,
            canal=notificacion.canal,
            estado="fallido",
            respuesta=str(e)
        )
        db.add(log)
        notificacion.estado = "fallida"
        db.commit()
        logger.error(f"Error enviando notificacion {notificacion.id}: {e}")
        return False


def procesar_alerta(db: Session, datos: dict) -> dict:
    severidad  = datos.get("severidad", "media")
    usuario_id = datos.get("usuario_id")

    canal = "sistema"
    if severidad == "critica":
        canal = "push"

    notificacion = crear_notificacion(
        db=db,
        usuario_id=usuario_id,
        dispositivo_id=datos.get("dispositivo_id"),
        id_logico=datos.get("id_logico"),
        tipo_alerta=datos.get("tipo_alerta", datos.get("tipo_metrica")),
        tipo_metrica=datos.get("tipo_metrica"),
        valor=datos.get("valor_detectado", datos.get("valor_metrica", 0)),
        condicion=datos.get("condicion", ""),
        severidad=severidad,
        canal=canal,
        origen_evento=datos.get("event", "alert.generated")
    )

    enviada = enviar_notificacion(db, notificacion)

    return {
        "notificacion_id": notificacion.id,
        "canal":           canal,
        "estado":          notificacion.estado,
        "enviada":         enviada
    }