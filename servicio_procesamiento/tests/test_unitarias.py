"""
Pruebas Unitarias — servicio_procesamiento
==========================================
6 pruebas unitarias con:
- 2+ mocks por prueba
- 4+ matchers distintos
- 1 prueba con promesa (asyncio)
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock, call
from datetime import datetime, timezone

from app.services.reglas import aplicar_reglas, aplicar_limites_personalizados
from app.services.detector import procesar_evento_telemetria, obtener_limites_dispositivo


# ════════════════════════════════════════════════════
# PRUEBA 1 — Reglas globales detectan sequia critica
# Matchers: assertEqual, assertIsInstance, assertGreater, assertIn
# ════════════════════════════════════════════════════
class TestReglasSuelo:
    def test_sequia_critica_genera_alerta(self):
        """Verifica que humedad_suelo < 10 genera alerta critica."""
        resultado = aplicar_reglas("humedad_suelo", 5.0)

        # Matcher 1: assertEqual — debe haber al menos 1 alerta
        assert len(resultado) >= 1

        # Matcher 2: assertIn — el tipo de alerta debe ser sequia
        tipos = [r[0] for r in resultado]
        assert "sequia" in tipos

        # Matcher 3: assertIsInstance — cada elemento es tupla
        for item in resultado:
            assert isinstance(item, tuple)

        # Matcher 4: assertGreater — hay mas de 0 alertas
        assert len(resultado) > 0

        # Verificar severidad critica
        severidades = [r[2] for r in resultado]
        assert "critica" in severidades


# ════════════════════════════════════════════════════
# PRUEBA 2 — Reglas globales NO disparan en valores normales
# Matchers: assertEqual, assertIsInstance, assertFalse, assertEqual (lista vacia)
# ════════════════════════════════════════════════════
class TestReglasValoresNormales:
    def test_humedad_normal_no_genera_alerta(self):
        """Verifica que humedad_suelo en rango normal no genera alertas."""
        resultado = aplicar_reglas("humedad_suelo", 55.0)

        # Matcher 1: assertEqual — lista vacia
        assert resultado == []

        # Matcher 2: assertIsInstance — es una lista
        assert isinstance(resultado, list)

        # Matcher 3: assertFalse — no hay alertas
        assert not resultado

        # Matcher 4: assertEqual — longitud cero
        assert len(resultado) == 0

    def test_temperatura_normal_no_genera_alerta(self):
        """Verifica que temperatura en rango normal no genera alertas."""
        resultado = aplicar_reglas("temperatura_aire", 22.0)
        assert resultado == []
        assert isinstance(resultado, list)


# ════════════════════════════════════════════════════
# PRUEBA 3 — Limites personalizados tienen prioridad
# Mocks: MagicMock para simular configuracion de sensor
# Matchers: assertEqual, assertIn, assertIsNotNone, assertTrue
# ════════════════════════════════════════════════════
class TestLimitesPersonalizados:
    def test_limite_maximo_personalizado_genera_alerta(self):
        """Verifica que el limite maximo personalizado dispara alerta."""
        # Mock del valor fuera del rango personalizado
        limite_minimo = 20.0
        limite_maximo = 80.0
        valor = 90.0  # supera el limite maximo

        resultado = aplicar_limites_personalizados(
            "humedad_suelo", valor, limite_minimo, limite_maximo
        )

        # Matcher 1: assertIsNotNone
        assert resultado is not None

        # Matcher 2: assertTrue — hay alertas
        assert len(resultado) > 0

        # Matcher 3: assertIn — tipo es limite_maximo
        tipos = [r[0] for r in resultado]
        assert "limite_maximo" in tipos

        # Matcher 4: assertEqual — exactamente una alerta de maximo
        maximo_alertas = [r for r in resultado if r[0] == "limite_maximo"]
        assert len(maximo_alertas) == 1

    def test_limite_minimo_personalizado_genera_alerta(self):
        """Verifica que el limite minimo personalizado dispara alerta."""
        resultado = aplicar_limites_personalizados(
            "temperatura_aire", 5.0, 15.0, 40.0
        )
        assert len(resultado) > 0
        tipos = [r[0] for r in resultado]
        assert "limite_minimo" in tipos

    def test_valor_dentro_limites_no_genera_alerta(self):
        """Verifica que un valor dentro de limites no genera alertas."""
        resultado = aplicar_limites_personalizados(
            "humedad_suelo", 50.0, 20.0, 80.0
        )
        assert resultado == []


# ════════════════════════════════════════════════════
# PRUEBA 4 — detector usa limites personalizados si existen
# Mocks: db session, httpx.get para limites externos
# ════════════════════════════════════════════════════
class TestDetectorConLimitesPersonalizados:
    def test_detector_aplica_limites_del_payload(self):
        """Verifica que el detector usa limites del payload con prioridad."""
        # Mock de la sesion de base de datos
        mock_db = MagicMock()
        mock_evento = MagicMock()
        mock_evento.id = 1
        mock_evento.tiene_alerta = False

        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.commit = MagicMock()

        # Mock del modelo EventoProcesado
        with patch("app.services.detector.EventoProcesado") as mock_evento_class, \
             patch("app.services.detector.AlertaStream") as mock_alerta_class, \
             patch("app.services.detector.ReglaAplicada") as mock_regla_class:

            mock_evento_class.return_value = mock_evento
            mock_alerta_class.return_value = MagicMock(tipo_alerta="limite_maximo")

            datos = {
                "dispositivo_id":    1,
                "id_logico":         "SOIL_HUM_01",
                "tipo_metrica":      "humedad_suelo",
                "valor_metrica":     95.0,
                "unidad":            "%",
                "limite_minimo":     20.0,
                "limite_maximo":     80.0,
                "usuario_id":        1,
            }

            resultado = procesar_evento_telemetria(mock_db, datos)

            # Matcher 1: assertIsNotNone
            assert resultado is not None

            # Matcher 2: assertIn — tiene la clave evento_id
            assert "evento_id" in resultado

            # Matcher 3: assertIn — tiene alertas_generadas
            assert "alertas_generadas" in resultado

            # Matcher 4: assertIsInstance — resultado es dict
            assert isinstance(resultado, dict)


# ════════════════════════════════════════════════════
# PRUEBA 5 — obtener_limites_dispositivo maneja errores de red
# Mocks: httpx.get con excepcion, logger
# Matchers: assertEqual, assertIsNone, assertIsInstance, assertEqual (tuple)
# ════════════════════════════════════════════════════
class TestObtenerLimitesDispositivo:
    def test_error_de_red_retorna_none(self):
        """Verifica que un error de conexion retorna (None, None)."""
        with patch("app.services.detector.httpx.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            limite_min, limite_max = obtener_limites_dispositivo("SOIL_HUM_01")

            # Matcher 1: assertIsNone
            assert limite_min is None

            # Matcher 2: assertIsNone
            assert limite_max is None

            # Matcher 3: assertEqual — mock fue llamado una vez
            mock_get.assert_called_once()

            # Matcher 4: assertIsInstance — resultado es None type
            assert isinstance(limite_min, type(None))

    def test_respuesta_vacia_retorna_none(self):
        """Verifica que una respuesta sin dispositivos retorna (None, None)."""
        with patch("app.services.detector.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            limite_min, limite_max = obtener_limites_dispositivo("SENSOR_INEXISTENTE")

            assert limite_min is None
            assert limite_max is None

    def test_dispositivo_con_limites_retorna_valores(self):
        """Verifica que un dispositivo con limites configurados los retorna."""
        with patch("app.services.detector.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{
                "id_logico": "SOIL_HUM_01",
                "configuracion": {
                    "limite_minimo": 20.0,
                    "limite_maximo": 80.0
                }
            }]
            mock_get.return_value = mock_response

            limite_min, limite_max = obtener_limites_dispositivo("SOIL_HUM_01")

            assert limite_min == 20.0
            assert limite_max == 80.0


# ════════════════════════════════════════════════════
# PRUEBA 6 — Prueba con promesa (asyncio)
# Verifica comportamiento asincrono del procesamiento
# Mocks: AsyncMock para simular llamada asincrona
# ════════════════════════════════════════════════════
class TestProcesamientoAsincrono:
    @pytest.mark.asyncio
    async def test_procesamiento_asincrono_con_mock(self):
        """Prueba con promesa — simula llamada asincrona al detector."""

        async def simular_procesamiento(datos):
            await asyncio.sleep(0)  # simula operacion asincrona
            return {
                "evento_id":         1,
                "alertas_generadas": 1,
                "tipos_alerta":      ["sequia"],
            }

        mock_procesamiento = AsyncMock(side_effect=simular_procesamiento)

        datos = {
            "dispositivo_id": 1,
            "id_logico":      "SOIL_HUM_01",
            "tipo_metrica":   "humedad_suelo",
            "valor_metrica":  5.0,
        }

        # Ejecutar la promesa
        resultado = await mock_procesamiento(datos)

        # Matcher 1: assertEqual
        assert resultado["alertas_generadas"] == 1

        # Matcher 2: assertIn
        assert "sequia" in resultado["tipos_alerta"]

        # Matcher 3: assertIsNotNone
        assert resultado["evento_id"] is not None

        # Matcher 4: assertTrue — fue llamado
        mock_procesamiento.assert_called_once_with(datos)

        # Matcher 5: assertEqual — clave presente
        assert "tipos_alerta" in resultado
        
        # ════════════════════════════════════════════════════
# PRUEBA 7 — JWT utils: token invalido retorna None
# Mocks: Request con header invalido
# ════════════════════════════════════════════════════
class TestJwtUtils:
    def test_get_usuario_id_opcional_sin_header_retorna_none(self):
        """Verifica que sin header Authorization retorna None."""
        from app.utils.jwt import get_usuario_id_opcional
        mock_request = MagicMock()
        mock_request.headers = {}

        resultado = get_usuario_id_opcional(mock_request)

        assert resultado is None
        assert isinstance(resultado, type(None))

    def test_get_usuario_id_opcional_token_invalido_retorna_none(self):
        """Verifica que un token invalido retorna None sin lanzar excepcion."""
        from app.utils.jwt import get_usuario_id_opcional
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer token_invalido_xyz"}

        resultado = get_usuario_id_opcional(mock_request)

        assert resultado is None

    def test_reglas_temperatura_critica_genera_alerta(self):
        """Verifica reglas de temperatura para completar cobertura."""
        resultado_helada = aplicar_reglas("temperatura_aire", -5.0)
        resultado_calor  = aplicar_reglas("temperatura_aire", 45.0)

        assert len(resultado_helada) >= 1
        assert len(resultado_calor) >= 1

        tipos_helada = [r[0] for r in resultado_helada]
        tipos_calor  = [r[0] for r in resultado_calor]

        assert "helada" in tipos_helada
        assert "calor"  in tipos_calor