from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
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

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

app.include_router(predicciones.router)


@app.get("/health")
def health_check():
    return {"estado": "ok", "servicio": "ml-prediction-service", "version": "1.0.0"}