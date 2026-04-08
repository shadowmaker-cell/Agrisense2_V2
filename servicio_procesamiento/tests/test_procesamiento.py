import os
os.environ["DATABASE_URL"] = "sqlite:///./test_procesamiento.db"
os.environ["JWT_SECRET"]   = "agrisense_jwt_secret_2026"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from datetime import datetime, timezone, timedelta

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_procesamiento.db"
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
    assert res.json()["servicio"] == "stream-processor"


# ── Procesamiento manual ──────────────────────────────
def test_procesar_lectura_normal():
    res = client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 55.0, "unidad": "%"
    })
    assert res.status_code == 201
    assert res.json()["alertas_generadas"] == 0
    assert res.json()["evento_id"] is not None


def test_procesar_lectura_con_alerta_sequia():
    res = client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 10.0, "unidad": "%"
    })
    assert res.status_code == 201
    assert res.json()["alertas_generadas"] >= 1
    assert "sequia" in res.json()["tipos_alerta"]


def test_procesar_lectura_con_alerta_helada():
    res = client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire", "valor_metrica": -5.0, "unidad": "°C"
    })
    assert res.status_code == 201
    assert res.json()["alertas_generadas"] >= 1
    assert "helada" in res.json()["tipos_alerta"]


def test_procesar_lectura_critica():
    res = client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire", "valor_metrica": 42.0, "unidad": "°C"
    })
    assert res.status_code == 201
    assert res.json()["alertas_generadas"] >= 1


def test_procesar_viento_critico():
    res = client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 5, "id_logico": "WIND_01",
        "tipo_metrica": "velocidad_viento", "valor_metrica": 55.0, "unidad": "km/h"
    })
    assert res.status_code == 201
    assert "viento" in res.json()["tipos_alerta"]


# ── Eventos ───────────────────────────────────────────
def test_listar_eventos_vacio():
    res = client.get("/api/v1/procesamiento/eventos", headers=AUTH)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_listar_eventos_con_datos():
    client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 60.0
    })
    res = client.get("/api/v1/procesamiento/eventos", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_eventos_aislados_por_usuario():
    client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 60.0
    })
    res = client.get("/api/v1/procesamiento/eventos", headers=AUTH2)
    assert res.status_code == 200
    assert len(res.json()) == 0


def test_eventos_por_dispositivo():
    client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 3, "id_logico": "LUX_01",
        "tipo_metrica": "luz", "valor_metrica": 5000.0
    })
    res = client.get("/api/v1/procesamiento/eventos/LUX_01", headers=AUTH)
    assert res.status_code == 200
    assert res.json()[0]["id_logico"] == "LUX_01"


def test_eventos_dispositivo_inexistente():
    res = client.get("/api/v1/procesamiento/eventos/FALSO_99", headers=AUTH)
    assert res.status_code == 404


# ── Alertas ───────────────────────────────────────────
def test_listar_alertas_vacio():
    res = client.get("/api/v1/procesamiento/alertas", headers=AUTH)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_listar_alertas_con_datos():
    client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 5.0
    })
    res = client.get("/api/v1/procesamiento/alertas", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_alertas_aisladas_por_usuario():
    client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 5.0
    })
    res = client.get("/api/v1/procesamiento/alertas", headers=AUTH2)
    assert res.status_code == 200
    assert len(res.json()) == 0


def test_filtrar_alertas_por_severidad():
    client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
        "tipo_metrica": "temperatura_aire", "valor_metrica": -10.0
    })
    res = client.get("/api/v1/procesamiento/alertas?severidad=critica", headers=AUTH)
    assert res.status_code == 200
    for alerta in res.json():
        assert alerta["severidad"] == "critica"


def test_alertas_por_dispositivo():
    client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 8.0
    })
    res = client.get("/api/v1/procesamiento/alertas/SOIL_HUM_01", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


# ── Resumen ───────────────────────────────────────────
def test_resumen_procesamiento():
    client.post("/api/v1/procesamiento/manual", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_metrica": "humedad_suelo", "valor_metrica": 5.0
    })
    res = client.get("/api/v1/procesamiento/resumen", headers=AUTH)
    assert res.status_code == 200
    data = res.json()
    assert "total_eventos" in data
    assert "total_alertas" in data
    assert data["total_eventos"] >= 1