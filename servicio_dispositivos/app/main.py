from fastapi import FastAPI
from app.routers import devices

app = FastAPI(
    title="Servicio de Gestión de Dispositivos",
    description="Gestión de sensores IoT desplegados en huertos — AgriSense",
    version="1.0.0"
)

app.include_router(devices.router)


@app.get("/health")
def verificar_salud():
    return {"estado": "ok", "servicio": "gestión-dispositivos"}