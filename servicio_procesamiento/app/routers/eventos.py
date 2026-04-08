from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.evento import EventoProcesado, AlertaStream
from app.schemas.evento import (
    EventoRespuesta, AlertaStreamRespuesta,
    ResumenProcesamiento, ProcesarManualEntrada
)
from app.services.detector import procesar_evento_telemetria
from app.utils.jwt import get_usuario_id, get_usuario_id_opcional

router = APIRouter(prefix="/api/v1/procesamiento", tags=["procesamiento"])


@router.post("/manual", status_code=201)
def procesar_manual(
    payload: ProcesarManualEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    """Procesa una lectura manualmente sin pasar por Kafka."""
    usuario_id = get_usuario_id_opcional(request)
    datos = {
        "dispositivo_id":    payload.dispositivo_id,
        "id_logico":         payload.id_logico,
        "tipo_metrica":      payload.tipo_metrica,
        "valor_metrica":     payload.valor_metrica,
        "unidad":            payload.unidad,
        "timestamp_lectura": None,
        "usuario_id":        usuario_id,
    }
    resultado = procesar_evento_telemetria(db, datos)
    return {
        "mensaje":           "Evento procesado exitosamente",
        "evento_id":         resultado["evento_id"],
        "alertas_generadas": resultado["alertas_generadas"],
        "tipos_alerta":      resultado["tipos_alerta"]
    }


@router.get("/eventos", response_model=List[EventoRespuesta])
def listar_eventos(
    request: Request,
    limite: int = 50,
    con_alerta: bool = None,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(EventoProcesado)
    if usuario_id:
        query = query.filter(EventoProcesado.usuario_id == usuario_id)
    if con_alerta is not None:
        query = query.filter(EventoProcesado.tiene_alerta == con_alerta)
    return query.order_by(EventoProcesado.procesado_en.desc()).limit(limite).all()


@router.get("/eventos/{id_logico}", response_model=List[EventoRespuesta])
def eventos_por_dispositivo(
    id_logico: str,
    request: Request,
    limite: int = 20,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(EventoProcesado).filter(EventoProcesado.id_logico == id_logico)
    if usuario_id:
        query = query.filter(EventoProcesado.usuario_id == usuario_id)
    eventos = query.order_by(EventoProcesado.procesado_en.desc()).limit(limite).all()
    if not eventos:
        raise HTTPException(status_code=404, detail=f"No se encontraron eventos para {id_logico}")
    return eventos


@router.get("/alertas", response_model=List[AlertaStreamRespuesta])
def listar_alertas(
    request: Request,
    severidad: str = None,
    tipo_alerta: str = None,
    limite: int = 50,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(AlertaStream)
    if usuario_id:
        query = query.filter(AlertaStream.usuario_id == usuario_id)
    if severidad:
        query = query.filter(AlertaStream.severidad == severidad)
    if tipo_alerta:
        query = query.filter(AlertaStream.tipo_alerta == tipo_alerta)
    return query.order_by(AlertaStream.generada_en.desc()).limit(limite).all()


@router.get("/alertas/{id_logico}", response_model=List[AlertaStreamRespuesta])
def alertas_por_dispositivo(
    id_logico: str,
    request: Request,
    limite: int = 20,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(AlertaStream).filter(AlertaStream.id_logico == id_logico)
    if usuario_id:
        query = query.filter(AlertaStream.usuario_id == usuario_id)
    alertas = query.order_by(AlertaStream.generada_en.desc()).limit(limite).all()
    if not alertas:
        raise HTTPException(status_code=404, detail=f"No se encontraron alertas para {id_logico}")
    return alertas


@router.get("/resumen", response_model=ResumenProcesamiento)
def resumen_procesamiento(
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    q = db.query(EventoProcesado)
    qa = db.query(AlertaStream)
    if usuario_id:
        q  = q.filter(EventoProcesado.usuario_id == usuario_id)
        qa = qa.filter(AlertaStream.usuario_id == usuario_id)

    return ResumenProcesamiento(
        total_eventos=q.count(),
        total_alertas=qa.count(),
        alertas_criticas=qa.filter(AlertaStream.severidad == "critica").count(),
        alertas_altas=qa.filter(AlertaStream.severidad == "alta").count(),
        alertas_medias=qa.filter(AlertaStream.severidad == "media").count(),
    )