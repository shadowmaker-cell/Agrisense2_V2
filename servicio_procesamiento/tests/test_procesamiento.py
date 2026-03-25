import os
os.environ["DATABASE_URL"] = "sqlite:///./test_procesamiento.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_procesamiento.db"

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
    Base.metadata.create_all(bind=engine_test)


def teardown_function():
    Base.metadata.drop_all(bind=engine_test)


# ── Health check ───────────────────────────────────────
def test_health_check():
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"
    assert respuesta.json()["servicio"] == "stream-processor"


# ── Tests de procesamiento manual ─────────────────────
def test_procesar_lectura_normal():
    payload = {
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 55.0,
        "unidad": "%"
    }
    respuesta = client.post("/api/v1/procesamiento/manual", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["alertas_generadas"] == 0
    assert datos["evento_id"] is not None


def test_procesar_lectura_con_alerta_sequia():
    payload = {
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 10.0,
        "unidad": "%"
    }
    respuesta = client.post("/api/v1/procesamiento/manual", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["alertas_generadas"] >= 1
    assert "sequia" in datos["tipos_alerta"]


def test_procesar_lectura_con_alerta_helada():
    payload = {
        "dispositivo_id": 2,
        "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire",
        "valor_metrica": -5.0,
        "unidad": "°C"
    }
    respuesta = client.post("/api/v1/procesamiento/manual", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["alertas_generadas"] >= 1
    assert "helada" in datos["tipos_alerta"]


def test_procesar_lectura_critica():
    payload = {
        "dispositivo_id": 2,
        "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire",
        "valor_metrica": 42.0,
        "unidad": "°C"
    }
    respuesta = client.post("/api/v1/procesamiento/manual", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["alertas_generadas"] >= 1


def test_procesar_viento_critico():
    payload = {
        "dispositivo_id": 5,
        "id_logico": "WIND_01",
        "tipo_metrica": "velocidad_viento",
        "valor_metrica": 55.0,
        "unidad": "km/h"
    }
    respuesta = client.post("/api/v1/procesamiento/manual", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert "viento" in datos["tipos_alerta"]


# ── Tests de consultas ─────────────────────────────────
def test_listar_eventos_vacio():
    respuesta = client.get("/api/v1/procesamiento/eventos")
    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)


def test_listar_eventos_con_datos():
    client.post("/api/v1/procesamiento/manual", json={
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 60.0
    })
    respuesta = client.get("/api/v1/procesamiento/eventos")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 1


def test_eventos_por_dispositivo():
    client.post("/api/v1/procesamiento/manual", json={
        "dispositivo_id": 3,
        "id_logico": "LUX_01",
        "tipo_metrica": "luz",
        "valor_metrica": 5000.0
    })
    respuesta = client.get("/api/v1/procesamiento/eventos/LUX_01")
    assert respuesta.status_code == 200
    assert respuesta.json()[0]["id_logico"] == "LUX_01"


def test_eventos_dispositivo_inexistente():
    respuesta = client.get("/api/v1/procesamiento/eventos/FALSO_99")
    assert respuesta.status_code == 404


# ── Tests de alertas ───────────────────────────────────
def test_listar_alertas_vacio():
    respuesta = client.get("/api/v1/procesamiento/alertas")
    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)


def test_listar_alertas_con_datos():
    client.post("/api/v1/procesamiento/manual", json={
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 5.0
    })
    respuesta = client.get("/api/v1/procesamiento/alertas")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 1


def test_filtrar_alertas_por_severidad():
    client.post("/api/v1/procesamiento/manual", json={
        "dispositivo_id": 2,
        "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire",
        "valor_metrica": -10.0
    })
    respuesta = client.get("/api/v1/procesamiento/alertas?severidad=critica")
    assert respuesta.status_code == 200
    for alerta in respuesta.json():
        assert alerta["severidad"] == "critica"


def test_alertas_por_dispositivo():
    client.post("/api/v1/procesamiento/manual", json={
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 8.0
    })
    respuesta = client.get("/api/v1/procesamiento/alertas/SOIL_HUM_01")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 1


# ── Test resumen ───────────────────────────────────────
def test_resumen_procesamiento():
    client.post("/api/v1/procesamiento/manual", json={
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo",
        "valor_metrica": 5.0
    })
    respuesta = client.get("/api/v1/procesamiento/resumen")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "total_eventos" in datos
    assert "total_alertas" in datos
    assert datos["total_eventos"] >= 1