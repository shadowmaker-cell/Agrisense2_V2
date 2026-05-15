from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.routers import parcelas

app = FastAPI(
    title="Parcel Management Service",
    description="Gestion de parcelas agricolas — AgriSense",
    version="1.0.0",
)

Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

app.include_router(parcelas.router)


@app.get("/health")
def health_check():
    return {"estado": "ok", "servicio": "parcel-management", "version": "1.0.0"}