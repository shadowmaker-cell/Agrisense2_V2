from fastapi import FastAPI
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from app.routers import eventos
from app.consumers.telemetria import iniciar_consumidor

@asynccontextmanager
async def lifespan(app: FastAPI):
    iniciar_consumidor()
    yield

app = FastAPI(
    title="Stream Processor Service",
    description="Procesamiento de eventos IoT en tiempo real — AgriSense",
    version="1.0.0",
    lifespan=lifespan
)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

app.include_router(eventos.router)

@app.get("/health")
def health_check():
    return {"estado": "ok", "servicio": "stream-processor", "version": "1.0.0"}