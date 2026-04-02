from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.recomendacion import (
    CategoriaRespuesta,
    RecomendacionRespuesta, RecomendacionEntrada,
    GenerarRecomendacionesEntrada, GenerarRecomendacionesRespuesta,
    ActualizarEstadoEntrada, ResumenRecomendacionesRespuesta,
)
from app.services.recomendacion_service import (
    listar_categorias,
    generar_recomendaciones,
    listar_recomendaciones,
    obtener_recomendacion,
    actualizar_estado,
    crear_recomendacion_manual,
    resumen_recomendaciones,
)

router = APIRouter(prefix="/api/v1/recomendaciones", tags=["recomendaciones"])


# ── Health ────────────────────────────────────────────
@router.get("/health")
def health():
    return {
        "estado":   "ok",
        "servicio": "recommendation-engine",
        "version":  "1.0.0",
    }


# ── Categorias ────────────────────────────────────────
@router.get("/categorias", response_model=List[CategoriaRespuesta])
def get_categorias(db: Session = Depends(get_db)):
    """Lista todas las categorias de recomendaciones disponibles."""
    return listar_categorias(db)


# ── Generar recomendaciones automaticas ───────────────
@router.post("/generar", response_model=GenerarRecomendacionesRespuesta, status_code=201)
def post_generar(
    payload: GenerarRecomendacionesEntrada,
    db: Session = Depends(get_db)
):
    """
    Motor de recomendaciones agronomicas.
    Analiza las condiciones del cultivo y genera recomendaciones
    combinando reglas de negocio y predicciones ML.
    """
    try:
        resultado = generar_recomendaciones(db, payload.model_dump())
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendaciones: {str(e)}")


# ── CRUD recomendaciones ──────────────────────────────
@router.get("/", response_model=List[RecomendacionRespuesta])
def get_recomendaciones(
    parcela_id: Optional[int] = None,
    id_logico:  Optional[str] = None,
    prioridad:  Optional[str] = None,
    estado:     Optional[str] = None,
    limite:     int           = 50,
    db: Session = Depends(get_db)
):
    """Lista recomendaciones con filtros opcionales."""
    return listar_recomendaciones(db, parcela_id, id_logico, prioridad, estado, limite)


@router.get("/activas", response_model=List[RecomendacionRespuesta])
def get_activas(
    parcela_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Lista solo las recomendaciones activas."""
    return listar_recomendaciones(db, parcela_id=parcela_id, estado="activa")


@router.get("/resumen", response_model=ResumenRecomendacionesRespuesta)
def get_resumen(db: Session = Depends(get_db)):
    """Resumen del motor de recomendaciones."""
    return resumen_recomendaciones(db)


@router.get("/{rec_id}", response_model=RecomendacionRespuesta)
def get_recomendacion(rec_id: int, db: Session = Depends(get_db)):
    """Obtiene una recomendacion por ID."""
    rec = obtener_recomendacion(db, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendacion no encontrada")
    return rec


@router.post("/", response_model=RecomendacionRespuesta, status_code=201)
def post_recomendacion(
    payload: RecomendacionEntrada,
    db: Session = Depends(get_db)
):
    """Crea una recomendacion manual."""
    return crear_recomendacion_manual(db, payload)


@router.put("/{rec_id}/estado", response_model=RecomendacionRespuesta)
def put_estado(
    rec_id: int,
    payload: ActualizarEstadoEntrada,
    db: Session = Depends(get_db)
):
    """Actualiza el estado de una recomendacion (aplicada, descartada, etc.)."""
    rec = actualizar_estado(db, rec_id, payload.estado)
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendacion no encontrada")
    return rec


# ── Por parcela ───────────────────────────────────────
@router.get("/parcela/{parcela_id}", response_model=List[RecomendacionRespuesta])
def get_por_parcela(
    parcela_id: int,
    estado:     Optional[str] = None,
    prioridad:  Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista recomendaciones de una parcela especifica."""
    return listar_recomendaciones(db, parcela_id=parcela_id, estado=estado, prioridad=prioridad)


# ── Por sensor ────────────────────────────────────────
@router.get("/sensor/{id_logico}", response_model=List[RecomendacionRespuesta])
def get_por_sensor(
    id_logico: str,
    db: Session = Depends(get_db)
):
    """Lista recomendaciones de un sensor especifico."""
    return listar_recomendaciones(db, id_logico=id_logico)