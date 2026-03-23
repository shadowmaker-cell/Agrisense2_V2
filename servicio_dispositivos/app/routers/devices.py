from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
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
    RetirarDespliegue, RespuestaDespliegue
)
from app.events.producer import publicar_dispositivo_creado, publicar_dispositivo_actualizado

router = APIRouter(prefix="/api/v1/dispositivos", tags=["Dispositivos"])


# ══════════════════════════════════════════════════════
# TIPOS DE SENSOR — solo lectura
# ══════════════════════════════════════════════════════

@router.get("/tipos", response_model=List[RespuestaTipoDispositivo])
def listar_tipos(db: Session = Depends(get_db)):
    """Lista todos los tipos de sensor disponibles."""
    return db.query(TipoDispositivo).all()


@router.get("/tipos/{tipo_id}", response_model=RespuestaTipoDispositivo)
def obtener_tipo(tipo_id: int, db: Session = Depends(get_db)):
    """Consulta un tipo de sensor por ID."""
    tipo = db.query(TipoDispositivo).filter(TipoDispositivo.id == tipo_id).first()
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo de sensor no encontrado")
    return tipo


# ══════════════════════════════════════════════════════
# DISPOSITIVOS — registro y gestión
# ══════════════════════════════════════════════════════

@router.post("/", response_model=RespuestaDispositivo, status_code=201)
def registrar_dispositivo(payload: CrearDispositivo, db: Session = Depends(get_db)):
    """Registra un nuevo sensor en el inventario."""

    # Verifica que el tipo de sensor existe
    tipo = db.query(TipoDispositivo).filter(
        TipoDispositivo.id == payload.tipo_dispositivo_id
    ).first()
    if not tipo:
        raise HTTPException(status_code=404,
                            detail="Tipo de sensor no encontrado")

    # Verifica duplicados
    if db.query(Dispositivo).filter(
        Dispositivo.numero_serial == payload.numero_serial
    ).first():
        raise HTTPException(status_code=400,
                            detail="El número serial ya está registrado")

    if db.query(Dispositivo).filter(
        Dispositivo.id_logico == payload.id_logico
    ).first():
        raise HTTPException(status_code=400,
                            detail="El ID lógico ya está en uso")

    # Crea el dispositivo
    dispositivo = Dispositivo(
        tipo_dispositivo_id=payload.tipo_dispositivo_id,
        id_logico=payload.id_logico,
        numero_serial=payload.numero_serial,
        version_firmware=payload.version_firmware,
        estado=payload.estado
    )
    db.add(dispositivo)
    db.commit()
    db.refresh(dispositivo)

    # Crea configuración por defecto
    config = ConfiguracionDispositivo(dispositivo_id=dispositivo.id)
    db.add(config)
    db.commit()

    # Publica evento a Kafka
    publicar_dispositivo_creado(dispositivo)
    return dispositivo


@router.get("/", response_model=List[RespuestaDispositivo])
def listar_dispositivos(
    skip: int = 0,
    limit: int = 50,
    estado: str = None,
    db: Session = Depends(get_db)
):
    """Lista todos los sensores. Filtra por estado si se indica."""
    consulta = db.query(Dispositivo)
    if estado:
        consulta = consulta.filter(Dispositivo.estado == estado)
    return consulta.offset(skip).limit(limit).all()


@router.get("/{dispositivo_id}", response_model=RespuestaDispositivo)
def obtener_dispositivo(dispositivo_id: int, db: Session = Depends(get_db)):
    """Consulta un sensor por su ID."""
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return dispositivo


@router.put("/{dispositivo_id}", response_model=RespuestaDispositivo)
def actualizar_dispositivo(
    dispositivo_id: int,
    payload: ActualizarDispositivo,
    db: Session = Depends(get_db)
):
    """Actualiza estado o configuración de un sensor."""
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    # Registra historial si cambia el estado
    if payload.estado and payload.estado != dispositivo.estado:
        historial = HistorialEstadoDispositivo(
            dispositivo_id=dispositivo.id,
            estado_anterior=dispositivo.estado,
            estado_nuevo=payload.estado
        )
        db.add(historial)

    # Separa campos del dispositivo y de su configuración
    datos = payload.model_dump(exclude_unset=True)
    campos_config = {"intervalo_muestreo", "protocolo_transmision", "umbral_bateria"}

    for campo, valor in datos.items():
        if campo in campos_config:
            setattr(dispositivo.configuracion, campo, valor)
        else:
            setattr(dispositivo, campo, valor)

    db.commit()
    db.refresh(dispositivo)

    publicar_dispositivo_actualizado(dispositivo)
    return dispositivo


@router.get("/{dispositivo_id}/metricas", response_model=RespuestaMetricasDispositivo)
def obtener_metricas_dispositivo(dispositivo_id: int, db: Session = Depends(get_db)):
    """
    Devuelve las métricas permitidas para este sensor.
    Usado por el microservicio de ingesta para filtrar datos.
    """
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    return RespuestaMetricasDispositivo(
        dispositivo_id=dispositivo.id, # type: ignore
        id_logico=dispositivo.id_logico, # type: ignore
        tipo_dispositivo=dispositivo.tipo_dispositivo.nombre,
        metricas_permitidas=dispositivo.tipo_dispositivo.metricas_permitidas,
        estado=dispositivo.estado # type: ignore
    )




@router.post("/{dispositivo_id}/despliegues",
             response_model=RespuestaDespliegue, status_code=201)
def crear_despliegue(
    dispositivo_id: int,
    payload: CrearDespliegue,
    db: Session = Depends(get_db)
):
    """Instala un sensor en un lote del huerto."""
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id
    ).first()
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    if dispositivo.estado != "activo":
        raise HTTPException(status_code=400,
                            detail="Solo se pueden desplegar sensores activos")

    # Verifica que no haya otro despliegue activo para este sensor
    despliegue_activo = db.query(DespliegueDispositivo).filter(
        DespliegueDispositivo.dispositivo_id == dispositivo_id,
        DespliegueDispositivo.estado == "activo"
    ).first()
    if despliegue_activo:
        raise HTTPException(status_code=400,
                            detail=f"El sensor ya está desplegado en el lote "
                                   f"{despliegue_activo.lote_id}")

    despliegue = DespliegueDispositivo(
        dispositivo_id=dispositivo_id,
        lote_id=payload.lote_id,
        posicion=payload.posicion
    )
    db.add(despliegue)
    db.commit()
    db.refresh(despliegue)
    return despliegue


@router.get("/{dispositivo_id}/despliegues", response_model=List[RespuestaDespliegue])
def historial_despliegues(dispositivo_id: int, db: Session = Depends(get_db)):
    """Historial completo de despliegues de un sensor."""
    dispositivo = db.query(Dispositivo).filter(
        Dispositivo.id == dispositivo_id
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
    db: Session = Depends(get_db)
):
    """
    Retira un sensor de su lote actual.
    Si se indica reemplazado_por, instala automáticamente el sensor de reemplazo
    en el mismo lote y posición.
    """
    # Busca despliegue activo
    despliegue = db.query(DespliegueDispositivo).filter(
        DespliegueDispositivo.dispositivo_id == dispositivo_id,
        DespliegueDispositivo.estado == "activo"
    ).first()
    if not despliegue:
        raise HTTPException(status_code=404,
                            detail="El sensor no tiene un despliegue activo")

    # Retira el sensor actual
    despliegue.estado        = payload.estado
    despliegue.motivo_retiro = payload.motivo_retiro
    despliegue.retirado_en   = datetime.now(timezone.utc)
    despliegue.reemplazado_por = payload.reemplazado_por

    # Si hay reemplazo, verifica que existe y lo despliega en el mismo lote
    if payload.reemplazado_por:
        reemplazo = db.query(Dispositivo).filter(
            Dispositivo.id == payload.reemplazado_por
        ).first()
        if not reemplazo:
            raise HTTPException(status_code=404,
                                detail="El sensor de reemplazo no existe")
        if reemplazo.estado != "activo":
            raise HTTPException(status_code=400,
                                detail="El sensor de reemplazo debe estar activo")

        nuevo_despliegue = DespliegueDispositivo(
            dispositivo_id=payload.reemplazado_por,
            lote_id=despliegue.lote_id,
            posicion=despliegue.posicion
        )
        db.add(nuevo_despliegue)

    db.commit()
    db.refresh(despliegue)
    return despliegue