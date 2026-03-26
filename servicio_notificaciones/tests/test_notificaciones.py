import os
os.environ["DATABASE_URL"] = "sqlite:///./test_notificaciones.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_notificaciones.db"

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
    assert respuesta.json()["servicio"] == "notification-service"


# ── Tests de envío manual ──────────────────────────────
def test_enviar_notificacion_critica():
    payload = {
        "dispositivo_id": 2,
        "id_logico":      "AIR_TEMP_01",
        "tipo_alerta":    "helada",
        "tipo_metrica":   "temperatura_aire",
        "valor":          -5.0,
        "condicion":      "< 0°C — Helada inminente",
        "severidad":      "critica",
        "canal":          "push"
    }
    respuesta = client.post("/api/v1/notificaciones/enviar", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["estado"] == "enviada"
    assert datos["canal"] == "push"


def test_enviar_notificacion_alta():
    payload = {
        "dispositivo_id": 1,
        "id_logico":      "SOIL_HUM_01",
        "tipo_alerta":    "sequia",
        "tipo_metrica":   "humedad_suelo",
        "valor":          10.0,
        "condicion":      "< 20% — Marchitez inminente",
        "severidad":      "alta",
        "canal":          "sistema"
    }
    respuesta = client.post("/api/v1/notificaciones/enviar", json=payload)
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "enviada"


def test_enviar_notificacion_media():
    payload = {
        "dispositivo_id": 3,
        "id_logico":      "LUX_01",
        "tipo_alerta":    "luz",
        "tipo_metrica":   "luz",
        "valor":          500.0,
        "condicion":      "< 2000 Lux — Déficit de luz",
        "severidad":      "media",
        "canal":          "sistema"
    }
    respuesta = client.post("/api/v1/notificaciones/enviar", json=payload)
    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "enviada"


def test_severidad_invalida():
    payload = {
        "dispositivo_id": 1,
        "id_logico":      "SOIL_HUM_01",
        "tipo_alerta":    "sequia",
        "tipo_metrica":   "humedad_suelo",
        "valor":          10.0,
        "condicion":      "test",
        "severidad":      "invalida",
        "canal":          "sistema"
    }
    respuesta = client.post("/api/v1/notificaciones/enviar", json=payload)
    assert respuesta.status_code == 422


# ── Tests de consultas ─────────────────────────────────
def test_listar_notificaciones_vacio():
    respuesta = client.get("/api/v1/notificaciones/")
    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)


def test_listar_notificaciones_con_datos():
    client.post("/api/v1/notificaciones/enviar", json={
        "dispositivo_id": 1,
        "id_logico":      "SOIL_HUM_01",
        "tipo_alerta":    "sequia",
        "tipo_metrica":   "humedad_suelo",
        "valor":          5.0,
        "condicion":      "< 10% — Sequía crítica",
        "severidad":      "critica",
        "canal":          "push"
    })
    respuesta = client.get("/api/v1/notificaciones/")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 1


def test_obtener_notificacion_por_id():
    creada = client.post("/api/v1/notificaciones/enviar", json={
        "dispositivo_id": 1,
        "id_logico":      "SOIL_HUM_01",
        "tipo_alerta":    "sequia",
        "tipo_metrica":   "humedad_suelo",
        "valor":          5.0,
        "condicion":      "< 10%",
        "severidad":      "critica",
        "canal":          "push"
    }).json()
    respuesta = client.get(f"/api/v1/notificaciones/{creada['notificacion_id']}")
    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == creada["notificacion_id"]


def test_notificacion_inexistente():
    respuesta = client.get("/api/v1/notificaciones/9999")
    assert respuesta.status_code == 404


def test_marcar_leida():
    creada = client.post("/api/v1/notificaciones/enviar", json={
        "dispositivo_id": 1,
        "id_logico":      "SOIL_HUM_01",
        "tipo_alerta":    "sequia",
        "tipo_metrica":   "humedad_suelo",
        "valor":          5.0,
        "condicion":      "< 10%",
        "severidad":      "alta",
        "canal":          "sistema"
    }).json()
    respuesta = client.put(
        f"/api/v1/notificaciones/{creada['notificacion_id']}/leer"
    )
    assert respuesta.status_code == 200


def test_notificaciones_por_dispositivo():
    client.post("/api/v1/notificaciones/enviar", json={
        "dispositivo_id": 4,
        "id_logico":      "RAIN_01",
        "tipo_alerta":    "inundacion",
        "tipo_metrica":   "lluvia",
        "valor":          60.0,
        "condicion":      "> 50 mm/h — Inundación",
        "severidad":      "critica",
        "canal":          "push"
    })
    respuesta = client.get("/api/v1/notificaciones/dispositivo/RAIN_01")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 1


def test_dispositivo_sin_notificaciones():
    respuesta = client.get("/api/v1/notificaciones/dispositivo/FALSO_99")
    assert respuesta.status_code == 404


# ── Test resumen ───────────────────────────────────────
def test_resumen_notificaciones():
    client.post("/api/v1/notificaciones/enviar", json={
        "dispositivo_id": 1,
        "id_logico":      "SOIL_HUM_01",
        "tipo_alerta":    "sequia",
        "tipo_metrica":   "humedad_suelo",
        "valor":          5.0,
        "condicion":      "< 10%",
        "severidad":      "critica",
        "canal":          "push"
    })
    respuesta = client.get("/api/v1/notificaciones/resumen/general")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "total" in datos
    assert "criticas" in datos
    assert datos["total"] >= 1


# ── Test preferencias ──────────────────────────────────
def test_guardar_preferencias():
    payload = {
        "canal_preferido":  "push",
        "activo":           True,
        "alertas_criticas": True,
        "alertas_altas":    True,
        "alertas_medias":   False,
        "alertas_bajas":    False
    }
    respuesta = client.post(
        "/api/v1/notificaciones/preferencias/1",
        json=payload
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["canal_preferido"] == "push"


def test_actualizar_preferencias():
    client.post("/api/v1/notificaciones/preferencias/1", json={
        "canal_preferido": "push", "activo": True,
        "alertas_criticas": True, "alertas_altas": True,
        "alertas_medias": False, "alertas_bajas": False
    })
    respuesta = client.post("/api/v1/notificaciones/preferencias/1", json={
        "canal_preferido": "email", "activo": True,
        "alertas_criticas": True, "alertas_altas": True,
        "alertas_medias": True, "alertas_bajas": False
    })
    assert respuesta.status_code == 200
    assert respuesta.json()["canal_preferido"] == "email"