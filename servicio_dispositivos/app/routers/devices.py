from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.device import (
    Dispositivo, ConfiguracionDispositivo,
    HistorialEstadoDispositivo, TipoDispositivo,
    DespliegueDispositivo
)
from app.schemas.device import (
    CrearDispositivo, ActualizarDispositivo,
    RespuestaDispositivo, RespuestaTipoDispositivo,
    RespuestaMetricasDispositivo, CrearDespliegue,
    RetirarDespliegue, RespuestaDespliegue,
)
from app.events.producer import publicar_dispositivo_creado, publicar_dispositivo_actualizado
from app.utils.jwt import get_usuario_id, get_usuario_id_opcional

router = APIRouter(prefix="/api/v1/dispositivos", tags=["Dispositivos"])


# ── Health ────────────────────────────────────────────
@router.get("/health")
def health():
    return {"estado": "ok", "servicio": "device-management", "version": "1.0.0"}


# ── Tipos de sensor ───────────────────────────────────
@router.get("/tipos", response_model=List[RespuestaTipoDispositivo])
def listar_tipos(db: Session = Depends(get_db)):
    return db.query(TipoDispositivo).all()


@router.get("/tipos/{tipo_id}", response_model=RespuestaTipoDispositivo)
def obtener_tipo(tipo_id: int, db: Session = Depends(get_db)):
    tipo = db.query(TipoDispositivo).filter(TipoDispositivo.id == tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de sensor no encontrado")
    return tipo


# ── Dispositivos ──────────────────────────────────────
@router.post("/", response_model=RespuestaDispositivo, status_code=201)
def registrar_dispositivo(
    payload: CrearDispositivo,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)

    tipo = db.query(TipoDispositivo).filter(
        TipoDispositivo.id == payload.tipo_dispositivo_id
    ).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de sensor no encontrado")

    if db.query(Dispositivo).filter(
        Dispositivo.numero_serial == payload.numero_serial,
        Dispositivo.usuario_id == usuario_id
    ).first():
        raise HTTPException(status_code=400, detail="El numero serial ya esta registrado")

    if db.query(Dispositivo).filter(
        Dispositivo.id_logico == payload.id_logico,
        Dispositivo.usuario_id == usuario_id
    ).first():
        raise HTTPException(status_code=400, detail="El ID logico ya esta en uso")

    dispositivo = Dispositivo(
        usuario_id=usuario_id,
        tipo_dispositivo_id=payload.tipo_dispositivo_id,
        id_logico=payload.id_logico,
        numero_serial=payload.numero_serial,
        version_firmware=payload.version_firmware,
        estado=payload.estado,
    )
    db.add(dispositivo)
    db.commit()
    db.refresh(dispositivo)

    config = ConfiguracionDispositivo(
        dispositivo_id=dispositivo.id,
        limite_minimo=payload.limite_minimo,
        limite_maximo=payload.limite_maximo,
        parcela_id=payload.parcela_id,
        parcela_nombre=payload.parcela_nombre,
        posicion_campo=payload.posicion_campo,
    )
    db.add(config)
    db.commit()
    db.refresh(dispositivo)

    publicar_dispositivo_creado(dispositivo)
    return dispositivo


@router.get("/", response_model=List[RespuestaDispositivo])
def listar_dispositivos(
    request: Request,
    skip:   int           = 0,
    limit:  int           = 100,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    consulta = db.query(Dispositivo).filter(
        Dispositivo.usuario_id == usuario_id
    )
    if estado:
        consulta = consulta.filter(Dispositivo.estado == estado)
    return consulta.offset(skip).limit(limit).all()


@router.get("/{dispositivo_id}", response_model=RespuestaDispositivo)
def obtener_dispositivo(
    dispositivo_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id,
        Dispositivo.usuario_id == usuario_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return dispositivo


@router.put("/{dispositivo_id}", response_model=RespuestaDispositivo)
def actualizar_dispositivo(
    dispositivo_id: int,
    payload: ActualizarDispositivo,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id,
        Dispositivo.usuario_id == usuario_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    if payload.estado and payload.estado != dispositivo.estado:
        historial = HistorialEstadoDispositivo(
            dispositivo_id=dispositivo.id,
            estado_anterior=dispositivo.estado,
            estado_nuevo=payload.estado,
        )
        db.add(historial)

    datos = payload.model_dump(exclude_unset=True)
    campos_config = {
        "intervalo_muestreo", "protocolo_transmision", "umbral_bateria",
        "limite_minimo", "limite_maximo",
        "parcela_id", "parcela_nombre", "posicion_campo",
    }

    for campo, valor in datos.items():
        if campo in campos_config:
            if dispositivo.configuracion:
                setattr(dispositivo.configuracion, campo, valor)
        else:
            setattr(dispositivo, campo, valor)

    db.commit()
    db.refresh(dispositivo)
    publicar_dispositivo_actualizado(dispositivo)
    return dispositivo


@router.get("/{dispositivo_id}/metricas", response_model=RespuestaMetricasDispositivo)
def obtener_metricas_dispositivo(
    dispositivo_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id_opcional(request)
    query = db.query(Dispositivo).filter(Dispositivo.id == dispositivo_id)
    if usuario_id:
        query = query.filter(Dispositivo.usuario_id == usuario_id)
    dispositivo = query.first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    config = dispositivo.configuracion
    return RespuestaMetricasDispositivo(
        dispositivo_id=dispositivo.id,
        id_logico=dispositivo.id_logico,
        tipo_dispositivo=dispositivo.tipo_dispositivo.nombre,
        metricas_permitidas=dispositivo.tipo_dispositivo.metricas_permitidas,
        estado=dispositivo.estado,
        limite_minimo=config.limite_minimo if config else None,
        limite_maximo=config.limite_maximo if config else None,
    )


# ── Hoja de vida ──────────────────────────────────────
@router.get("/{dispositivo_id}/hoja-de-vida")
def hoja_de_vida(
    dispositivo_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id,
        Dispositivo.usuario_id == usuario_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    historial = db.query(HistorialEstadoDispositivo).filter(
        HistorialEstadoDispositivo.dispositivo_id == dispositivo_id
    ).order_by(HistorialEstadoDispositivo.cambiado_en.desc()).all()

    despliegues = db.query(DespliegueDispositivo).filter(
        DespliegueDispositivo.dispositivo_id == dispositivo_id
    ).order_by(DespliegueDispositivo.instalado_en.desc()).all()

    config = dispositivo.configuracion

    return {
        "id":               dispositivo.id,
        "id_logico":        dispositivo.id_logico,
        "numero_serial":    dispositivo.numero_serial,
        "tipo":             dispositivo.tipo_dispositivo.nombre,
        "categoria":        dispositivo.tipo_dispositivo.categoria,
        "estado":           dispositivo.estado,
        "version_firmware": dispositivo.version_firmware,
        "registrado_en":    dispositivo.registrado_en,
        "ultima_conexion":  dispositivo.ultima_conexion,
        "configuracion": {
            "intervalo_muestreo":    config.intervalo_muestreo    if config else None,
            "protocolo_transmision": config.protocolo_transmision if config else None,
            "umbral_bateria":        config.umbral_bateria        if config else None,
            "limite_minimo":         config.limite_minimo         if config else None,
            "limite_maximo":         config.limite_maximo         if config else None,
            "parcela_id":            config.parcela_id            if config else None,
            "parcela_nombre":        config.parcela_nombre        if config else None,
            "posicion_campo":        config.posicion_campo        if config else None,
        } if config else None,
        "total_cambios_estado": len(historial),
        "total_despliegues":    len(despliegues),
        "historial_estados": [
            {
                "estado_anterior": h.estado_anterior,
                "estado_nuevo":    h.estado_nuevo,
                "cambiado_en":     h.cambiado_en,
            } for h in historial
        ],
        "despliegues": [
            {
                "lote_id":       d.lote_id,
                "posicion":      d.posicion,
                "estado":        d.estado,
                "instalado_en":  d.instalado_en,
                "retirado_en":   d.retirado_en,
                "motivo_retiro": d.motivo_retiro,
            } for d in despliegues
        ],
    }


# ── Despliegues ───────────────────────────────────────
@router.post("/{dispositivo_id}/despliegues",
             response_model=RespuestaDespliegue, status_code=201)
def crear_despliegue(
    dispositivo_id: int,
    payload: CrearDespliegue,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id,
        Dispositivo.usuario_id == usuario_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    if dispositivo.estado != "activo":
        raise HTTPException(status_code=400, detail="Solo se pueden desplegar sensores activos")

    despliegue_activo = db.query(DespliegueDispositivo).filter(
        DespliegueDispositivo.dispositivo_id == dispositivo_id,
        DespliegueDispositivo.estado == "activo"
    ).first()
    if despliegue_activo:
        raise HTTPException(
            status_code=400,
            detail=f"El sensor ya esta desplegado en {despliegue_activo.lote_id}"
        )

    despliegue = DespliegueDispositivo(
        dispositivo_id=dispositivo_id,
        lote_id=payload.lote_id,
        posicion=payload.posicion,
    )
    db.add(despliegue)
    db.commit()
    db.refresh(despliegue)
    return despliegue


@router.get("/{dispositivo_id}/despliegues",
            response_model=List[RespuestaDespliegue])
def historial_despliegues(
    dispositivo_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id,
        Dispositivo.usuario_id == usuario_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return db.query(DespliegueDispositivo).filter(
        DespliegueDispositivo.dispositivo_id == dispositivo_id
    ).all()


@router.put("/{dispositivo_id}/despliegues/retirar",
            response_model=RespuestaDespliegue)
def retirar_sensor(
    dispositivo_id: int,
    payload: RetirarDespliegue,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id,
        Dispositivo.usuario_id == usuario_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    despliegue = db.query(DespliegueDispositivo).filter(
        DespliegueDispositivo.dispositivo_id == dispositivo_id,
        DespliegueDispositivo.estado == "activo"
    ).first()
    if not despliegue:
        raise HTTPException(status_code=404, detail="El sensor no tiene despliegue activo")

    despliegue.estado          = payload.estado
    despliegue.motivo_retiro   = payload.motivo_retiro
    despliegue.retirado_en     = datetime.now(timezone.utc)
    despliegue.reemplazado_por = payload.reemplazado_por

    if payload.reemplazado_por:
        reemplazo = db.query(Dispositivo).filter(
            Dispositivo.id == payload.reemplazado_por,
            Dispositivo.usuario_id == usuario_id
        ).first()
        if not reemplazo:
            raise HTTPException(status_code=404, detail="Sensor de reemplazo no existe")
        if reemplazo.estado != "activo":
            raise HTTPException(status_code=400, detail="El sensor de reemplazo debe estar activo")
        nuevo = DespliegueDispositivo(
            dispositivo_id=payload.reemplazado_por,
            lote_id=despliegue.lote_id,
            posicion=despliegue.posicion,
        )
        db.add(nuevo)

    db.commit()
    db.refresh(despliegue)
    return despliegue