from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import telemetria
from app.database import engine
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


def inicializar_timescale():
    """Activa TimescaleDB. La conversion a hypertable requiere recrear la tabla."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            conn.commit()

            result = conn.execute(text("""
                SELECT COUNT(*) FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'lectura_sensor'
            """)).scalar()

            if result == 0:
                # Recrear tabla con timestamp como parte de la PK
                conn.execute(text("""
                    ALTER TABLE lectura_sensor DROP CONSTRAINT IF EXISTS lectura_sensor_pkey;
                """))
                conn.execute(text("""
                    ALTER TABLE lectura_sensor
                    ADD CONSTRAINT lectura_sensor_pkey
                    PRIMARY KEY (id, timestamp_lectura);
                """))
                conn.commit()
                conn.execute(text("""
                    SELECT create_hypertable(
                        'lectura_sensor',
                        'timestamp_lectura',
                        if_not_exists => TRUE,
                        migrate_data  => TRUE
                    );
                """))
                conn.commit()
                logger.info("✅ lectura_sensor convertida a hypertable TimescaleDB")
            else:
                logger.info("✅ lectura_sensor ya es hypertable TimescaleDB")

    except Exception as e:
        logger.warning(f"TimescaleDB no disponible — usando PostgreSQL estandar: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    inicializar_timescale()
    yield


app = FastAPI(
    title="IoT Ingestion Service",
    description="Servicio de ingesta de telemetria IoT — AgriSense",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(telemetria.router)


@app.get("/health")
def health_check():
    return {
        "estado":   "ok",
        "servicio": "iot-ingestion",
        "version":  "1.0.0",
        "timescale": "activo",
    }