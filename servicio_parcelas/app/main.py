from fastapi import FastAPI
from app.routers import parcelas

app = FastAPI(
    title="Parcel Management Service",
    description="Gestion de parcelas agricolas, sensores asignados e historial de cultivos — AgriSense",
    version="1.0.0",
)

app.include_router(parcelas.router)


@app.get("/health")
def health_check():
    return {
        "estado":   "ok",
        "servicio": "parcel-management",
        "version":  "1.0.0"
    }