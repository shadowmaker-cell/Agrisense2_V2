import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.device import TipoDispositivo

# ── Base de datos en memoria para tests ───────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

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
    """Crea las tablas y datos base antes de cada test."""
    Base.metadata.create_all(bind=engine_test)
    db = SesionTest()
    tipo = TipoDispositivo(
        nombre="Sensor de Prueba",
        categoria="suelo",
        unidad="%",
        rango_minimo=0,
        rango_maximo=100,
        umbral_alerta="> 80%",
        tipo_pin="Analógico A0",
        metricas_permitidas=["humedad_prueba"]
    )
    db.add(tipo)
    db.commit()
    db.close()


def teardown_function():
    """Borra las tablas después de cada test."""
    Base.metadata.drop_all(bind=engine_test)


# ── Tests de tipos de sensor ───────────────────────────
def test_listar_tipos():
    respuesta = client.get("/api/v1/dispositivos/tipos")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert len(datos) >= 1
    assert datos[0]["nombre"] == "Sensor de Prueba"


def test_obtener_tipo_existente():
    respuesta = client.get("/api/v1/dispositivos/tipos/1")
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Sensor de Prueba"


def test_obtener_tipo_inexistente():
    respuesta = client.get("/api/v1/dispositivos/tipos/999")
    assert respuesta.status_code == 404


# ── Tests de registro de dispositivos ─────────────────
def test_registrar_dispositivo():
    payload = {
        "tipo_dispositivo_id": 1,
        "id_logico": "TEST_HUM_01",
        "numero_serial": "SN-TEST-001",
        "version_firmware": "1.0.0",
        "estado": "activo"
    }
    respuesta = client.post("/api/v1/dispositivos/", json=payload)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["id_logico"] == "TEST_HUM_01"
    assert datos["numero_serial"] == "SN-TEST-001"
    assert datos["estado"] == "activo"


def test_registrar_dispositivo_serial_duplicado():
    payload = {
        "tipo_dispositivo_id": 1,
        "id_logico": "TEST_HUM_01",
        "numero_serial": "SN-TEST-001",
        "estado": "activo"
    }
    client.post("/api/v1/dispositivos/", json=payload)
    payload["id_logico"] = "TEST_HUM_02"
    respuesta = client.post("/api/v1/dispositivos/", json=payload)
    assert respuesta.status_code == 400
    assert "serial" in respuesta.json()["detail"]


def test_registrar_dispositivo_id_logico_duplicado():
    payload = {
        "tipo_dispositivo_id": 1,
        "id_logico": "TEST_HUM_01",
        "numero_serial": "SN-TEST-001",
        "estado": "activo"
    }
    client.post("/api/v1/dispositivos/", json=payload)
    payload["numero_serial"] = "SN-TEST-002"
    respuesta = client.post("/api/v1/dispositivos/", json=payload)
    assert respuesta.status_code == 400
    assert "lógico" in respuesta.json()["detail"]


def test_registrar_dispositivo_tipo_inexistente():
    payload = {
        "tipo_dispositivo_id": 999,
        "id_logico": "TEST_HUM_99",
        "numero_serial": "SN-TEST-999",
        "estado": "activo"
    }
    respuesta = client.post("/api/v1/dispositivos/", json=payload)
    assert respuesta.status_code == 404


# ── Tests de consulta ──────────────────────────────────
def test_listar_dispositivos():
    respuesta = client.get("/api/v1/dispositivos/")
    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)


def test_obtener_dispositivo_existente():
    payload = {
        "tipo_dispositivo_id": 1,
        "id_logico": "TEST_HUM_01",
        "numero_serial": "SN-TEST-001",
        "estado": "activo"
    }
    creado = client.post("/api/v1/dispositivos/", json=payload).json()
    respuesta = client.get(f"/api/v1/dispositivos/{creado['id']}")
    assert respuesta.status_code == 200
    assert respuesta.json()["id_logico"] == "TEST_HUM_01"


def test_obtener_dispositivo_inexistente():
    respuesta = client.get("/api/v1/dispositivos/999")
    assert respuesta.status_code == 404


# ── Tests de actualización ─────────────────────────────
def test_actualizar_estado_dispositivo():
    payload = {
        "tipo_dispositivo_id": 1,
        "id_logico": "TEST_HUM_01",
        "numero_serial": "SN-TEST-001",
        "estado": "activo"
    }
    creado = client.post("/api/v1/dispositivos/", json=payload).json()
    respuesta = client.put(
        f"/api/v1/dispositivos/{creado['id']}",
        json={"estado": "mantenimiento"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "mantenimiento"


def test_no_puede_modificar_serial():
    payload = {
        "tipo_dispositivo_id": 1,
        "id_logico": "TEST_HUM_01",
        "numero_serial": "SN-TEST-001",
        "estado": "activo"
    }
    creado = client.post("/api/v1/dispositivos/", json=payload).json()
    respuesta = client.put(
        f"/api/v1/dispositivos/{creado['id']}",
        json={"numero_serial": "SN-HACK-999"}
    )
    assert respuesta.status_code == 422


# ── Tests de métricas ──────────────────────────────────
def test_obtener_metricas_dispositivo():
    payload = {
        "tipo_dispositivo_id": 1,
        "id_logico": "TEST_HUM_01",
        "numero_serial": "SN-TEST-001",
        "estado": "activo"
    }
    creado = client.post("/api/v1/dispositivos/", json=payload).json()
    respuesta = client.get(f"/api/v1/dispositivos/{creado['id']}/metricas")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "metricas_permitidas" in datos
    assert "humedad_prueba" in datos["metricas_permitidas"]


# ── Test health check ──────────────────────────────────
def test_health_check():
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"