from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import notificaciones
from app.consumers.alertas import iniciar_consumidor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia el consumidor Kafka al arrancar el servicio."""
    iniciar_consumidor()
    yield


app = FastAPI(
    title="Notification Service",
    description="Servicio de notificaciones y alertas — AgriSense",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(notificaciones.router)


@app.get("/health")
def health_check():
    return {
        "estado":   "ok",
        "servicio": "notification-service",
        "version":  "1.0.0"
    }