from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel as PydanticBase
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
    generar_desde_alerta,
    listar_recomendaciones,
    obtener_recomendacion,
    actualizar_estado,
    crear_recomendacion_manual,
    resumen_recomendaciones,
)
from app.utils.jwt import get_usuario_id, get_usuario_id_opcional

router = APIRouter(prefix="/api/v1/recomendaciones", tags=["recomendaciones"])


class AlertaEntrada(PydanticBase):
    tipo_alerta:    str
    tipo_metrica:   str
    valor:          float
    id_logico:      Optional[str]  = None
    parcela_id:     Optional[int]  = None
    severidad:      str            = "media"
    condicion:      str            = ""
    tipo_cultivo:   str            = "maiz"
    area_hectareas: float          = 1.0


# ── Health ────────────────────────────────────────────
@router.get("/health")
def health():
    return {"estado": "ok", "servicio": "recommendation-engine", "version": "1.0.0"}


# ── Categorias ────────────────────────────────────────
@router.get("/categorias", response_model=List[CategoriaRespuesta])
def get_categorias(db: Session = Depends(get_db)):
    return listar_categorias(db)


# ── Generar manual ────────────────────────────────────
@router.post("/generar", response_model=GenerarRecomendacionesRespuesta, status_code=201)
def post_generar(
    payload: GenerarRecomendacionesEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    try:
        data = payload.model_dump()
        data["usuario_id"] = usuario_id
        return generar_recomendaciones(db, data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendaciones: {str(e)}")


# ── Generar automatico desde alerta ──────────────────
@router.post("/desde-alerta", status_code=201)
def post_desde_alerta(
    payload: AlertaEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    """Genera recomendaciones automáticas a partir de una alerta detectada."""
    usuario_id = get_usuario_id_opcional(request)
    try:
        datos = payload.model_dump()
        datos["usuario_id"] = usuario_id
        resultado = generar_desde_alerta(db, datos)
        return {
            "mensaje":         "Recomendaciones generadas automaticamente",
            "total_generadas": resultado["total_generadas"],
            "criticas":        resultado["criticas"],
            "altas":           resultado["altas"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ── Rutas especificas antes de parametros ─────────────
@router.get("/activas", response_model=List[RecomendacionRespuesta])
def get_activas(
    request: Request,
    parcela_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    return listar_recomendaciones(db, parcela_id=parcela_id, estado="activa", usuario_id=usuario_id)


@router.get("/resumen", response_model=ResumenRecomendacionesRespuesta)
def get_resumen(request: Request, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id_opcional(request)
    return resumen_recomendaciones(db, usuario_id)


@router.get("/parcela/{parcela_id}", response_model=List[RecomendacionRespuesta])
def get_por_parcela(
    parcela_id: int,
    request: Request,
    estado:    Optional[str] = None,
    prioridad: Optional[str] = None,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    return listar_recomendaciones(db, parcela_id=parcela_id, estado=estado,
                                   prioridad=prioridad, usuario_id=usuario_id)


@router.get("/sensor/{id_logico}", response_model=List[RecomendacionRespuesta])
def get_por_sensor(
    id_logico: str,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    return listar_recomendaciones(db, id_logico=id_logico, usuario_id=usuario_id)


@router.get("/", response_model=List[RecomendacionRespuesta])
def get_recomendaciones(
    request: Request,
    parcela_id: Optional[int] = None,
    id_logico:  Optional[str] = None,
    prioridad:  Optional[str] = None,
    estado:     Optional[str] = None,
    limite:     int           = 50,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    return listar_recomendaciones(db, parcela_id, id_logico, prioridad, estado, limite, usuario_id)


@router.post("/", response_model=RecomendacionRespuesta, status_code=201)
def post_recomendacion(
    payload: RecomendacionEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    return crear_recomendacion_manual(db, payload, usuario_id)


# ── Rutas con parametros al final ─────────────────────
@router.get("/{rec_id}", response_model=RecomendacionRespuesta)
def get_recomendacion(
    rec_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    rec = obtener_recomendacion(db, rec_id, usuario_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendacion no encontrada")
    return rec


@router.put("/{rec_id}/estado", response_model=RecomendacionRespuesta)
def put_estado(
    rec_id: int,
    payload: ActualizarEstadoEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    rec = actualizar_estado(db, rec_id, payload.estado, usuario_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendacion no encontrada")
    return rec