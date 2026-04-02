from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import recomendaciones
from app.database import SessionLocal
from app.services.recomendacion_service import inicializar_categorias


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        inicializar_categorias(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Recommendation Engine",
    description="Motor de recomendaciones agronomicas para AgriSense — combina reglas de negocio y predicciones ML",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(recomendaciones.router)


@app.get("/health")
def health_check():
    return {
        "estado":   "ok",
        "servicio": "recommendation-engine",
        "version":  "1.0.0",
    }