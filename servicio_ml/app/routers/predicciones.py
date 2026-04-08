from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.prediccion import (
    ModeloRegistroRespuesta,
    PrediccionAguaEntrada, PrediccionAguaRespuesta,
    PrediccionRendimientoEntrada, PrediccionRendimientoRespuesta,
    PrediccionRiesgoEntrada, PrediccionRiesgoRespuesta,
    SolicitudPrediccionRespuesta, ResultadoPrediccionRespuesta,
    ResumenMLRespuesta,
)
from app.services.prediccion_service import (
    listar_modelos, obtener_modelo,
    ejecutar_prediccion_agua,
    ejecutar_prediccion_rendimiento,
    ejecutar_prediccion_riesgo,
    listar_predicciones, obtener_resultado,
    resumen_ml,
)
from app.utils.jwt import get_usuario_id_opcional

router = APIRouter(prefix="/api/v1/ml", tags=["machine-learning"])


# ── Health ────────────────────────────────────────────
@router.get("/health")
def health():
    return {
        "estado":   "ok",
        "servicio": "ml-prediction-service",
        "version":  "1.0.0",
        "modelos":  ["agua", "rendimiento", "riesgo"],
    }


# ── Modelos ───────────────────────────────────────────
@router.get("/modelos", response_model=List[ModeloRegistroRespuesta])
def get_modelos(db: Session = Depends(get_db)):
    return listar_modelos(db)


@router.get("/modelos/{modelo_id}", response_model=ModeloRegistroRespuesta)
def get_modelo(modelo_id: int, db: Session = Depends(get_db)):
    modelo = obtener_modelo(db, modelo_id)
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return modelo


# ── Prediccion de agua ────────────────────────────────
@router.post("/predicciones/agua", response_model=PrediccionAguaRespuesta, status_code=201)
def predecir_agua(
    payload: PrediccionAguaEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    try:
        return ejecutar_prediccion_agua(db, payload.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prediccion: {str(e)}")


# ── Prediccion de rendimiento ─────────────────────────
@router.post("/predicciones/rendimiento", response_model=PrediccionRendimientoRespuesta, status_code=201)
def predecir_rendimiento(
    payload: PrediccionRendimientoEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    try:
        return ejecutar_prediccion_rendimiento(db, payload.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prediccion: {str(e)}")


# ── Prediccion de riesgo ──────────────────────────────
@router.post("/predicciones/riesgo", response_model=PrediccionRiesgoRespuesta, status_code=201)
def predecir_riesgo(
    payload: PrediccionRiesgoEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    try:
        return ejecutar_prediccion_riesgo(db, payload.model_dump(), usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prediccion: {str(e)}")


# ── Historial ─────────────────────────────────────────
@router.get("/predicciones", response_model=List[SolicitudPrediccionRespuesta])
def get_predicciones(
    request: Request,
    tipo:   Optional[str] = None,
    limite: int           = 50,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    return listar_predicciones(db, tipo, limite, usuario_id)


@router.get("/predicciones/{solicitud_id}/resultado", response_model=ResultadoPrediccionRespuesta)
def get_resultado(solicitud_id: int, db: Session = Depends(get_db)):
    resultado = obtener_resultado(db, solicitud_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return resultado


# ── Resumen ───────────────────────────────────────────
@router.get("/resumen", response_model=ResumenMLRespuesta)
def get_resumen(request: Request, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id_opcional(request)
    return resumen_ml(db, usuario_id)