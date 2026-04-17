import logging
import httpx
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.evento import EventoProcesado, AlertaStream, ReglaAplicada
from app.services.reglas import aplicar_reglas, aplicar_limites_personalizados

logger = logging.getLogger(__name__)

DEVICE_SERVICE_URL = os.getenv("DEVICE_SERVICE_URL", "http://servicio-dispositivos:8001")


def obtener_limites_dispositivo(id_logico: str) -> tuple:
    """Obtiene los límites personalizados del sensor desde el servicio de dispositivos."""
    try:
        res = httpx.get(
            f"{DEVICE_SERVICE_URL}/api/v1/dispositivos/",
            timeout=3.0
        )
        if res.status_code == 200:
            dispositivos = res.json()
            disp = next((d for d in dispositivos if d.get("id_logico") == id_logico), None)
            if disp and disp.get("configuracion"):
                config = disp["configuracion"]
                return config.get("limite_minimo"), config.get("limite_maximo")
    except Exception as e:
        logger.debug(f"No se pudieron obtener límites para {id_logico}: {e}")
    return None, None


def procesar_evento_telemetria(db: Session, datos: dict) -> dict:
    dispositivo_id    = datos.get("dispositivo_id")
    id_logico         = datos.get("id_logico")
    tipo_metrica      = datos.get("tipo_metrica")
    valor_metrica     = datos.get("valor_metrica")
    unidad            = datos.get("unidad")
    timestamp_lectura = datos.get("timestamp_lectura")
    usuario_id        = datos.get("usuario_id")
    limite_minimo     = datos.get("limite_minimo")
    limite_maximo     = datos.get("limite_maximo")

    try:
        ts = datetime.fromisoformat(timestamp_lectura) if timestamp_lectura else datetime.now(timezone.utc)
    except Exception:
        ts = datetime.now(timezone.utc)

    evento = EventoProcesado(
        usuario_id=usuario_id,
        dispositivo_id=dispositivo_id,
        id_logico=id_logico,
        tipo_metrica=tipo_metrica,
        valor_metrica=valor_metrica,
        unidad=unidad,
        timestamp_lectura=ts,
        tiene_alerta=False,
    )
    db.add(evento)
    db.flush()

    # Si no vienen límites en el payload los buscamos en dispositivos
    if limite_minimo is None and limite_maximo is None and id_logico:
        limite_minimo, limite_maximo = obtener_limites_dispositivo(id_logico)

    # Límites personalizados tienen prioridad
    alertas_detectadas = []
    if limite_minimo is not None or limite_maximo is not None:
        alertas_detectadas = aplicar_limites_personalizados(
            tipo_metrica, valor_metrica, limite_minimo, limite_maximo
        )

    # Si no hay límites personalizados o no generaron alertas usar reglas globales
    if not alertas_detectadas:
        alertas_detectadas = aplicar_reglas(tipo_metrica, valor_metrica)

    alertas_generadas = []
    for tipo_alerta, condicion, severidad, nombre_regla in alertas_detectadas:
        alerta = AlertaStream(
            usuario_id=usuario_id,
            dispositivo_id=dispositivo_id,
            id_logico=id_logico,
            tipo_metrica=tipo_metrica,
            valor_detectado=valor_metrica,
            condicion=condicion,
            severidad=severidad,
            tipo_alerta=tipo_alerta,
            evento_id=evento.id,
        )
        db.add(alerta)
        db.flush()
        alertas_generadas.append(alerta)

        regla = ReglaAplicada(
            nombre_regla=nombre_regla,
            dispositivo_id=dispositivo_id,
            id_logico=id_logico,
            tipo_metrica=tipo_metrica,
            valor=valor_metrica,
            resultado="disparada",
            detalle=condicion,
        )
        db.add(regla)
        logger.warning(
            f"ALERTA [{severidad.upper()}] {id_logico} — "
            f"{tipo_metrica}: {valor_metrica} — {condicion}"
        )

    if alertas_generadas:
        evento.tiene_alerta = True

    db.commit()
    return {
        "evento_id":         evento.id,
        "alertas_generadas": len(alertas_generadas),
        "tipos_alerta":      [a.tipo_alerta for a in alertas_generadas],
    }