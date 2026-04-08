import os
os.environ["DATABASE_URL"] = "sqlite:///./test_parcelas.db"
os.environ["JWT_SECRET"]   = "agrisense_jwt_secret_2026"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from datetime import datetime, timezone, timedelta

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_parcelas.db"
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

PARCELA_BASE = {
    "nombre": "Parcela Norte", "area_hectareas": 5.5,
    "tipo_suelo": "arcilloso", "latitud": 8.7534,
    "longitud": -75.8811, "municipio": "Monteria",
    "departamento": "Cordoba", "estado": "activa"
}


# ── Health ────────────────────────────────────────────
def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["estado"] == "ok"


# ── Tipos de cultivo ──────────────────────────────────
def test_crear_tipo_cultivo():
    res = client.post("/api/v1/parcelas/tipos-cultivo", json={"nombre": "Maiz"})
    assert res.status_code == 201
    assert res.json()["nombre"] == "Maiz"


def test_listar_tipos_cultivo():
    client.post("/api/v1/parcelas/tipos-cultivo", json={"nombre": "Cafe"})
    res = client.get("/api/v1/parcelas/tipos-cultivo")
    assert res.status_code == 200
    assert len(res.json()) >= 1


# ── Parcelas CRUD ─────────────────────────────────────
def test_crear_parcela():
    res = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE)
    assert res.status_code == 201
    assert res.json()["nombre"] == "Parcela Norte"


def test_listar_parcelas():
    client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE)
    res = client.get("/api/v1/parcelas/", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_listar_parcelas_aisladas_por_usuario():
    client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE)
    res = client.get("/api/v1/parcelas/", headers=AUTH2)
    assert res.status_code == 200
    assert len(res.json()) == 0


def test_obtener_parcela():
    creada = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    res = client.get(f"/api/v1/parcelas/{creada['id']}", headers=AUTH)
    assert res.status_code == 200
    assert res.json()["nombre"] == "Parcela Norte"


def test_parcela_inexistente():
    res = client.get("/api/v1/parcelas/9999", headers=AUTH)
    assert res.status_code == 404


def test_obtener_parcela_otro_usuario():
    creada = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    res = client.get(f"/api/v1/parcelas/{creada['id']}", headers=AUTH2)
    assert res.status_code == 404


def test_actualizar_parcela():
    creada = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    res = client.put(f"/api/v1/parcelas/{creada['id']}", headers=AUTH, json={
        "nombre": "Parcela Actualizada", "area_hectareas": 8.0, "estado": "activa"
    })
    assert res.status_code == 200
    assert res.json()["nombre"] == "Parcela Actualizada"


def test_filtrar_parcelas_por_estado():
    client.post("/api/v1/parcelas/", headers=AUTH, json={**PARCELA_BASE, "estado": "inactiva"})
    res = client.get("/api/v1/parcelas/?estado=inactiva", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1
    for p in res.json():
        assert p["estado"] == "inactiva"


def test_eliminar_parcela():
    creada = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    res = client.delete(f"/api/v1/parcelas/{creada['id']}", headers=AUTH)
    assert res.status_code == 200
    res2 = client.get(f"/api/v1/parcelas/{creada['id']}", headers=AUTH)
    assert res2.status_code == 404


# ── Sensores de parcela ───────────────────────────────
def test_asignar_sensor():
    parcela = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    res = client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", headers=AUTH, json={
        "dispositivo_id": 1,
        "id_logico":      "SOIL_HUM_01",
        "notas":          "Sector norte"
    })
    assert res.status_code == 201
    assert res.json()["id_logico"] == "SOIL_HUM_01"


def test_asignar_sensor_duplicado():
    parcela = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", headers=AUTH,
                json={"dispositivo_id": 1, "id_logico": "AIR_TEMP_01"})
    res = client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", headers=AUTH,
                      json={"dispositivo_id": 1, "id_logico": "AIR_TEMP_01"})
    assert res.status_code == 400


def test_listar_sensores_parcela():
    parcela = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", headers=AUTH,
                json={"dispositivo_id": 1, "id_logico": "LUX_01"})
    res = client.get(f"/api/v1/parcelas/{parcela['id']}/sensores", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_desasignar_sensor():
    parcela = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    sensor = client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", headers=AUTH,
                         json={"dispositivo_id": 1, "id_logico": "WIND_01"}).json()
    res = client.delete(f"/api/v1/parcelas/{parcela['id']}/sensores/{sensor['id']}", headers=AUTH)
    assert res.status_code == 200


# ── Historial de cultivos ─────────────────────────────
def test_agregar_historial():
    tipo    = client.post("/api/v1/parcelas/tipos-cultivo", json={"nombre": "Yuca Test"}).json()
    parcela = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    res = client.post(f"/api/v1/parcelas/{parcela['id']}/historial", headers=AUTH, json={
        "tipo_cultivo_id":  tipo["id"],
        "fecha_siembra":    "2026-01-15T00:00:00",
        "etapa_fenologica": "vegetativo",
        "estado":           "activo"
    })
    assert res.status_code == 201
    assert res.json()["tipo_cultivo_nombre"] == "Yuca Test"


def test_listar_historial():
    tipo    = client.post("/api/v1/parcelas/tipos-cultivo", json={"nombre": "Maiz Test"}).json()
    parcela = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    client.post(f"/api/v1/parcelas/{parcela['id']}/historial", headers=AUTH, json={
        "tipo_cultivo_id": tipo["id"],
        "fecha_siembra":   "2026-02-01T00:00:00",
        "estado":          "activo"
    })
    res = client.get(f"/api/v1/parcelas/{parcela['id']}/historial", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_actualizar_historial():
    tipo    = client.post("/api/v1/parcelas/tipos-cultivo", json={"nombre": "Cafe Test"}).json()
    parcela = client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE).json()
    hist = client.post(f"/api/v1/parcelas/{parcela['id']}/historial", headers=AUTH, json={
        "tipo_cultivo_id": tipo["id"],
        "fecha_siembra":   "2026-01-01T00:00:00",
        "estado":          "activo"
    }).json()
    res = client.put(f"/api/v1/parcelas/{parcela['id']}/historial/{hist['id']}", headers=AUTH, json={
        "tipo_cultivo_id": tipo["id"],
        "fecha_siembra":   "2026-01-01T00:00:00",
        "estado":          "finalizado",
        "rendimiento_kg":  5000.0
    })
    assert res.status_code == 200
    assert res.json()["estado"] == "finalizado"


# ── Resumen ───────────────────────────────────────────
def test_resumen_parcelas():
    client.post("/api/v1/parcelas/", headers=AUTH, json=PARCELA_BASE)
    res = client.get("/api/v1/parcelas/resumen", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


# ── Sin token ─────────────────────────────────────────
def test_sin_token_retorna_401():
    res = client.get("/api/v1/parcelas/")
    assert res.status_code == 401


def test_token_invalido_retorna_401():
    res = client.get("/api/v1/parcelas/",
                     headers={"Authorization": "Bearer tokenfalso"})
    assert res.status_code == 401