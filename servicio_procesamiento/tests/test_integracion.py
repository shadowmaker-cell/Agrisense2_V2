"""
Pruebas de Integracion — servicio_procesamiento
================================================
6 pruebas de integracion con:
- 2+ mocks por prueba (JWT, httpx limites externos)
- Cliente HTTP real contra endpoints FastAPI con BD SQLite en memoria
"""
import pytest
from unittest.mock import MagicMock, patch


# ════════════════════════════════════════════════════
# PRUEBA INT-1 — Health check del servicio
# Mocks: get_db override (via fixture client), mock_http
# ════════════════════════════════════════════════════
class TestHealthCheck:
    def test_health_retorna_ok(self, client, mock_http_vacio, mock_jwt_anonimo):
        """Verifica que el endpoint /health responde correctamente."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "ok"
        assert "servicio" in data
        assert isinstance(data["servicio"], str)


# ════════════════════════════════════════════════════
# PRUEBA INT-2 — Procesar lectura manual sin alerta
# Mocks: JWT anonimo, httpx sin limites personalizados
# ════════════════════════════════════════════════════
class TestProcesarManualSinAlerta:
    def test_lectura_normal_no_genera_alerta(self, client, mock_jwt_anonimo, mock_http_vacio):
        """Verifica que una lectura en rango normal se procesa sin alertas."""
        payload = {
            "dispositivo_id": 1,
            "id_logico":      "AIR_TEMP_01",
            "tipo_metrica":   "temperatura_aire",
            "valor_metrica":  22.0,
            "unidad":         "C",
        }

        response = client.post("/api/v1/procesamiento/manual", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["alertas_generadas"] == 0
        assert "evento_id" in data
        assert isinstance(data["tipos_alerta"], list)
        assert data["tipos_alerta"] == []


# ════════════════════════════════════════════════════
# PRUEBA INT-3 — Procesar lectura con alerta critica
# Mocks: JWT con usuario, httpx sin limites externos
# ════════════════════════════════════════════════════
class TestProcesarManualConAlerta:
    def test_sequia_critica_genera_alerta(self, client, mock_jwt_usuario, mock_http_vacio):
        """Verifica que humedad < 10% genera alerta critica persistida en BD."""
        payload = {
            "dispositivo_id": 1,
            "id_logico":      "SOIL_HUM_01",
            "tipo_metrica":   "humedad_suelo",
            "valor_metrica":  5.0,
            "unidad":         "%",
        }

        response = client.post("/api/v1/procesamiento/manual", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["alertas_generadas"] >= 1
        assert "sequia" in data["tipos_alerta"]
        assert "evento_id" in data
        assert data["evento_id"] is not None


# ════════════════════════════════════════════════════
# PRUEBA INT-4 — Listar eventos tras procesamiento
# Mocks: JWT usuario autenticado, httpx vacio
# ════════════════════════════════════════════════════
class TestListarEventos:
    def test_listar_eventos_despues_de_procesar(self, client, mock_jwt_usuario, mock_http_vacio):
        """Verifica que eventos procesados aparecen en el listado."""
        # Crear evento primero
        client.post("/api/v1/procesamiento/manual", json={
            "dispositivo_id": 2,
            "id_logico":      "SOIL_HUM_02",
            "tipo_metrica":   "humedad_suelo",
            "valor_metrica":  50.0,
            "unidad":         "%",
        })

        response = client.get("/api/v1/procesamiento/eventos")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id_logico"] == "SOIL_HUM_02"
        assert data[0]["tipo_metrica"] == "humedad_suelo"

    def test_listar_eventos_usuario_anonimo_retorna_lista(self, client, mock_jwt_anonimo, mock_http_vacio):
        """Verifica que usuario anonimo obtiene lista vacia o con sus eventos."""
        response = client.get("/api/v1/procesamiento/eventos")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ════════════════════════════════════════════════════
# PRUEBA INT-5 — Listar alertas generadas
# Mocks: JWT usuario, httpx vacio
# ════════════════════════════════════════════════════
class TestListarAlertas:
    def test_alertas_generadas_aparecen_en_listado(self, client, mock_jwt_usuario, mock_http_vacio):
        """Verifica que alertas criticas quedan registradas y se pueden listar."""
        # Crear alerta con valor critico
        client.post("/api/v1/procesamiento/manual", json={
            "dispositivo_id": 3,
            "id_logico":      "SOIL_HUM_03",
            "tipo_metrica":   "humedad_suelo",
            "valor_metrica":  5.0,
            "unidad":         "%",
        })

        response = client.get("/api/v1/procesamiento/alertas")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(a["id_logico"] == "SOIL_HUM_03" for a in data)

    def test_alertas_filtradas_por_tipo(self, client, mock_jwt_usuario, mock_http_vacio):
        """Verifica el filtro de alertas por tipo de alerta."""
        client.post("/api/v1/procesamiento/manual", json={
            "dispositivo_id": 4,
            "id_logico":      "SOIL_HUM_04",
            "tipo_metrica":   "humedad_suelo",
            "valor_metrica":  5.0,
            "unidad":         "%",
        })

        response = client.get("/api/v1/procesamiento/alertas?tipo_alerta=sequia")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for alerta in data:
            assert alerta["tipo_alerta"] == "sequia"


# ════════════════════════════════════════════════════
# PRUEBA INT-6 — Resumen de procesamiento
# Mocks: JWT usuario, httpx vacio
# ════════════════════════════════════════════════════
class TestResumenProcesamiento:
    def test_resumen_estructura_correcta(self, client, mock_jwt_usuario, mock_http_vacio):
        """Verifica que el resumen incluye todos los campos esperados."""
        response = client.get("/api/v1/procesamiento/resumen")

        assert response.status_code == 200
        data = response.json()
        assert "total_eventos" in data
        assert "total_alertas" in data
        assert "alertas_criticas" in data
        assert "alertas_altas" in data
        assert "alertas_medias" in data
        assert isinstance(data["total_eventos"], int)
        assert isinstance(data["total_alertas"], int)

    def test_resumen_conteos_reflejan_eventos_creados(self, client, mock_jwt_usuario, mock_http_vacio):
        """Verifica que el resumen cuenta correctamente los eventos creados."""
        # Crear 1 evento critico y 1 normal
        client.post("/api/v1/procesamiento/manual", json={
            "dispositivo_id": 5, "id_logico": "SOIL_HUM_05",
            "tipo_metrica": "humedad_suelo", "valor_metrica": 5.0, "unidad": "%"
        })
        client.post("/api/v1/procesamiento/manual", json={
            "dispositivo_id": 6, "id_logico": "AIR_TEMP_02",
            "tipo_metrica": "temperatura_aire", "valor_metrica": 22.0, "unidad": "C"
        })

        response = client.get("/api/v1/procesamiento/resumen")
        data = response.json()

        assert data["total_eventos"] >= 2
        assert data["total_alertas"] >= 1
        assert data["alertas_criticas"] >= 1
        
        # ════════════════════════════════════════════════════
# PRUEBA INT-7 — Eventos por dispositivo retorna 404
# Mocks: JWT usuario, httpx vacio
# ════════════════════════════════════════════════════
class TestEventosPorDispositivo:
    def test_eventos_dispositivo_inexistente_retorna_404(
        self, client, mock_jwt_usuario, mock_http_vacio
    ):
        """Verifica que buscar eventos de sensor sin datos retorna 404."""
        response = client.get("/api/v1/procesamiento/eventos/SENSOR_INEXISTENTE_XYZ")
        assert response.status_code == 404

    def test_alertas_dispositivo_inexistente_retorna_404(
        self, client, mock_jwt_usuario, mock_http_vacio
    ):
        """Verifica que buscar alertas de sensor sin datos retorna 404."""
        response = client.get("/api/v1/procesamiento/alertas/SENSOR_INEXISTENTE_XYZ")
        assert response.status_code == 404

    def test_eventos_dispositivo_con_datos(
        self, client, mock_jwt_usuario, mock_http_vacio
    ):
        """Verifica que eventos por dispositivo retorna datos correctos."""
        client.post("/api/v1/procesamiento/manual", json={
            "dispositivo_id": 7,
            "id_logico":      "WIND_SENSOR_01",
            "tipo_metrica":   "velocidad_viento",
            "valor_metrica":  10.0,
            "unidad":         "km/h",
        })

        response = client.get("/api/v1/procesamiento/eventos/WIND_SENSOR_01")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id_logico"] == "WIND_SENSOR_01"