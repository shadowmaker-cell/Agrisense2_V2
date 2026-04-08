import os
os.environ["DATABASE_URL"] = "sqlite:///./test_ingesta.db"
os.environ["JWT_SECRET"]   = "agrisense_jwt_secret_2026"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from datetime import datetime, timezone, timedelta

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_ingesta.db"
engine_test = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
SesionTest  = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = SesionTest()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def make_token(usuario_id: int = 1) -> str:
    payload = {
        "sub":    str(usuario_id),
        "email":  "admin@agrisense.co",
        "rol":    "administrador",
        "nombre": "Admin",
        "exp":    datetime.now(timezone.utc) + timedelta(hours=1),
        "type":   "access",
    }
    return jwt.encode(payload, "agrisense_jwt_secret_2026", algorithm="HS256")


AUTH  = {"Authorization": f"Bearer {make_token(1)}"}
AUTH2 = {"Authorization": f"Bearer {make_token(2)}"}


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


client = TestClient(app)


# ── Health ────────────────────────────────────────────
def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["estado"] == "ok"
    assert res.json()["servicio"] == "iot-ingestion"


# ── Lectura individual ────────────────────────────────
def test_recibir_lectura_valida():
    res = client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 55.0, "unidad": "%"
    })
    assert res.status_code == 201
    assert res.json()["id_logico"] == "SOIL_HUM_01"
    assert res.json()["valor_metrica"] == 55.0
    assert res.json()["bandera_calidad"] == "valido"


def test_recibir_lectura_invalida_fuera_de_rango():
    res = client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 150.0, "unidad": "%"
    })
    assert res.status_code == 201
    assert res.json()["bandera_calidad"] == "invalido"


def test_recibir_lectura_metrica_desconocida():
    res = client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SENSOR_01",
        "tipo_metrica": "metrica_inexistente", "valor_metrica": 42.0
    })
    assert res.status_code == 201
    assert res.json()["bandera_calidad"] == "sospechoso"


def test_recibir_lectura_con_timestamp():
    res = client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire", "valor_metrica": 25.0,
        "unidad": "°C", "timestamp_lectura": "2026-03-23T10:00:00"
    })
    assert res.status_code == 201
    assert res.json()["valor_metrica"] == 25.0


# ── Alertas ───────────────────────────────────────────
def test_lectura_genera_alerta_marchitez():
    client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 10.0, "unidad": "%"
    })
    alertas = client.get("/api/v1/telemetria/alertas/SOIL_HUM_01", headers=AUTH)
    assert alertas.status_code == 200
    assert len(alertas.json()) >= 1
    assert "Marchitez" in alertas.json()[0]["condicion"]


def test_lectura_genera_alerta_helada():
    client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire", "valor_metrica": -5.0, "unidad": "°C"
    })
    alertas = client.get("/api/v1/telemetria/alertas/AIR_TEMP_01", headers=AUTH)
    assert alertas.status_code == 200
    assert any("helada" in a["condicion"].lower() for a in alertas.json())


def test_lectura_normal_no_genera_alerta():
    client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "LUX_01",
        "tipo_metrica": "luz", "valor_metrica": 5000.0, "unidad": "Lux"
    })
    alertas = client.get("/api/v1/telemetria/alertas/LUX_01", headers=AUTH)
    assert alertas.status_code == 404


# ── Aislamiento por usuario ───────────────────────────
def test_alertas_aisladas_por_usuario():
    client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 5.0
    })
    alertas_u1 = client.get("/api/v1/telemetria/alertas", headers=AUTH)
    alertas_u2 = client.get("/api/v1/telemetria/alertas", headers=AUTH2)
    assert len(alertas_u1.json()) >= 1
    assert len(alertas_u2.json()) == 0


# ── Lote ──────────────────────────────────────────────
def test_recibir_lote_valido():
    res = client.post("/api/v1/telemetria/lote", headers=AUTH, json={
        "tipo_origen": "HTTP",
        "lecturas": [
            {"dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
             "tipo_metrica": "humedad_suelo", "valor_metrica": 60.0, "unidad": "%"},
            {"dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
             "tipo_metrica": "temperatura_aire", "valor_metrica": 22.0, "unidad": "°C"},
            {"dispositivo_id": 3, "id_logico": "SOIL_PH_01",
             "tipo_metrica": "ph_suelo", "valor_metrica": 6.5, "unidad": "pH"},
        ]
    })
    assert res.status_code == 201
    assert res.json()["total_registros"] == 3
    assert res.json()["registros_validos"] == 3
    assert res.json()["estado"] == "procesado"


def test_recibir_lote_mixto():
    res = client.post("/api/v1/telemetria/lote", headers=AUTH, json={
        "tipo_origen": "HTTP",
        "lecturas": [
            {"dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
             "tipo_metrica": "humedad_suelo", "valor_metrica": 50.0},
            {"dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
             "tipo_metrica": "temperatura_aire", "valor_metrica": 999.0},
        ]
    })
    assert res.status_code == 201
    assert res.json()["registros_validos"] == 1
    assert res.json()["registros_invalidos"] == 1


# ── Consultas ─────────────────────────────────────────
def test_ultimas_lecturas_sensor_existente():
    for i in range(3):
        client.post("/api/v1/telemetria/", headers=AUTH, json={
            "dispositivo_id": 1, "id_logico": "WIND_01",
            "tipo_metrica": "velocidad_viento",
            "valor_metrica": float(10 + i), "unidad": "km/h"
        })
    res = client.get("/api/v1/telemetria/ultimas/WIND_01", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) == 3


def test_ultimas_lecturas_sensor_inexistente():
    res = client.get("/api/v1/telemetria/ultimas/SENSOR_FALSO", headers=AUTH)
    assert res.status_code == 404


def test_listar_alertas():
    client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 5.0
    })
    res = client.get("/api/v1/telemetria/alertas", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_listar_alertas_por_severidad():
    client.post("/api/v1/telemetria/", headers=AUTH, json={
        "dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire", "valor_metrica": -10.0
    })
    res = client.get("/api/v1/telemetria/alertas?severidad=critica", headers=AUTH)
    assert res.status_code == 200
    for alerta in res.json():
        assert alerta["severidad"] == "critica"