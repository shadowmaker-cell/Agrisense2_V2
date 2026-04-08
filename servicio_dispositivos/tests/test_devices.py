import os
os.environ["DATABASE_URL"] = "sqlite:///./test_devices.db"
os.environ["JWT_SECRET"]   = "agrisense_jwt_secret_2026"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from datetime import datetime, timezone, timedelta

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_devices.db"
engine_test = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
SesionTest  = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = SesionTest()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def make_token(usuario_id: int = 1, rol: str = "administrador") -> str:
    payload = {
        "sub":    str(usuario_id),
        "email":  "admin@agrisense.co",
        "rol":    rol,
        "nombre": "Admin",
        "exp":    datetime.now(timezone.utc) + timedelta(hours=1),
        "type":   "access",
    }
    return jwt.encode(payload, "agrisense_jwt_secret_2026", algorithm="HS256")


AUTH = {"Authorization": f"Bearer {make_token()}"}


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


client = TestClient(app)


# ── Seed tipos ────────────────────────────────────────
def seed_tipos():
    from app.models.device import TipoDispositivo
    db = SesionTest()
    if db.query(TipoDispositivo).count() == 0:
        db.add(TipoDispositivo(
            nombre="Sensor Humedad Suelo", categoria="suelo",
            unidad="%", rango_minimo=0, rango_maximo=100,
            metricas_permitidas=["humedad_suelo"],
        ))
        db.commit()
    db.close()


# ── Health ────────────────────────────────────────────
def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["estado"] == "ok"


def test_health_router():
    res = client.get("/api/v1/dispositivos/health")
    assert res.status_code == 200


# ── Tipos ─────────────────────────────────────────────
def test_listar_tipos():
    seed_tipos()
    res = client.get("/api/v1/dispositivos/tipos")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ── Registrar dispositivo ─────────────────────────────
def test_registrar_dispositivo():
    seed_tipos()
    res = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
        "version_firmware": "1.0.0",
        "estado": "activo",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["id_logico"] == "SOIL_HUM_01"
    assert data["estado"] == "activo"

def test_registrar_dispositivo_serial_duplicado():
    seed_tipos()
    client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    })
    res = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_02",
        "numero_serial":"SN-HUM-CAP-001",
    })
    assert res.status_code == 400


def test_registrar_dispositivo_id_logico_duplicado():
    seed_tipos()
    client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    })
    res = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-002",
    })
    assert res.status_code == 400


def test_registrar_dispositivo_tipo_inexistente():
    res = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 9999,
        "id_logico":    "SOIL_HUM_99",
        "numero_serial":"SN-HUM-CAP-099",
    })
    assert res.status_code == 404


# ── Listar ────────────────────────────────────────────
def test_listar_dispositivos():
    seed_tipos()
    client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    })
    res = client.get("/api/v1/dispositivos/", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_listar_dispositivos_aislados_por_usuario():
    seed_tipos()
    # Usuario 1 registra un sensor
    client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    })
    # Usuario 2 no ve sensores del usuario 1
    auth2 = {"Authorization": f"Bearer {make_token(usuario_id=2)}"}
    res = client.get("/api/v1/dispositivos/", headers=auth2)
    assert res.status_code == 200
    assert len(res.json()) == 0


# ── Obtener ───────────────────────────────────────────
def test_obtener_dispositivo_existente():
    seed_tipos()
    created = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    }).json()
    res = client.get(f"/api/v1/dispositivos/{created['id']}", headers=AUTH)
    assert res.status_code == 200
    assert res.json()["id_logico"] == "SOIL_HUM_01"


def test_obtener_dispositivo_inexistente():
    res = client.get("/api/v1/dispositivos/9999", headers=AUTH)
    assert res.status_code == 404


def test_obtener_dispositivo_otro_usuario():
    seed_tipos()
    created = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    }).json()
    auth2 = {"Authorization": f"Bearer {make_token(usuario_id=2)}"}
    res = client.get(f"/api/v1/dispositivos/{created['id']}", headers=auth2)
    assert res.status_code == 404


# ── Actualizar ────────────────────────────────────────
def test_actualizar_estado_dispositivo():
    seed_tipos()
    created = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    }).json()
    res = client.put(f"/api/v1/dispositivos/{created['id']}", headers=AUTH,
                     json={"estado": "mantenimiento"})
    assert res.status_code == 200
    assert res.json()["estado"] == "mantenimiento"


def test_no_puede_modificar_serial():
    seed_tipos()
    created = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    }).json()
    res = client.put(f"/api/v1/dispositivos/{created['id']}", headers=AUTH,
                     json={"numero_serial": "SN-NUEVO-001"})
    assert res.status_code == 422


# ── Metricas ──────────────────────────────────────────
def test_obtener_metricas_dispositivo():
    seed_tipos()
    created = client.post("/api/v1/dispositivos/", headers=AUTH, json={
        "tipo_dispositivo_id": 1,
        "id_logico":    "SOIL_HUM_01",
        "numero_serial":"SN-HUM-CAP-001",
    }).json()
    res = client.get(f"/api/v1/dispositivos/{created['id']}/metricas", headers=AUTH)
    assert res.status_code == 200
    assert "metricas_permitidas" in res.json()


# ── Sin token ─────────────────────────────────────────
def test_sin_token_retorna_401():
    res = client.get("/api/v1/dispositivos/")
    assert res.status_code == 401


def test_token_invalido_retorna_401():
    res = client.get("/api/v1/dispositivos/",
                     headers={"Authorization": "Bearer tokenfalso"})
    assert res.status_code == 401