from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.notificacion import Notificacion, PreferenciaNotificacion
from app.schemas.notificacion import (
    NotificacionRespuesta, NotificacionManualEntrada,
    PreferenciaEntrada, PreferenciaRespuesta,
    ResumenNotificaciones
)
from app.services.canales import procesar_alerta
from app.utils.jwt import get_usuario_id, get_usuario_id_opcional

router = APIRouter(prefix="/api/v1/notificaciones", tags=["notificaciones"])


@router.post("/enviar", status_code=201)
def enviar_notificacion_manual(
    payload: NotificacionManualEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    datos = {
        "usuario_id":      usuario_id,
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
        "mensaje":         "Notificacion enviada exitosamente",
        "notificacion_id": resultado["notificacion_id"],
        "canal":           resultado["canal"],
        "estado":          resultado["estado"]
    }


@router.get("/", response_model=List[NotificacionRespuesta])
def listar_notificaciones(
    request: Request,
    limite: int = 50,
    estado: str = None,
    severidad: str = None,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(Notificacion)
    if usuario_id:
        query = query.filter(Notificacion.usuario_id == usuario_id)
    if estado:
        query = query.filter(Notificacion.estado == estado)
    if severidad:
        query = query.filter(Notificacion.severidad == severidad)
    return query.order_by(Notificacion.creada_en.desc()).limit(limite).all()


@router.get("/resumen/general", response_model=ResumenNotificaciones)
def resumen_notificaciones(
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    q = db.query(Notificacion)
    if usuario_id:
        q = q.filter(Notificacion.usuario_id == usuario_id)

    return ResumenNotificaciones(
        total=q.count(),
        pendientes=q.filter(Notificacion.estado == "pendiente").count(),
        enviadas=q.filter(Notificacion.estado == "enviada").count(),
        fallidas=q.filter(Notificacion.estado == "fallida").count(),
        no_leidas=q.filter(Notificacion.leida == False).count(),
        criticas=q.filter(Notificacion.severidad == "critica").count(),
    )


@router.get("/dispositivo/{id_logico}", response_model=List[NotificacionRespuesta])
def notificaciones_por_dispositivo(
    id_logico: str,
    request: Request,
    limite: int = 20,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(Notificacion).filter(Notificacion.id_logico == id_logico)
    if usuario_id:
        query = query.filter(Notificacion.usuario_id == usuario_id)
    notificaciones = query.order_by(Notificacion.creada_en.desc()).limit(limite).all()
    if not notificaciones:
        raise HTTPException(status_code=404, detail=f"No se encontraron notificaciones para {id_logico}")
    return notificaciones


@router.get("/{notificacion_id}", response_model=NotificacionRespuesta)
def obtener_notificacion(
    notificacion_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(Notificacion).filter(Notificacion.id == notificacion_id)
    if usuario_id:
        query = query.filter(Notificacion.usuario_id == usuario_id)
    notificacion = query.first()
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    return notificacion


@router.put("/{notificacion_id}/leer")
def marcar_leida(
    notificacion_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(Notificacion).filter(Notificacion.id == notificacion_id)
    if usuario_id:
        query = query.filter(Notificacion.usuario_id == usuario_id)
    notificacion = query.first()
    if not notificacion:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    notificacion.leida = True
    db.commit()
    return {"mensaje": "Notificacion marcada como leida"}


@router.post("/preferencias/{usuario_id}", response_model=PreferenciaRespuesta)
def guardar_preferencias(
    usuario_id: int,
    payload: PreferenciaEntrada,
    db: Session = Depends(get_db)
):
    preferencia = db.query(PreferenciaNotificacion).filter(
        PreferenciaNotificacion.usuario_id == usuario_id
    ).first()
    if preferencia:
        for key, val in payload.model_dump().items():
            setattr(preferencia, key, val)
    else:
        preferencia = PreferenciaNotificacion(
            usuario_id=usuario_id, **payload.model_dump()
        )
        db.add(preferencia)
    db.commit()
    db.refresh(preferencia)
    return preferencia