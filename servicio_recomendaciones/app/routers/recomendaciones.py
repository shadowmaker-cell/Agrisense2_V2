from fastapi import APIRouter, Depends, HTTPException, Request
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
from app.utils.jwt import get_usuario_id, get_usuario_id_opcional

router = APIRouter(prefix="/api/v1/recomendaciones", tags=["recomendaciones"])


# ── Health ────────────────────────────────────────────
@router.get("/health")
def health():
    return {"estado": "ok", "servicio": "recommendation-engine", "version": "1.0.0"}


# ── Categorias (globales) ─────────────────────────────
@router.get("/categorias", response_model=List[CategoriaRespuesta])
def get_categorias(db: Session = Depends(get_db)):
    return listar_categorias(db)


# ── Generar ───────────────────────────────────────────
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


# ── Listar ────────────────────────────────────────────
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


@router.post("/", response_model=RecomendacionRespuesta, status_code=201)
def post_recomendacion(
    payload: RecomendacionEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    return crear_recomendacion_manual(db, payload, usuario_id)


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


# ── Por parcela ───────────────────────────────────────
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


# ── Por sensor ────────────────────────────────────────
@router.get("/sensor/{id_logico}", response_model=List[RecomendacionRespuesta])
def get_por_sensor(
    id_logico: str,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    return listar_recomendaciones(db, id_logico=id_logico, usuario_id=usuario_id)