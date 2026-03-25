from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app.models.lectura import LecturaSensor, LoteIngesta, ErrorIngesta
from app.schemas.lectura import (
    LecturaEntrada, LoteEntrada,
    LecturaRespuesta, LoteRespuesta,
    AlertaRespuesta, UltimasLecturasRespuesta
)
from app.services.validador import validar_lectura, detectar_alertas, normalizar_timestamp
from app.services.alertas import procesar_alertas
from app.events.producer import publish_telemetry_raw, publish_alert_generated, publish_batch_completed

router = APIRouter(prefix="/api/v1/telemetria", tags=["telemetria"])


_contadores = {}
LIMITE_POR_MINUTO = 60


def verificar_rate_limit(id_logico: str) -> bool:
    """Verifica que el dispositivo no exceda 60 lecturas por minuto."""
    ahora = datetime.now(timezone.utc)
    minuto_actual = ahora.strftime("%Y%m%d%H%M")
    clave = f"{id_logico}:{minuto_actual}"

    _contadores[clave] = _contadores.get(clave, 0) + 1


    claves_viejas = [k for k in _contadores if not k.endswith(minuto_actual)]
    for k in claves_viejas:
        del _contadores[k]

    return _contadores[clave] <= LIMITE_POR_MINUTO


def procesar_una_lectura(lectura_data: LecturaEntrada, db: Session, lote_id: int = None):
    """Procesa una lectura individual: valida, persiste, detecta alertas."""

    if not verificar_rate_limit(lectura_data.id_logico):
        return None, "rate_limit", f"{lectura_data.id_logico} excedió {LIMITE_POR_MINUTO} lecturas/min"


    bandera, razon_error = validar_lectura(
        lectura_data.tipo_metrica,
        lectura_data.valor_metrica
    )

  
    ts = normalizar_timestamp(lectura_data.timestamp_lectura)

  
    lectura = LecturaSensor(
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
        alertas_detectadas=alertas_detectadas
    )


    for alerta in alertas_guardadas:
        publish_alert_generated(alerta)

    return lectura, bandera, razon_error



@router.post("/", response_model=LecturaRespuesta, status_code=201)
def recibir_lectura(
    payload: LecturaEntrada,
    db: Session = Depends(get_db)
):
    """Recibe una lectura individual de un sensor IoT."""
    lectura, bandera, razon_error = procesar_una_lectura(payload, db)

    if lectura is None:
        raise HTTPException(status_code=429, detail=razon_error)

    if bandera == "invalido":
        error = ErrorIngesta(
            payload_raw=payload.model_dump_json(),
            razon_error=razon_error
        )
        db.add(error)

    db.commit()
    db.refresh(lectura)
    return lectura



@router.post("/lote", response_model=LoteRespuesta, status_code=201)
def recibir_lote(
    payload: LoteEntrada,
    db: Session = Depends(get_db)
):
    """Recibe un lote de lecturas de sensores IoT."""
    lote = LoteIngesta(
        tipo_origen=payload.tipo_origen,
        total_registros=len(payload.lecturas)
    )
    db.add(lote)
    db.flush()

    validos = 0
    invalidos = 0
    alertas_total = 0

    for lectura_data in payload.lecturas:
        lectura, bandera, razon_error = procesar_una_lectura(
            lectura_data, db, lote_id=lote.id
        )

        if lectura is None or bandera == "invalido":
            invalidos += 1
            error = ErrorIngesta(
                lote_id=lote.id,
                payload_raw=lectura_data.model_dump_json(),
                razon_error=razon_error
            )
            db.add(error)
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
        alertas_generadas=alertas_total
    )



@router.get("/ultimas/{id_logico}", response_model=List[LecturaRespuesta])
def ultimas_lecturas(
    id_logico: str,
    limite: int = 10,
    db: Session = Depends(get_db)
):
    """Retorna las últimas lecturas de un sensor específico."""
    lecturas = db.query(LecturaSensor).filter(
        LecturaSensor.id_logico == id_logico
    ).order_by(
        LecturaSensor.timestamp_lectura.desc()
    ).limit(limite).all()

    if not lecturas:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron lecturas para {id_logico}"
        )
    return lecturas



@router.get("/alertas", response_model=List[AlertaRespuesta])
def listar_alertas(
    severidad: str = None,
    limite: int = 50,
    db: Session = Depends(get_db)
):
    """Lista las alertas generadas durante la ingesta."""
    from app.models.lectura import AlertaGenerada
    query = db.query(AlertaGenerada)
    if severidad:
        query = query.filter(AlertaGenerada.severidad == severidad)
    return query.order_by(AlertaGenerada.generada_en.desc()).limit(limite).all()



@router.get("/alertas/{id_logico}", response_model=List[AlertaRespuesta])
def alertas_por_dispositivo(
    id_logico: str,
    limite: int = 20,
    db: Session = Depends(get_db)
):
    """Lista alertas de un dispositivo específico."""
    from app.models.lectura import AlertaGenerada
    alertas = db.query(AlertaGenerada).filter(
        AlertaGenerada.id_logico == id_logico
    ).order_by(
        AlertaGenerada.generada_en.desc()
    ).limit(limite).all()

    if not alertas:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontraron alertas para {id_logico}"
        )
    return alertas