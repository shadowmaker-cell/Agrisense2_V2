from fastapi import FastAPI
from app.routers import telemetria

app = FastAPI(
    title="IoT Ingestion Service",
    description="Servicio de ingesta de telemetría IoT — AgriSense",
    version="1.0.0"
)

app.include_router(telemetria.router)


@app.get("/health")
def health_check():
    """Health check para balanceadores y CI/CD."""
    return {
        "estado": "ok",
        "servicio": "iot-ingestion",
        "version": "1.0.0"
    }