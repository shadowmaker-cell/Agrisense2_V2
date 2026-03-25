from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import eventos
from app.consumers.telemetria import iniciar_consumidor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia el consumidor Kafka al arrancar el servicio."""
    iniciar_consumidor()
    yield


app = FastAPI(
    title="Stream Processor Service",
    description="Procesamiento de eventos IoT en tiempo real — AgriSense",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(eventos.router)


@app.get("/health")
def health_check():
    """Health check para balanceadores y CI/CD."""
    return {
        "estado":   "ok",
        "servicio": "stream-processor",
        "version":  "1.0.0"
    }