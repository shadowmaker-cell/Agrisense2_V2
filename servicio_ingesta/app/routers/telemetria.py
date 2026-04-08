from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import httpx
import os

from app.database import get_db
from app.models.lectura import LecturaSensor, LoteIngesta, ErrorIngesta, AlertaGenerada
from app.schemas.lectura import (
    LecturaEntrada, LoteEntrada,
    LecturaRespuesta, LoteRespuesta,
    AlertaRespuesta,
)
from app.services.validador import validar_lectura, detectar_alertas, normalizar_timestamp
from app.services.alertas import procesar_alertas
from app.events.producer import publish_telemetry_raw, publish_alert_generated, publish_batch_completed
from app.utils.jwt import get_usuario_id, get_usuario_id_opcional

router = APIRouter(prefix="/api/v1/telemetria", tags=["telemetria"])

_contadores = {}
LIMITE_POR_MINUTO = 60
DEVICE_SERVICE_URL = os.getenv("DEVICE_SERVICE_URL", "http://localhost:8001")


def verificar_rate_limit(id_logico: str) -> bool:
    ahora = datetime.now(timezone.utc)
    minuto_actual = ahora.strftime("%Y%m%d%H%M")
    clave = f"{id_logico}:{minuto_actual}"
    _contadores[clave] = _contadores.get(clave, 0) + 1
    claves_viejas = [k for k in _contadores if not k.endswith(minuto_actual)]
    for k in claves_viejas:
        del _contadores[k]
    return _contadores[clave] <= LIMITE_POR_MINUTO


def verificar_estado_dispositivo(id_logico: str) -> tuple:
    try:
        url = f"{DEVICE_SERVICE_URL}/api/v1/dispositivos/"
        response = httpx.get(url, timeout=3.0)
        if response.status_code == 200:
            dispositivos = response.json()
            dispositivo = next(
                (d for d in dispositivos if d.get("id_logico") == id_logico), None
            )
            if dispositivo is None:
                return True, ""
            estado = dispositivo.get("estado", "activo")
            if estado != "activo":
                return False, f"Dispositivo {id_logico} esta en estado '{estado}' — lecturas rechazadas"
    except Exception:
        pass
    return True, ""


def procesar_una_lectura(
    lectura_data: LecturaEntrada,
    db: Session,
    lote_id: int = None,
    usuario_id: int = None,
):
    if not verificar_rate_limit(lectura_data.id_logico):
        return None, "rate_limit", f"{lectura_data.id_logico} excedio {LIMITE_POR_MINUTO} lecturas/min"

    permitido, motivo = verificar_estado_dispositivo(lectura_data.id_logico)
    if not permitido:
        return None, "dispositivo_inactivo", motivo

    bandera, razon_error = validar_lectura(
        lectura_data.tipo_metrica,
        lectura_data.valor_metrica
    )

    ts = normalizar_timestamp(lectura_data.timestamp_lectura)

    lectura = LecturaSensor(
        usuario_id=usuario_id,
        dispositivo_id=lectura_data.dispositivo_id,
        id_logico=lectura_data.id_logico,
        tipo_metrica=lectura_data.tipo_metrica,
        valor_metrica=lectura_data.valor_metrica,
        unidad=lectura_data.unidad,
        timestamp_lectura=ts,
        bandera_calidad=bandera,
        lote_id=lote_id
    )
    db.add(lectura)
    db.flush()

    publish_telemetry_raw(lectura)

    alertas_detectadas = detectar_alertas(
        lectura_data.tipo_metrica,
        lectura_data.valor_metrica
    )
    alertas_guardadas = procesar_alertas(
        db=db,
        dispositivo_id=lectura_data.dispositivo_id,
        id_logico=lectura_data.id_logico,
        tipo_metrica=lectura_data.tipo_metrica,
        valor=lectura_data.valor_metrica,
        alertas_detectadas=alertas_detectadas,
        usuario_id=usuario_id,
    )

    for alerta in alertas_guardadas:
        publish_alert_generated(alerta)

    return lectura, bandera, razon_error


# ── Lectura individual ────────────────────────────────
@router.post("/", response_model=LecturaRespuesta, status_code=201)
def recibir_lectura(
    payload: LecturaEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    lectura, bandera, razon_error = procesar_una_lectura(payload, db, usuario_id=usuario_id)

    if lectura is None:
        if bandera == "rate_limit":
            raise HTTPException(status_code=429, detail=razon_error)
        if bandera == "dispositivo_inactivo":
            raise HTTPException(status_code=403, detail=razon_error)
        raise HTTPException(status_code=400, detail=razon_error)

    if bandera == "invalido":
        error = ErrorIngesta(payload_raw=payload.model_dump_json(), razon_error=razon_error)
        db.add(error)

    db.commit()
    db.refresh(lectura)
    return lectura


# ── Lote ──────────────────────────────────────────────
@router.post("/lote", response_model=LoteRespuesta, status_code=201)
def recibir_lote(
    payload: LoteEntrada,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    lote = LoteIngesta(
        tipo_origen=payload.tipo_origen,
        total_registros=len(payload.lecturas)
    )
    db.add(lote)
    db.flush()

    validos = invalidos = 0

    for lectura_data in payload.lecturas:
        lectura, bandera, razon_error = procesar_una_lectura(
            lectura_data, db, lote_id=lote.id, usuario_id=usuario_id
        )
        if lectura is None or bandera == "invalido":
            invalidos += 1
            db.add(ErrorIngesta(
                lote_id=lote.id,
                payload_raw=lectura_data.model_dump_json(),
                razon_error=razon_error
            ))
        else:
            validos += 1

    lote.registros_validos   = validos
    lote.registros_invalidos = invalidos
    lote.estado = "procesado"

    db.commit()
    db.refresh(lote)
    publish_batch_completed(lote)

    return LoteRespuesta(
        lote_id=lote.id,
        total_registros=lote.total_registros,
        registros_validos=validos,
        registros_invalidos=invalidos,
        estado=lote.estado,
        alertas_generadas=0
    )


# ── Ultimas lecturas ──────────────────────────────────
@router.get("/ultimas/{id_logico}", response_model=List[LecturaRespuesta])
def ultimas_lecturas(
    id_logico: str,
    request: Request,
    limite: int = 10,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(LecturaSensor).filter(LecturaSensor.id_logico == id_logico)
    if usuario_id:
        query = query.filter(LecturaSensor.usuario_id == usuario_id)
    lecturas = query.order_by(LecturaSensor.timestamp_lectura.desc()).limit(limite).all()
    if not lecturas:
        raise HTTPException(status_code=404, detail=f"No se encontraron lecturas para {id_logico}")
    return lecturas


# ── Alertas ───────────────────────────────────────────
@router.get("/alertas", response_model=List[AlertaRespuesta])
def listar_alertas(
    request: Request,
    severidad: str = None,
    limite: int = 50,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(AlertaGenerada)
    if usuario_id:
        query = query.filter(AlertaGenerada.usuario_id == usuario_id)
    if severidad:
        query = query.filter(AlertaGenerada.severidad == severidad)
    return query.order_by(AlertaGenerada.generada_en.desc()).limit(limite).all()


@router.get("/alertas/{id_logico}", response_model=List[AlertaRespuesta])
def alertas_por_dispositivo(
    id_logico: str,
    request: Request,
    limite: int = 20,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(AlertaGenerada).filter(AlertaGenerada.id_logico == id_logico)
    if usuario_id:
        query = query.filter(AlertaGenerada.usuario_id == usuario_id)
    alertas = query.order_by(AlertaGenerada.generada_en.desc()).limit(limite).all()
    if not alertas:
        raise HTTPException(status_code=404, detail=f"No se encontraron alertas para {id_logico}")
    return alertas