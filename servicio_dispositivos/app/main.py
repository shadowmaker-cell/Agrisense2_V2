from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.routers import devices

app = FastAPI(
    title="Servicio de Gestion de Dispositivos",
    description="Gestion de sensores IoT desplegados en huertos — AgriSense",
    version="1.0.0"
)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

app.include_router(devices.router)


@app.get("/health")
def verificar_salud():
    return {"estado": "ok", "servicio": "gestion-dispositivos", "version": "1.0.0"}