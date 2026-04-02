from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import predicciones
from app.database import SessionLocal
from app.services.prediccion_service import inicializar_modelos


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        inicializar_modelos(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="ML Prediction Service",
    description="Servicio de predicciones Machine Learning para AgriSense",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(predicciones.router)


@app.get("/health")
def health_check():
    return {
        "estado":   "ok",
        "servicio": "ml-prediction-service",
        "version":  "1.0.0",
    }