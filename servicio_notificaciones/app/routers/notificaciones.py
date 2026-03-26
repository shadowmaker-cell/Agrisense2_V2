from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.notificacion import Notificacion, PreferenciaNotificacion
from app.schemas.notificacion import (
    NotificacionRespuesta, NotificacionManualEntrada,
    PreferenciaEntrada, PreferenciaRespuesta,
    ResumenNotificaciones
)
from app.services.canales import procesar_alerta, crear_notificacion, enviar_notificacion

router = APIRouter(prefix="/api/v1/notificaciones", tags=["notificaciones"])


# ── POST /api/v1/notificaciones/enviar ────────────────
@router.post("/enviar", status_code=201)
def enviar_notificacion_manual(
    payload: NotificacionManualEntrada,
    db: Session = Depends(get_db)
):
    """Envía una notificación manualmente."""
    datos = {
        "dispositivo_id":  payload.dispositivo_id,
        "id_logico":       payload.id_logico,
        "tipo_alerta":     payload.tipo_alerta,
        "tipo_metrica":    payload.tipo_metrica,
        "valor_detectado": payload.valor,
        "condicion":       payload.condicion,
        "severidad":       payload.severidad,
        "event":           "manual"
    }
    resultado = procesar_alerta(db, datos)
    return {
        "mensaje":         "Notificación enviada exitosamente",
        "notificacion_id": resultado["notificacion_id"],
        "canal":           resultado["canal"],
        "estado":          resultado["estado"]
    }


# ── GET /api/v1/notificaciones ────────────────────────
@router.get("/", response_model=List[NotificacionRespuesta])
def listar_notificaciones(
    limite: int = 50,
    estado: str = None,
    severidad: str = None,
    db: Session = Depends(get_db)
):
    """Lista todas las notificaciones."""
    query = db.query(Notificacion)
    if estado:
        query = query.filter(Notificacion.estado == estado)
    if severidad:
        query = query.filter(Notificacion.severidad == severidad)
    return query.order_by(Notificacion.creada_en.desc()).limit(limite).all()


# ── GET /api/v1/notificaciones/{id} ───────────────────
@router.get("/{notificacion_id}", response_model=NotificacionRespuesta)
def obtener_notificacion(
    notificacion_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una notificación por ID."""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id
    ).first()
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notificacion


# ── PUT /api/v1/notificaciones/{id}/leer ──────────────
@router.put("/{notificacion_id}/leer")
def marcar_leida(
    notificacion_id: int,
    db: Session = Depends(get_db)
):
    """Marca una notificación como leída."""
    notificacion = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id
    ).first()
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    notificacion.leida = True
    db.commit()
    return {"mensaje": "Notificación marcada como leída"}


# ── GET /api/v1/notificaciones/dispositivo/{id_logico}
@router.get("/dispositivo/{id_logico}", response_model=List[NotificacionRespuesta])
def notificaciones_por_dispositivo(
    id_logico: str,
    limite: int = 20,
    db: Session = Depends(get_db)
):
    """Lista notificaciones de un dispositivo específico."""
    notificaciones = db.query(Notificacion).filter(
        Notificacion.id_logico == id_logico
    ).order_by(
        Notificacion.creada_en.desc()
    ).limit(limite).all()

    if not notificaciones:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron notificaciones para {id_logico}"
        )
    return notificaciones


# ── GET /api/v1/notificaciones/resumen ────────────────
@router.get("/resumen/general", response_model=ResumenNotificaciones)
def resumen_notificaciones(db: Session = Depends(get_db)):
    """Resumen general de notificaciones."""
    total     = db.query(Notificacion).count()
    pendientes = db.query(Notificacion).filter(Notificacion.estado == "pendiente").count()
    enviadas  = db.query(Notificacion).filter(Notificacion.estado == "enviada").count()
    fallidas  = db.query(Notificacion).filter(Notificacion.estado == "fallida").count()
    no_leidas = db.query(Notificacion).filter(Notificacion.leida == False).count()
    criticas  = db.query(Notificacion).filter(Notificacion.severidad == "critica").count()

    return ResumenNotificaciones(
        total=total,
        pendientes=pendientes,
        enviadas=enviadas,
        fallidas=fallidas,
        no_leidas=no_leidas,
        criticas=criticas
    )


# ── POST /api/v1/notificaciones/preferencias/{user_id}
@router.post("/preferencias/{usuario_id}", response_model=PreferenciaRespuesta)
def guardar_preferencias(
    usuario_id: int,
    payload: PreferenciaEntrada,
    db: Session = Depends(get_db)
):
    """Guarda las preferencias de notificación de un usuario."""
    preferencia = db.query(PreferenciaNotificacion).filter(
        PreferenciaNotificacion.usuario_id == usuario_id
    ).first()

    if preferencia:
        for key, val in payload.model_dump().items():
            setattr(preferencia, key, val)
    else:
        preferencia = PreferenciaNotificacion(
            usuario_id=usuario_id,
            **payload.model_dump()
        )
        db.add(preferencia)

    db.commit()
    db.refresh(preferencia)
    return preferencia