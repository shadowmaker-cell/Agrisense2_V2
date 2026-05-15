from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.routers import recomendaciones
from app.database import SessionLocal, engine
from app.models import recomendacion as models_rec
from app.services.recomendacion_service import inicializar_categorias
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        models_rec.Base.metadata.create_all(bind=engine)
        logger.info("Tablas de recomendaciones verificadas")
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")

    db = SessionLocal()
    try:
        inicializar_categorias(db)
    except Exception as e:
        logger.warning(f"No se pudieron inicializar categorias: {e}")
    finally:
        db.close()
    yield


app = FastAPI(
    title="Recommendation Engine",
    description="Motor de recomendaciones agronomicas para AgriSense",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

app.include_router(recomendaciones.router)


@app.get("/health")
def health_check():
    return {"estado": "ok", "servicio": "recommendation-engine", "version": "1.0.0"}