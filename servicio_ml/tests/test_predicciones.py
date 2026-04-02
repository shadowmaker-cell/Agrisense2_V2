import os
os.environ["DATABASE_URL"] = "sqlite:///./test_ml.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.services.prediccion_service import inicializar_modelos

SQLALCHEMY_TEST_URL = "sqlite:///./test_ml.db"

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


def setup_function():
    Base.metadata.create_all(bind=engine_test)
    db = SesionTest()
    inicializar_modelos(db)
    db.close()


def teardown_function():
    Base.metadata.drop_all(bind=engine_test)


client = TestClient(app)


# ── Health ────────────────────────────────────────────
def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["estado"] == "ok"
    assert res.json()["servicio"] == "ml-prediction-service"


def test_health_router():
    res = client.get("/api/v1/ml/health")
    assert res.status_code == 200
    assert "modelos" in res.json()


# ── Modelos ───────────────────────────────────────────
def test_listar_modelos():
    res = client.get("/api/v1/ml/modelos")
    assert res.status_code == 200
    assert len(res.json()) == 3
    tipos = [m["tipo"] for m in res.json()]
    assert "agua"        in tipos
    assert "rendimiento" in tipos
    assert "riesgo"      in tipos


def test_obtener_modelo_existente():
    res = client.get("/api/v1/ml/modelos/1")
    assert res.status_code == 200
    assert res.json()["id"] == 1


def test_obtener_modelo_inexistente():
    res = client.get("/api/v1/ml/modelos/9999")
    assert res.status_code == 404


# ── Prediccion de agua ────────────────────────────────
def test_prediccion_agua_normal():
    res = client.post("/api/v1/ml/predicciones/agua", json={
        "humedad_suelo":    45.0,
        "temperatura_aire": 28.0,
        "lluvia":           5.0,
        "area_hectareas":   10.0,
        "tipo_cultivo":     "maiz",
    })
    assert res.status_code == 201
    data = res.json()
    assert "litros_recomendados" in data
    assert "frecuencia_horas"    in data
    assert "urgencia"            in data
    assert "confianza"           in data
    assert "solicitud_id"        in data
    assert data["litros_recomendados"] >= 0


def test_prediccion_agua_suelo_seco():
    res = client.post("/api/v1/ml/predicciones/agua", json={
        "humedad_suelo":    10.0,
        "temperatura_aire": 35.0,
        "lluvia":           0.0,
        "area_hectareas":   5.0,
        "tipo_cultivo":     "cafe",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["urgencia"] in ["critica", "alta"]
    assert data["litros_recomendados"] > 0


def test_prediccion_agua_suelo_humedo():
    res = client.post("/api/v1/ml/predicciones/agua", json={
        "humedad_suelo":    80.0,
        "temperatura_aire": 22.0,
        "lluvia":           40.0,
        "area_hectareas":   3.0,
        "tipo_cultivo":     "arroz",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["urgencia"] in ["baja", "media"]


def test_prediccion_agua_parcela_id():
    res = client.post("/api/v1/ml/predicciones/agua", json={
        "parcela_id":       1,
        "id_logico":        "SOIL_HUM_01",
        "humedad_suelo":    55.0,
        "temperatura_aire": 26.0,
        "lluvia":           10.0,
        "area_hectareas":   8.0,
        "tipo_cultivo":     "platano",
    })
    assert res.status_code == 201
    assert res.json()["solicitud_id"] > 0


# ── Prediccion de rendimiento ─────────────────────────
def test_prediccion_rendimiento_normal():
    res = client.post("/api/v1/ml/predicciones/rendimiento", json={
        "area_hectareas":   15.0,
        "tipo_cultivo":     "maiz",
        "humedad_suelo":    65.0,
        "temperatura_aire": 25.0,
        "ph_suelo":         6.5,
        "lluvia_acumulada": 50.0,
        "etapa_fenologica": "vegetativo",
    })
    assert res.status_code == 201
    data = res.json()
    assert "rendimiento_kg_ha"    in data
    assert "rendimiento_total_kg" in data
    assert "calificacion"         in data
    assert "factores_riesgo"      in data
    assert "recomendaciones"      in data
    assert data["rendimiento_kg_ha"] >= 0
    assert data["calificacion"] in ["excelente", "bueno", "regular", "bajo"]


def test_prediccion_rendimiento_condiciones_malas():
    res = client.post("/api/v1/ml/predicciones/rendimiento", json={
        "area_hectareas":   5.0,
        "tipo_cultivo":     "papa",
        "humedad_suelo":    15.0,
        "temperatura_aire": 40.0,
        "ph_suelo":         4.5,
        "lluvia_acumulada": 0.0,
    })
    assert res.status_code == 201
    data = res.json()
    assert len(data["factores_riesgo"]) > 0
    assert len(data["recomendaciones"]) > 0


def test_prediccion_rendimiento_total():
    res = client.post("/api/v1/ml/predicciones/rendimiento", json={
        "area_hectareas":   20.0,
        "tipo_cultivo":     "cana",
        "humedad_suelo":    70.0,
        "temperatura_aire": 28.0,
        "ph_suelo":         6.8,
        "lluvia_acumulada": 80.0,
    })
    assert res.status_code == 201
    data = res.json()
    assert data["rendimiento_total_kg"] > 0
    assert data["rendimiento_kg_ha"] > 0

# ── Prediccion de riesgo ──────────────────────────────
def test_prediccion_riesgo_helada():
    res = client.post("/api/v1/ml/predicciones/riesgo", json={
        "temperatura_aire": -3.0,
        "humedad_aire":     90.0,
        "humedad_suelo":    40.0,
        "velocidad_viento": 15.0,
        "lluvia":           0.0,
        "tipo_riesgo":      "helada",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["tipo_riesgo"] == "helada"
    assert data["nivel"] in ["bajo", "medio", "alto", "critico"]
    assert len(data["acciones"]) > 0
    assert 0 <= data["probabilidad"] <= 1


def test_prediccion_riesgo_sequia():
    res = client.post("/api/v1/ml/predicciones/riesgo", json={
        "temperatura_aire": 38.0,
        "humedad_aire":     20.0,
        "humedad_suelo":    10.0,
        "velocidad_viento": 5.0,
        "lluvia":           0.0,
        "tipo_riesgo":      "sequia",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["tipo_riesgo"] == "sequia"
    assert data["nivel"] in ["bajo", "medio", "alto", "critico"]
    assert len(data["acciones"]) > 0

def test_prediccion_riesgo_hongo():
    res = client.post("/api/v1/ml/predicciones/riesgo", json={
        "temperatura_aire": 22.0,
        "humedad_aire":     95.0,
        "humedad_suelo":    85.0,
        "velocidad_viento": 2.0,
        "lluvia":           30.0,
        "tipo_riesgo":      "hongo",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["tipo_riesgo"] == "hongo"


def test_prediccion_riesgo_inundacion():
    res = client.post("/api/v1/ml/predicciones/riesgo", json={
        "temperatura_aire": 25.0,
        "humedad_aire":     85.0,
        "humedad_suelo":    90.0,
        "velocidad_viento": 10.0,
        "lluvia":           80.0,
        "tipo_riesgo":      "inundacion",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["tipo_riesgo"] == "inundacion"


def test_prediccion_riesgo_tipo_invalido():
    res = client.post("/api/v1/ml/predicciones/riesgo", json={
        "temperatura_aire": 25.0,
        "humedad_aire":     60.0,
        "humedad_suelo":    50.0,
        "velocidad_viento": 10.0,
        "lluvia":           5.0,
        "tipo_riesgo":      "volcan",
    })
    assert res.status_code == 422


# ── Historial ─────────────────────────────────────────
def test_listar_predicciones_vacias():
    res = client.get("/api/v1/ml/predicciones")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_listar_predicciones_con_datos():
    client.post("/api/v1/ml/predicciones/agua", json={
        "humedad_suelo": 50.0, "temperatura_aire": 25.0,
        "lluvia": 0.0, "area_hectareas": 5.0,
    })
    res = client.get("/api/v1/ml/predicciones")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_listar_predicciones_filtro_tipo():
    client.post("/api/v1/ml/predicciones/agua", json={
        "humedad_suelo": 50.0, "temperatura_aire": 25.0,
        "lluvia": 0.0, "area_hectareas": 5.0,
    })
    res = client.get("/api/v1/ml/predicciones?tipo=agua")
    assert res.status_code == 200
    for p in res.json():
        assert p["tipo_prediccion"] == "agua"


def test_obtener_resultado():
    pred = client.post("/api/v1/ml/predicciones/agua", json={
        "humedad_suelo": 40.0, "temperatura_aire": 30.0,
        "lluvia": 0.0, "area_hectareas": 2.0,
    }).json()
    sid = pred["solicitud_id"]
    res = client.get(f"/api/v1/ml/predicciones/{sid}/resultado")
    assert res.status_code == 200
    assert res.json()["solicitud_id"] == sid
    assert res.json()["valor_predicho"] >= 0


# ── Resumen ───────────────────────────────────────────
def test_resumen_ml():
    res = client.get("/api/v1/ml/resumen")
    assert res.status_code == 200
    data = res.json()
    assert "total_predicciones"       in data
    assert "predicciones_agua"        in data
    assert "predicciones_riesgo"      in data
    assert "predicciones_rendimiento" in data
    assert "modelos_activos"          in data