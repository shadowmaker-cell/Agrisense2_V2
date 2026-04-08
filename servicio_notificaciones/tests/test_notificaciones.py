import os
os.environ["DATABASE_URL"] = "sqlite:///./test_notificaciones.db"
os.environ["JWT_SECRET"]   = "agrisense_jwt_secret_2026"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from datetime import datetime, timezone, timedelta

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_notificaciones.db"
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

NOTIF_BASE = {
    "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
    "tipo_alerta": "sequia", "tipo_metrica": "humedad_suelo",
    "valor": 5.0, "condicion": "< 10%",
    "severidad": "critica", "canal": "push"
}


# ── Health ────────────────────────────────────────────
def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["estado"] == "ok"
    assert res.json()["servicio"] == "notification-service"


# ── Envio ─────────────────────────────────────────────
def test_enviar_notificacion_critica():
    res = client.post("/api/v1/notificaciones/enviar", headers=AUTH, json={
        "dispositivo_id": 2, "id_logico": "AIR_TEMP_01",
        "tipo_alerta": "helada", "tipo_metrica": "temperatura_aire",
        "valor": -5.0, "condicion": "< 0C — Helada inminente",
        "severidad": "critica", "canal": "push"
    })
    assert res.status_code == 201
    assert res.json()["estado"] == "enviada"
    assert res.json()["canal"] == "push"


def test_enviar_notificacion_alta():
    res = client.post("/api/v1/notificaciones/enviar", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_alerta": "sequia", "tipo_metrica": "humedad_suelo",
        "valor": 10.0, "condicion": "< 20% — Marchitez inminente",
        "severidad": "alta", "canal": "sistema"
    })
    assert res.status_code == 201
    assert res.json()["estado"] == "enviada"


def test_enviar_notificacion_media():
    res = client.post("/api/v1/notificaciones/enviar", headers=AUTH, json={
        "dispositivo_id": 3, "id_logico": "LUX_01",
        "tipo_alerta": "luz", "tipo_metrica": "luz",
        "valor": 500.0, "condicion": "< 2000 Lux",
        "severidad": "media", "canal": "sistema"
    })
    assert res.status_code == 201
    assert res.json()["estado"] == "enviada"


def test_severidad_invalida():
    res = client.post("/api/v1/notificaciones/enviar", headers=AUTH, json={
        "dispositivo_id": 1, "id_logico": "SOIL_HUM_01",
        "tipo_alerta": "sequia", "tipo_metrica": "humedad_suelo",
        "valor": 10.0, "condicion": "test",
        "severidad": "invalida", "canal": "sistema"
    })
    assert res.status_code == 422


# ── Listar ────────────────────────────────────────────
def test_listar_notificaciones_vacio():
    res = client.get("/api/v1/notificaciones/", headers=AUTH)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_listar_notificaciones_con_datos():
    client.post("/api/v1/notificaciones/enviar", headers=AUTH, json=NOTIF_BASE)
    res = client.get("/api/v1/notificaciones/", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_notificaciones_aisladas_por_usuario():
    client.post("/api/v1/notificaciones/enviar", headers=AUTH, json=NOTIF_BASE)
    res = client.get("/api/v1/notificaciones/", headers=AUTH2)
    assert res.status_code == 200
    assert len(res.json()) == 0


def test_obtener_notificacion_por_id():
    creada = client.post("/api/v1/notificaciones/enviar", headers=AUTH, json=NOTIF_BASE).json()
    res = client.get(f"/api/v1/notificaciones/{creada['notificacion_id']}", headers=AUTH)
    assert res.status_code == 200
    assert res.json()["id"] == creada["notificacion_id"]


def test_notificacion_inexistente():
    res = client.get("/api/v1/notificaciones/9999", headers=AUTH)
    assert res.status_code == 404


def test_marcar_leida():
    creada = client.post("/api/v1/notificaciones/enviar", headers=AUTH, json=NOTIF_BASE).json()
    res = client.put(f"/api/v1/notificaciones/{creada['notificacion_id']}/leer", headers=AUTH)
    assert res.status_code == 200


def test_notificaciones_por_dispositivo():
    client.post("/api/v1/notificaciones/enviar", headers=AUTH, json={
        "dispositivo_id": 4, "id_logico": "RAIN_01",
        "tipo_alerta": "inundacion", "tipo_metrica": "lluvia",
        "valor": 60.0, "condicion": "> 50 mm/h",
        "severidad": "critica", "canal": "push"
    })
    res = client.get("/api/v1/notificaciones/dispositivo/RAIN_01", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_dispositivo_sin_notificaciones():
    res = client.get("/api/v1/notificaciones/dispositivo/FALSO_99", headers=AUTH)
    assert res.status_code == 404


# ── Resumen ───────────────────────────────────────────
def test_resumen_notificaciones():
    client.post("/api/v1/notificaciones/enviar", headers=AUTH, json=NOTIF_BASE)
    res = client.get("/api/v1/notificaciones/resumen/general", headers=AUTH)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "criticas" in data
    assert data["total"] >= 1


def test_resumen_aislado_por_usuario():
    client.post("/api/v1/notificaciones/enviar", headers=AUTH, json=NOTIF_BASE)
    res = client.get("/api/v1/notificaciones/resumen/general", headers=AUTH2)
    assert res.status_code == 200
    assert res.json()["total"] == 0


# ── Preferencias ──────────────────────────────────────
def test_guardar_preferencias():
    res = client.post("/api/v1/notificaciones/preferencias/1", json={
        "canal_preferido": "push", "activo": True,
        "alertas_criticas": True, "alertas_altas": True,
        "alertas_medias": False, "alertas_bajas": False
    })
    assert res.status_code == 200
    assert res.json()["canal_preferido"] == "push"


def test_actualizar_preferencias():
    client.post("/api/v1/notificaciones/preferencias/1", json={
        "canal_preferido": "push", "activo": True,
        "alertas_criticas": True, "alertas_altas": True,
        "alertas_medias": False, "alertas_bajas": False
    })
    res = client.post("/api/v1/notificaciones/preferencias/1", json={
        "canal_preferido": "email", "activo": True,
        "alertas_criticas": True, "alertas_altas": True,
        "alertas_medias": True, "alertas_bajas": False
    })
    assert res.status_code == 200
    assert res.json()["canal_preferido"] == "email"