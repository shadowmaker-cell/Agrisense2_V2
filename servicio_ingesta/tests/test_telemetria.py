import os
os.environ["DATABASE_URL"] = "sqlite:///./test_ingesta.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# ── Base de datos en memoria para tests ───────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test_ingesta.db"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}
)
SesionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = SesionTest()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    """Crea las tablas antes de cada test."""
    Base.metadata.create_all(bind=engine_test)


def teardown_function():
    """Borra las tablas después de cada test."""
    Base.metadata.drop_all(bind=engine_test)


# ── Test health check ──────────────────────────────────
def test_health_check():
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"
    assert respuesta.json()["servicio"] == "iot-ingestion"


# ── Tests de lectura individual ────────────────────────
def test_recibir_lectura_valida():
    payload = {
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 55.0,
        "unidad": "%"
    }
    respuesta = client.post("/api/v1/telemetria/", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["id_logico"] == "SOIL_HUM_01"
    assert datos["valor_metrica"] == 55.0
    assert datos["bandera_calidad"] == "valido"


def test_recibir_lectura_invalida_fuera_de_rango():
    payload = {
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 150.0,
        "unidad": "%"
    }
    respuesta = client.post("/api/v1/telemetria/", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["bandera_calidad"] == "invalido"


def test_recibir_lectura_metrica_desconocida():
    payload = {
        "dispositivo_id": 1,
        "id_logico": "SENSOR_01",
        "tipo_metrica": "metrica_inexistente",
        "valor_metrica": 42.0
    }
    respuesta = client.post("/api/v1/telemetria/", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["bandera_calidad"] == "sospechoso"


def test_recibir_lectura_con_timestamp():
    payload = {
        "dispositivo_id": 1,
        "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire",
        "valor_metrica": 25.0,
        "unidad": "°C",
        "timestamp_lectura": "2026-03-23T10:00:00"
    }
    respuesta = client.post("/api/v1/telemetria/", json=payload)
    assert respuesta.status_code == 201
    assert respuesta.json()["valor_metrica"] == 25.0


# ── Tests de detección de alertas ─────────────────────
def test_lectura_genera_alerta_marchitez():
    payload = {
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 10.0,
        "unidad": "%"
    }
    respuesta = client.post("/api/v1/telemetria/", json=payload)
    assert respuesta.status_code == 201
    # Verifica que se generó alerta
    alertas = client.get("/api/v1/telemetria/alertas/SOIL_HUM_01")
    assert alertas.status_code == 200
    assert len(alertas.json()) >= 1
    assert "Marchitez" in alertas.json()[0]["condicion"]


def test_lectura_genera_alerta_helada():
    payload = {
        "dispositivo_id": 2,
        "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire",
        "valor_metrica": -5.0,
        "unidad": "°C"
    }
    respuesta = client.post("/api/v1/telemetria/", json=payload)
    assert respuesta.status_code == 201
    alertas = client.get("/api/v1/telemetria/alertas/AIR_TEMP_01")
    assert alertas.status_code == 200
    assert any("helada" in a["condicion"].lower() for a in alertas.json())


def test_lectura_normal_no_genera_alerta():
    payload = {
        "dispositivo_id": 1,
        "id_logico": "LUX_01",
        "tipo_metrica": "luz",
        "valor_metrica": 5000.0,
        "unidad": "Lux"
    }
    respuesta = client.post("/api/v1/telemetria/", json=payload)
    assert respuesta.status_code == 201
    alertas = client.get("/api/v1/telemetria/alertas/LUX_01")
    assert alertas.status_code == 404


# ── Tests de lote ──────────────────────────────────────
def test_recibir_lote_valido():
    payload = {
        "tipo_origen": "HTTP",
        "lecturas": [
            {"dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
             "tipo_metrica": "humedad_suelo", "valor_metrica": 60.0, "unidad": "%"},
            {"dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
             "tipo_metrica": "temperatura_aire", "valor_metrica": 22.0, "unidad": "°C"},
            {"dispositivo_id": 3, "id_logico": "SOIL_PH_01",
             "tipo_metrica": "ph_suelo", "valor_metrica": 6.5, "unidad": "pH"},
        ]
    }
    respuesta = client.post("/api/v1/telemetria/lote", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["total_registros"] == 3
    assert datos["registros_validos"] == 3
    assert datos["registros_invalidos"] == 0
    assert datos["estado"] == "procesado"


def test_recibir_lote_mixto():
    payload = {
        "tipo_origen": "HTTP",
        "lecturas": [
            {"dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
             "tipo_metrica": "humedad_suelo", "valor_metrica": 50.0},
            {"dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
             "tipo_metrica": "temperatura_aire", "valor_metrica": 999.0},
        ]
    }
    respuesta = client.post("/api/v1/telemetria/lote", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["total_registros"] == 2
    assert datos["registros_validos"] == 1
    assert datos["registros_invalidos"] == 1


# ── Tests de consultas ─────────────────────────────────
def test_ultimas_lecturas_sensor_existente():
    # Primero inserta lecturas
    for i in range(3):
        client.post("/api/v1/telemetria/", json={
            "dispositivo_id": 1,
            "id_logico": "WIND_01",
            "tipo_metrica": "velocidad_viento",
            "valor_metrica": float(10 + i),
            "unidad": "km/h"
        })
    respuesta = client.get("/api/v1/telemetria/ultimas/WIND_01")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 3


def test_ultimas_lecturas_sensor_inexistente():
    respuesta = client.get("/api/v1/telemetria/ultimas/SENSOR_FALSO")
    assert respuesta.status_code == 404


def test_listar_alertas():
    # Genera una alerta
    client.post("/api/v1/telemetria/", json={
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 5.0
    })
    respuesta = client.get("/api/v1/telemetria/alertas")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 1


def test_listar_alertas_por_severidad():
    client.post("/api/v1/telemetria/", json={
        "dispositivo_id": 2,
        "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire",
        "valor_metrica": -10.0
    })
    respuesta = client.get("/api/v1/telemetria/alertas?severidad=critica")
    assert respuesta.status_code == 200
    for alerta in respuesta.json():
        assert alerta["severidad"] == "critica"