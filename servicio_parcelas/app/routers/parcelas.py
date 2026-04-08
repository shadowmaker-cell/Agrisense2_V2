from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.parcela import (
    ParcelaEntrada, ParcelaRespuesta, ParcelaResumen,
    ParcelaSensorEntrada, ParcelaSensorRespuesta,
    HistorialCultivoEntrada, HistorialCultivoRespuesta,
    TipoCultivoEntrada, TipoCultivoRespuesta,
)
from app.services.parcela_service import (
    crear_parcela, listar_parcelas, obtener_parcela,
    actualizar_parcela, eliminar_parcela,
    asignar_sensor, listar_sensores_parcela, desasignar_sensor,
    agregar_historial, listar_historial, actualizar_historial,
    listar_tipos_cultivo, crear_tipo_cultivo, resumen_parcelas,
)
from app.utils.jwt import get_usuario_id, get_usuario_id_opcional

router = APIRouter(prefix="/api/v1/parcelas", tags=["parcelas"])


# ── Health ────────────────────────────────────────────
@router.get("/health")
def health():
    return {"estado": "ok", "servicio": "parcel-management", "version": "1.0.0"}


# ── Tipos de cultivo (globales) ───────────────────────
@router.get("/tipos-cultivo", response_model=List[TipoCultivoRespuesta])
def get_tipos_cultivo(db: Session = Depends(get_db)):
    return listar_tipos_cultivo(db)


@router.post("/tipos-cultivo", response_model=TipoCultivoRespuesta, status_code=201)
def post_tipo_cultivo(payload: TipoCultivoEntrada, db: Session = Depends(get_db)):
    return crear_tipo_cultivo(db, payload)


# ── Resumen ───────────────────────────────────────────
@router.get("/resumen", response_model=List[ParcelaResumen])
def get_resumen(request: Request, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id(request)
    return resumen_parcelas(db, usuario_id)


# ── Parcelas CRUD ─────────────────────────────────────
@router.get("/", response_model=List[ParcelaRespuesta])
def get_parcelas(
    request: Request,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    return listar_parcelas(db, estado, usuario_id)


@router.get("/{parcela_id}", response_model=ParcelaRespuesta)
def get_parcela(
    parcela_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    parcela = obtener_parcela(db, parcela_id, usuario_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return parcela


@router.post("/", response_model=ParcelaRespuesta, status_code=201)
def post_parcela(
    payload: ParcelaEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    return crear_parcela(db, payload, usuario_id)


@router.put("/{parcela_id}", response_model=ParcelaRespuesta)
def put_parcela(
    parcela_id: int,
    payload: ParcelaEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    parcela = actualizar_parcela(db, parcela_id, payload.model_dump(), usuario_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return parcela


@router.delete("/{parcela_id}")
def delete_parcela(
    parcela_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    ok = eliminar_parcela(db, parcela_id, usuario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return {"mensaje": "Parcela eliminada exitosamente"}


# ── Sensores de parcela ───────────────────────────────
@router.get("/{parcela_id}/sensores", response_model=List[ParcelaSensorRespuesta])
def get_sensores_parcela(
    parcela_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    parcela = obtener_parcela(db, parcela_id, usuario_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return listar_sensores_parcela(db, parcela_id)


@router.post("/{parcela_id}/sensores", response_model=ParcelaSensorRespuesta, status_code=201)
def post_asignar_sensor(
    parcela_id: int,
    payload: ParcelaSensorEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    parcela = obtener_parcela(db, parcela_id, usuario_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    sensor, error = asignar_sensor(db, parcela_id, payload)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return sensor


@router.delete("/{parcela_id}/sensores/{sensor_id}")
def delete_sensor_parcela(
    parcela_id: int,
    sensor_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    parcela = obtener_parcela(db, parcela_id, usuario_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    ok = desasignar_sensor(db, parcela_id, sensor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Asignacion no encontrada")
    return {"mensaje": "Sensor desasignado exitosamente"}


# ── Historial de cultivos ─────────────────────────────
@router.get("/{parcela_id}/historial", response_model=List[HistorialCultivoRespuesta])
def get_historial(
    parcela_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    parcela = obtener_parcela(db, parcela_id, usuario_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return listar_historial(db, parcela_id)


@router.post("/{parcela_id}/historial", response_model=HistorialCultivoRespuesta, status_code=201)
def post_historial(
    parcela_id: int,
    payload: HistorialCultivoEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    parcela = obtener_parcela(db, parcela_id, usuario_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    historial, error = agregar_historial(db, parcela_id, payload)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return historial


@router.put("/{parcela_id}/historial/{historial_id}", response_model=HistorialCultivoRespuesta)
def put_historial(
    parcela_id: int,
    historial_id: int,
    payload: HistorialCultivoEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    parcela = obtener_parcela(db, parcela_id, usuario_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    historial = actualizar_historial(db, historial_id, payload.model_dump())
    if not historial:
        raise HTTPException(status_code=404, detail="Historial no encontrado")
    return historial