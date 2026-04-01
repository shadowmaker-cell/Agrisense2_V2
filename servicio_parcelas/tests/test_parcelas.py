import os
os.environ["DATABASE_URL"] = "sqlite:///./test_parcelas.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_parcelas.db"

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


# ── Health ─────────────────────────────────────────────
def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["estado"] == "ok"
    assert res.json()["servicio"] == "parcel-management"


# ── Tipos de cultivo ───────────────────────────────────
def test_crear_tipo_cultivo():
    res = client.post("/api/v1/parcelas/tipos-cultivo", json={
        "nombre": "Maiz", "descripcion": "Cultivo de maiz", "temporada": "todo_anio"
    })
    assert res.status_code == 201
    assert res.json()["nombre"] == "Maiz"


def test_listar_tipos_cultivo():
    client.post("/api/v1/parcelas/tipos-cultivo", json={"nombre": "Cafe"})
    res = client.get("/api/v1/parcelas/tipos-cultivo")
    assert res.status_code == 200
    assert len(res.json()) >= 1


# ── Parcelas CRUD ──────────────────────────────────────
def test_crear_parcela():
    res = client.post("/api/v1/parcelas/", json={
        "nombre":         "Parcela Norte",
        "area_hectareas": 5.5,
        "tipo_suelo":     "arcilloso",
        "latitud":        8.7534,
        "longitud":       -75.8811,
        "municipio":      "Monteria",
        "departamento":   "Cordoba",
        "estado":         "activa"
    })
    assert res.status_code == 201
    assert res.json()["nombre"] == "Parcela Norte"
    assert res.json()["area_hectareas"] == 5.5


def test_listar_parcelas():
    client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Sur", "area_hectareas": 3.0, "estado": "activa"
    })
    res = client.get("/api/v1/parcelas/")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_obtener_parcela():
    creada = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Este", "area_hectareas": 2.0, "estado": "activa"
    }).json()
    res = client.get(f"/api/v1/parcelas/{creada['id']}")
    assert res.status_code == 200
    assert res.json()["nombre"] == "Parcela Este"


def test_parcela_inexistente():
    res = client.get("/api/v1/parcelas/9999")
    assert res.status_code == 404


def test_actualizar_parcela():
    creada = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Oeste", "area_hectareas": 1.5, "estado": "activa"
    }).json()
    res = client.put(f"/api/v1/parcelas/{creada['id']}", json={
        "nombre": "Parcela Oeste Actualizada",
        "area_hectareas": 2.0,
        "estado": "activa"
    })
    assert res.status_code == 200
    assert res.json()["nombre"] == "Parcela Oeste Actualizada"


def test_filtrar_parcelas_por_estado():
    client.post("/api/v1/parcelas/", json={
        "nombre": "Inactiva", "area_hectareas": 1.0, "estado": "inactiva"
    })
    res = client.get("/api/v1/parcelas/?estado=inactiva")
    assert res.status_code == 200
    for p in res.json():
        assert p["estado"] == "inactiva"


def test_eliminar_parcela():
    creada = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Eliminar", "area_hectareas": 1.0, "estado": "activa"
    }).json()
    res = client.delete(f"/api/v1/parcelas/{creada['id']}")
    assert res.status_code == 200
    res2 = client.get(f"/api/v1/parcelas/{creada['id']}")
    assert res2.status_code == 404


# ── Sensores de parcela ────────────────────────────────
def test_asignar_sensor():
    parcela = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Sensor", "area_hectareas": 4.0, "estado": "activa"
    }).json()
    res = client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", json={
        "dispositivo_id": 1,
        "id_logico": "SOIL_HUM_01",
        "notas": "Instalado en sector norte"
    })
    assert res.status_code == 201
    assert res.json()["id_logico"] == "SOIL_HUM_01"


def test_asignar_sensor_duplicado():
    parcela = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Dup", "area_hectareas": 2.0, "estado": "activa"
    }).json()
    client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", json={
        "dispositivo_id": 1, "id_logico": "AIR_TEMP_01"
    })
    res = client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", json={
        "dispositivo_id": 1, "id_logico": "AIR_TEMP_01"
    })
    assert res.status_code == 400


def test_listar_sensores_parcela():
    parcela = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Lista", "area_hectareas": 3.0, "estado": "activa"
    }).json()
    client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", json={
        "dispositivo_id": 1, "id_logico": "LUX_01"
    })
    res = client.get(f"/api/v1/parcelas/{parcela['id']}/sensores")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_desasignar_sensor():
    parcela = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Desasignar", "area_hectareas": 2.0, "estado": "activa"
    }).json()
    sensor = client.post(f"/api/v1/parcelas/{parcela['id']}/sensores", json={
        "dispositivo_id": 1, "id_logico": "WIND_01"
    }).json()
    res = client.delete(f"/api/v1/parcelas/{parcela['id']}/sensores/{sensor['id']}")
    assert res.status_code == 200


# ── Historial de cultivos ──────────────────────────────
def test_agregar_historial():
    tipo = client.post("/api/v1/parcelas/tipos-cultivo", json={
        "nombre": "Yuca Test"
    }).json()
    parcela = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Hist", "area_hectareas": 3.0, "estado": "activa"
    }).json()
    res = client.post(f"/api/v1/parcelas/{parcela['id']}/historial", json={
        "tipo_cultivo_id":  tipo["id"],
        "fecha_siembra":    "2026-01-15T00:00:00",
        "etapa_fenologica": "vegetativo",
        "estado":           "activo"
    })
    assert res.status_code == 201
    assert res.json()["estado"] == "activo"


def test_listar_historial():
    tipo = client.post("/api/v1/parcelas/tipos-cultivo", json={
        "nombre": "Maiz Test"
    }).json()
    parcela = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Hist2", "area_hectareas": 2.0, "estado": "activa"
    }).json()
    client.post(f"/api/v1/parcelas/{parcela['id']}/historial", json={
        "tipo_cultivo_id": tipo["id"],
        "fecha_siembra":   "2026-02-01T00:00:00",
        "estado":          "activo"
    })
    res = client.get(f"/api/v1/parcelas/{parcela['id']}/historial")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_actualizar_historial():
    tipo = client.post("/api/v1/parcelas/tipos-cultivo", json={
        "nombre": "Cafe Test"
    }).json()
    parcela = client.post("/api/v1/parcelas/", json={
        "nombre": "Parcela Update", "area_hectareas": 2.0, "estado": "activa"
    }).json()
    hist = client.post(f"/api/v1/parcelas/{parcela['id']}/historial", json={
        "tipo_cultivo_id": tipo["id"],
        "fecha_siembra":   "2026-01-01T00:00:00",
        "estado":          "activo"
    }).json()
    res = client.put(f"/api/v1/parcelas/{parcela['id']}/historial/{hist['id']}", json={
        "tipo_cultivo_id":  tipo["id"],
        "fecha_siembra":    "2026-01-01T00:00:00",
        "fecha_cosecha":    "2026-06-01T00:00:00",
        "etapa_fenologica": "cosecha",
        "rendimiento_kg":   1200.0,
        "estado":           "finalizado"
    })
    assert res.status_code == 200
    assert res.json()["estado"] == "finalizado"
    assert res.json()["rendimiento_kg"] == 1200.0


# ── Resumen ────────────────────────────────────────────
def test_resumen_parcelas():
    client.post("/api/v1/parcelas/", json={
        "nombre": "Resumen Test", "area_hectareas": 5.0, "estado": "activa"
    })
    res = client.get("/api/v1/parcelas/resumen")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1