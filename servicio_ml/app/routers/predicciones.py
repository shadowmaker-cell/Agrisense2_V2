from fastapi import APIRouter, Depends, HTTPException
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


# ── Modelos disponibles ───────────────────────────────
@router.get("/modelos", response_model=List[ModeloRegistroRespuesta])
def get_modelos(db: Session = Depends(get_db)):
    """Lista todos los modelos ML activos."""
    return listar_modelos(db)


@router.get("/modelos/{modelo_id}", response_model=ModeloRegistroRespuesta)
def get_modelo(modelo_id: int, db: Session = Depends(get_db)):
    """Obtiene un modelo ML por ID."""
    modelo = obtener_modelo(db, modelo_id)
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return modelo


# ── Prediccion de necesidades hidricas ────────────────
@router.post("/predicciones/agua", response_model=PrediccionAguaRespuesta, status_code=201)
def predecir_agua(payload: PrediccionAguaEntrada, db: Session = Depends(get_db)):
    """
    Predice los litros de agua necesarios para una parcela.
    Usa RandomForest entrenado con datos agronomicos sinteticos.
    """
    try:
        resultado = ejecutar_prediccion_agua(db, payload.model_dump())
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prediccion: {str(e)}")


# ── Prediccion de rendimiento ─────────────────────────
@router.post("/predicciones/rendimiento", response_model=PrediccionRendimientoRespuesta, status_code=201)
def predecir_rendimiento(payload: PrediccionRendimientoEntrada, db: Session = Depends(get_db)):
    """
    Predice el rendimiento esperado del cultivo en kg/ha.
    Considera condiciones del suelo, clima y tipo de cultivo.
    """
    try:
        resultado = ejecutar_prediccion_rendimiento(db, payload.model_dump())
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prediccion: {str(e)}")


# ── Prediccion de riesgo ──────────────────────────────
@router.post("/predicciones/riesgo", response_model=PrediccionRiesgoRespuesta, status_code=201)
def predecir_riesgo(payload: PrediccionRiesgoEntrada, db: Session = Depends(get_db)):
    """
    Clasifica el nivel de riesgo agronomico.
    Tipos: helada, sequia, hongo, inundacion.
    Niveles: bajo, medio, alto, critico.
    """
    try:
        resultado = ejecutar_prediccion_riesgo(db, payload.model_dump())
        return resultado
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en prediccion: {str(e)}")


# ── Historial de predicciones ─────────────────────────
@router.get("/predicciones", response_model=List[SolicitudPrediccionRespuesta])
def get_predicciones(
    tipo:   Optional[str] = None,
    limite: int           = 50,
    db: Session = Depends(get_db)
):
    """Lista el historial de predicciones realizadas."""
    return listar_predicciones(db, tipo, limite)


@router.get("/predicciones/{solicitud_id}/resultado", response_model=ResultadoPrediccionRespuesta)
def get_resultado(solicitud_id: int, db: Session = Depends(get_db)):
    """Obtiene el resultado de una prediccion por ID de solicitud."""
    resultado = obtener_resultado(db, solicitud_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Resultado no encontrado")
    return resultado


# ── Resumen ───────────────────────────────────────────
@router.get("/resumen", response_model=ResumenMLRespuesta)
def get_resumen(db: Session = Depends(get_db)):
    """Resumen del servicio ML: total predicciones, por tipo y modelos activos."""
    return resumen_ml(db)