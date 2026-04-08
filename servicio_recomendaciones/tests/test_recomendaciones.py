import os
os.environ["DATABASE_URL"]            = "sqlite:///./test_recomendaciones.db"
os.environ["ML_SERVICE_URL"]          = "http://localhost:8006"
os.environ["PROCESAMIENTO_SERVICE_URL"] = "http://localhost:8003"
os.environ["JWT_SECRET"]              = "agrisense_jwt_secret_2026"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from datetime import datetime, timezone, timedelta

from app.main import app
from app.database import Base, get_db
from app.services.recomendacion_service import inicializar_categorias

SQLALCHEMY_TEST_URL = "sqlite:///./test_recomendaciones.db"
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
    db = SesionTest()
    inicializar_categorias(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine_test)


client = TestClient(app)


# ── Health ────────────────────────────────────────────
def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["estado"] == "ok"


def test_health_router():
    res = client.get("/api/v1/recomendaciones/health")
    assert res.status_code == 200


# ── Categorias ────────────────────────────────────────
def test_listar_categorias():
    res = client.get("/api/v1/recomendaciones/categorias")
    assert res.status_code == 200
    assert len(res.json()) == 7
    nombres = [c["nombre"] for c in res.json()]
    assert "Riego" in nombres
    assert "Suelo" in nombres


# ── Generar ───────────────────────────────────────────
def test_generar_suelo_seco():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "parcela_id": 1, "id_logico": "SOIL_HUM_01",
        "humedad_suelo": 15.0, "temperatura_aire": 28.0,
        "lluvia": 0.0, "area_hectareas": 10.0, "tipo_cultivo": "maiz",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["total_generadas"] >= 1
    assert data["criticas"] >= 1
    assert data["ejecucion_id"] > 0


def test_generar_suelo_humedo():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 90.0, "temperatura_aire": 22.0,
        "humedad_aire": 95.0, "lluvia": 30.0,
    })
    assert res.status_code == 201
    assert res.json()["total_generadas"] >= 1


def test_generar_helada():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "temperatura_aire": -2.0, "humedad_suelo": 50.0,
        "humedad_aire": 80.0, "velocidad_viento": 10.0, "lluvia": 0.0,
    })
    assert res.status_code == 201
    assert res.json()["criticas"] >= 1


def test_generar_calor_extremo():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "temperatura_aire": 40.0, "humedad_suelo": 30.0, "lluvia": 0.0,
    })
    assert res.status_code == 201
    assert res.json()["altas"] >= 1


def test_generar_ph_acido():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "ph_suelo": 4.8, "humedad_suelo": 55.0, "temperatura_aire": 25.0,
    })
    assert res.status_code == 201
    titulos = [r["titulo"] for r in res.json()["recomendaciones"]]
    assert any("pH" in t or "acido" in t.lower() for t in titulos)


def test_generar_ph_alcalino():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "ph_suelo": 8.2, "humedad_suelo": 60.0, "temperatura_aire": 24.0,
    })
    assert res.status_code == 201
    assert res.json()["total_generadas"] >= 1


def test_generar_viento_fuerte():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "velocidad_viento": 65.0, "temperatura_aire": 25.0, "humedad_suelo": 50.0,
    })
    assert res.status_code == 201
    assert res.json()["criticas"] >= 1


def test_generar_condiciones_normales():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 60.0, "temperatura_aire": 25.0,
        "ph_suelo": 6.5, "lluvia": 10.0, "velocidad_viento": 5.0,
    })
    assert res.status_code == 201
    assert res.json()["bajas"] >= 1


def test_generar_sin_datos():
    res = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={})
    assert res.status_code == 201
    assert res.json()["total_generadas"] >= 1


# ── Aislamiento por usuario ───────────────────────────
def test_recomendaciones_aisladas_por_usuario():
    client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 15.0, "temperatura_aire": 30.0,
    })
    res = client.get("/api/v1/recomendaciones/", headers=AUTH2)
    assert res.status_code == 200
    assert len(res.json()) == 0


# ── CRUD ──────────────────────────────────────────────
def test_listar_recomendaciones_vacias():
    res = client.get("/api/v1/recomendaciones/", headers=AUTH)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_listar_recomendaciones_con_datos():
    gen = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 15.0, "temperatura_aire": 30.0, "area_hectareas": 5.0,
    })
    assert gen.status_code == 201
    res = client.get("/api/v1/recomendaciones/", headers=AUTH)
    assert len(res.json()) >= 1


def test_obtener_recomendacion():
    gen = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 15.0, "temperatura_aire": 30.0, "area_hectareas": 5.0,
    })
    rec_id = gen.json()["recomendaciones"][0]["id"]
    res = client.get(f"/api/v1/recomendaciones/{rec_id}", headers=AUTH)
    assert res.status_code == 200
    assert res.json()["id"] == rec_id


def test_obtener_recomendacion_otro_usuario():
    gen = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 15.0, "temperatura_aire": 30.0, "area_hectareas": 5.0,
    })
    assert gen.status_code == 201
    rec_id = gen.json()["recomendaciones"][0]["id"]
    res = client.get(f"/api/v1/recomendaciones/{rec_id}", headers=AUTH2)
    assert res.status_code == 404


def test_obtener_recomendacion_inexistente():
    res = client.get("/api/v1/recomendaciones/9999", headers=AUTH)
    assert res.status_code == 404


def test_crear_recomendacion_manual():
    res = client.post("/api/v1/recomendaciones/", headers=AUTH, json={
        "categoria_id": 1, "parcela_id": 1,
        "titulo": "Aplicar fertilizante NPK",
        "descripcion": "El cultivo requiere nutricion adicional",
        "accion": "Aplicar 50 kg/ha de NPK 15-15-15",
        "prioridad": "media", "fuente": "manual",
    })
    assert res.status_code == 201
    assert res.json()["titulo"] == "Aplicar fertilizante NPK"


def test_actualizar_estado():
    gen = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 15.0, "temperatura_aire": 30.0, "area_hectareas": 5.0,
    })
    rec_id = gen.json()["recomendaciones"][0]["id"]
    res = client.put(f"/api/v1/recomendaciones/{rec_id}/estado", headers=AUTH,
                     json={"estado": "aplicada"})
    assert res.status_code == 200
    assert res.json()["estado"] == "aplicada"


def test_actualizar_estado_invalido():
    gen = client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 15.0, "temperatura_aire": 30.0, "area_hectareas": 5.0,
    })
    rec_id = gen.json()["recomendaciones"][0]["id"]
    res = client.put(f"/api/v1/recomendaciones/{rec_id}/estado", headers=AUTH,
                     json={"estado": "estado_invalido"})
    assert res.status_code == 422


# ── Por parcela y sensor ──────────────────────────────
def test_recomendaciones_por_parcela():
    client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "parcela_id": 5, "humedad_suelo": 15.0, "area_hectareas": 5.0,
    })
    res = client.get("/api/v1/recomendaciones/parcela/5", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1
    for r in res.json():
        assert r["parcela_id"] == 5


def test_recomendaciones_por_sensor():
    client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "id_logico": "SOIL_HUM_02", "humedad_suelo": 12.0, "area_hectareas": 3.0,
    })
    res = client.get("/api/v1/recomendaciones/sensor/SOIL_HUM_02", headers=AUTH)
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_recomendaciones_activas():
    client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 10.0, "temperatura_aire": 28.0, "area_hectareas": 5.0,
    })
    res = client.get("/api/v1/recomendaciones/activas", headers=AUTH)
    assert res.status_code == 200
    for r in res.json():
        assert r["estado"] == "activa"


# ── Resumen ───────────────────────────────────────────
def test_resumen():
    client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 15.0, "temperatura_aire": 30.0, "area_hectareas": 5.0,
    })
    res = client.get("/api/v1/recomendaciones/resumen", headers=AUTH)
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert data["total"] >= 1


def test_resumen_aislado_por_usuario():
    client.post("/api/v1/recomendaciones/generar", headers=AUTH, json={
        "humedad_suelo": 15.0, "temperatura_aire": 30.0,
    })
    res = client.get("/api/v1/recomendaciones/resumen", headers=AUTH2)
    assert res.status_code == 200
    assert res.json()["total"] == 0