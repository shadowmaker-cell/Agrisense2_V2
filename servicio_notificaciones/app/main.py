from fastapi import FastAPI
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from app.routers import notificaciones
from app.consumers.alertas import iniciar_consumidor


@asynccontextmanager
async def lifespan(app: FastAPI):
    iniciar_consumidor()
    yield


app = FastAPI(
    title="Notification Service",
    description="Servicio de notificaciones y alertas — AgriSense",
    version="1.0.0",
    lifespan=lifespan
)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

app.include_router(notificaciones.router)


@app.get("/health")
def health_check():
    return {"estado": "ok", "servicio": "notification-service", "version": "1.0.0"}