from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(prefix="/api/v1/parcelas", tags=["parcelas"])


# ── Health ────────────────────────────────────────────
@router.get("/health")
def health():
    return {"estado": "ok", "servicio": "parcel-management", "version": "1.0.0"}


# ── Tipos de cultivo ──────────────────────────────────
@router.get("/tipos-cultivo", response_model=List[TipoCultivoRespuesta])
def get_tipos_cultivo(db: Session = Depends(get_db)):
    """Lista todos los tipos de cultivo disponibles."""
    return listar_tipos_cultivo(db)


@router.post("/tipos-cultivo", response_model=TipoCultivoRespuesta, status_code=201)
def post_tipo_cultivo(payload: TipoCultivoEntrada, db: Session = Depends(get_db)):
    """Crea un nuevo tipo de cultivo."""
    return crear_tipo_cultivo(db, payload)


# ── Parcelas CRUD ─────────────────────────────────────
@router.get("/resumen", response_model=List[ParcelaResumen])
def get_resumen(db: Session = Depends(get_db)):
    """Resumen de todas las parcelas con sensores activos y cultivo actual."""
    return resumen_parcelas(db)


@router.get("/", response_model=List[ParcelaRespuesta])
def get_parcelas(
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista todas las parcelas con sus sensores e historial."""
    return listar_parcelas(db, estado)


@router.get("/{parcela_id}", response_model=ParcelaRespuesta)
def get_parcela(parcela_id: int, db: Session = Depends(get_db)):
    """Obtiene una parcela por ID con todos sus datos."""
    parcela = obtener_parcela(db, parcela_id)
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return parcela


@router.post("/", response_model=ParcelaRespuesta, status_code=201)
def post_parcela(payload: ParcelaEntrada, db: Session = Depends(get_db)):
    """Crea una nueva parcela."""
    return crear_parcela(db, payload)


@router.put("/{parcela_id}", response_model=ParcelaRespuesta)
def put_parcela(
    parcela_id: int,
    payload: ParcelaEntrada,
    db: Session = Depends(get_db)
):
    """Actualiza los datos de una parcela."""
    parcela = actualizar_parcela(db, parcela_id, payload.model_dump())
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return parcela


@router.delete("/{parcela_id}")
def delete_parcela(parcela_id: int, db: Session = Depends(get_db)):
    """Elimina una parcela y todos sus datos asociados."""
    ok = eliminar_parcela(db, parcela_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Parcela no encontrada")
    return {"mensaje": "Parcela eliminada exitosamente"}


# ── Sensores de parcela ───────────────────────────────
@router.get("/{parcela_id}/sensores", response_model=List[ParcelaSensorRespuesta])
def get_sensores_parcela(parcela_id: int, db: Session = Depends(get_db)):
    """Lista los sensores asignados a una parcela."""
    return listar_sensores_parcela(db, parcela_id)


@router.post("/{parcela_id}/sensores", response_model=ParcelaSensorRespuesta, status_code=201)
def post_asignar_sensor(
    parcela_id: int,
    payload: ParcelaSensorEntrada,
    db: Session = Depends(get_db)
):
    """Asigna un sensor IoT a una parcela."""
    sensor, error = asignar_sensor(db, parcela_id, payload)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return sensor


@router.delete("/{parcela_id}/sensores/{sensor_id}")
def delete_sensor_parcela(
    parcela_id: int,
    sensor_id: int,
    db: Session = Depends(get_db)
):
    """Desasigna un sensor de una parcela."""
    ok = desasignar_sensor(db, parcela_id, sensor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Asignacion no encontrada")
    return {"mensaje": "Sensor desasignado exitosamente"}


# ── Historial de cultivos ─────────────────────────────
@router.get("/{parcela_id}/historial", response_model=List[HistorialCultivoRespuesta])
def get_historial(parcela_id: int, db: Session = Depends(get_db)):
    """Lista el historial de cultivos de una parcela."""
    return listar_historial(db, parcela_id)


@router.post("/{parcela_id}/historial", response_model=HistorialCultivoRespuesta, status_code=201)
def post_historial(
    parcela_id: int,
    payload: HistorialCultivoEntrada,
    db: Session = Depends(get_db)
):
    """Agrega un registro al historial de cultivos."""
    historial, error = agregar_historial(db, parcela_id, payload)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return historial


@router.put("/{parcela_id}/historial/{historial_id}", response_model=HistorialCultivoRespuesta)
def put_historial(
    parcela_id: int,
    historial_id: int,
    payload: HistorialCultivoEntrada,
    db: Session = Depends(get_db)
):
    """Actualiza un registro del historial de cultivos."""
    historial = actualizar_historial(db, historial_id, payload.model_dump())
    if not historial:
        raise HTTPException(status_code=404, detail="Historial no encontrado")
    return historial