from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.evento import EventoProcesado, AlertaStream
from app.schemas.evento import (
    EventoRespuesta, AlertaStreamRespuesta,
    ResumenProcesamiento, ProcesarManualEntrada
)
from app.services.detector import procesar_evento_telemetria

router = APIRouter(prefix="/api/v1/procesamiento", tags=["procesamiento"])


# ── POST /api/v1/procesamiento/manual ─────────────────
@router.post("/manual", status_code=201)
def procesar_manual(
    payload: ProcesarManualEntrada,
    db: Session = Depends(get_db)
):
    """Procesa una lectura manualmente sin pasar por Kafka."""
    datos = {
        "dispositivo_id":    payload.dispositivo_id,
        "id_logico":         payload.id_logico,
        "tipo_metrica":      payload.tipo_metrica,
        "valor_metrica":     payload.valor_metrica,
        "unidad":            payload.unidad,
        "timestamp_lectura": None
    }
    resultado = procesar_evento_telemetria(db, datos)
    return {
        "mensaje":           "Evento procesado exitosamente",
        "evento_id":         resultado["evento_id"],
        "alertas_generadas": resultado["alertas_generadas"],
        "tipos_alerta":      resultado["tipos_alerta"]
    }


# ── GET /api/v1/procesamiento/eventos ─────────────────
@router.get("/eventos", response_model=List[EventoRespuesta])
def listar_eventos(
    limite: int = 50,
    con_alerta: bool = None,
    db: Session = Depends(get_db)
):
    """Lista los eventos procesados."""
    query = db.query(EventoProcesado)
    if con_alerta is not None:
        query = query.filter(EventoProcesado.tiene_alerta == con_alerta)
    return query.order_by(
        EventoProcesado.procesado_en.desc()
    ).limit(limite).all()


# ── GET /api/v1/procesamiento/eventos/{id_logico} ─────
@router.get("/eventos/{id_logico}", response_model=List[EventoRespuesta])
def eventos_por_dispositivo(
    id_logico: str,
    limite: int = 20,
    db: Session = Depends(get_db)
):
    """Lista eventos de un dispositivo específico."""
    eventos = db.query(EventoProcesado).filter(
        EventoProcesado.id_logico == id_logico
    ).order_by(
        EventoProcesado.procesado_en.desc()
    ).limit(limite).all()

    if not eventos:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron eventos para {id_logico}"
        )
    return eventos


# ── GET /api/v1/procesamiento/alertas ─────────────────
@router.get("/alertas", response_model=List[AlertaStreamRespuesta])
def listar_alertas(
    severidad: str = None,
    tipo_alerta: str = None,
    limite: int = 50,
    db: Session = Depends(get_db)
):
    """Lista alertas generadas por el Stream Processor."""
    query = db.query(AlertaStream)
    if severidad:
        query = query.filter(AlertaStream.severidad == severidad)
    if tipo_alerta:
        query = query.filter(AlertaStream.tipo_alerta == tipo_alerta)
    return query.order_by(
        AlertaStream.generada_en.desc()
    ).limit(limite).all()


# ── GET /api/v1/procesamiento/alertas/{id_logico} ─────
@router.get("/alertas/{id_logico}", response_model=List[AlertaStreamRespuesta])
def alertas_por_dispositivo(
    id_logico: str,
    limite: int = 20,
    db: Session = Depends(get_db)
):
    """Lista alertas de un dispositivo específico."""
    alertas = db.query(AlertaStream).filter(
        AlertaStream.id_logico == id_logico
    ).order_by(
        AlertaStream.generada_en.desc()
    ).limit(limite).all()

    if not alertas:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron alertas para {id_logico}"
        )
    return alertas


# ── GET /api/v1/procesamiento/resumen ─────────────────
@router.get("/resumen", response_model=ResumenProcesamiento)
def resumen_procesamiento(db: Session = Depends(get_db)):
    """Resumen general del procesamiento."""
    total_eventos = db.query(EventoProcesado).count()
    total_alertas = db.query(AlertaStream).count()
    alertas_criticas = db.query(AlertaStream).filter(
        AlertaStream.severidad == "critica"
    ).count()
    alertas_altas = db.query(AlertaStream).filter(
        AlertaStream.severidad == "alta"
    ).count()
    alertas_medias = db.query(AlertaStream).filter(
        AlertaStream.severidad == "media"
    ).count()

    return ResumenProcesamiento(
        total_eventos=total_eventos,
        total_alertas=total_alertas,
        alertas_criticas=alertas_criticas,
        alertas_altas=alertas_altas,
        alertas_medias=alertas_medias
    )