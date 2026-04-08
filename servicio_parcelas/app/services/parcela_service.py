from sqlalchemy.orm import Session, joinedload
from app.models.parcela import Parcela, ParcelaSensor, HistorialCultivo, TipoCultivo
from app.schemas.parcela import ParcelaEntrada, ParcelaSensorEntrada, HistorialCultivoEntrada
import httpx
import os

DEVICE_SERVICE_URL = os.getenv("DEVICE_SERVICE_URL", "http://localhost:8001")


def verificar_dispositivo(id_logico: str) -> dict:
    try:
        url = f"{DEVICE_SERVICE_URL}/api/v1/dispositivos/"
        res = httpx.get(url, timeout=3.0)
        if res.status_code == 200:
            dispositivos = res.json()
            return next((d for d in dispositivos if d.get("id_logico") == id_logico), None)
    except Exception:
        pass
    return None


# ── Parcelas ──────────────────────────────────────────
def crear_parcela(db: Session, data: ParcelaEntrada, usuario_id: int) -> Parcela:
    parcela = Parcela(**data.model_dump(), usuario_id=usuario_id)
    db.add(parcela)
    db.commit()
    db.refresh(parcela)
    return parcela


def listar_parcelas(db: Session, estado: str = None, usuario_id: int = None) -> list:
    query = db.query(Parcela).options(
        joinedload(Parcela.sensores),
        joinedload(Parcela.historial).joinedload(HistorialCultivo.tipo_cultivo)
    )
    if usuario_id:
        query = query.filter(Parcela.usuario_id == usuario_id)
    if estado:
        query = query.filter(Parcela.estado == estado)
    parcelas = query.order_by(Parcela.creada_en.desc()).all()
    for p in parcelas:
        for h in p.historial:
            if h.tipo_cultivo:
                h.tipo_cultivo_nombre = h.tipo_cultivo.nombre
    return parcelas


def obtener_parcela(db: Session, parcela_id: int, usuario_id: int = None) -> Parcela:
    query = db.query(Parcela).options(
        joinedload(Parcela.sensores),
        joinedload(Parcela.historial).joinedload(HistorialCultivo.tipo_cultivo)
    ).filter(Parcela.id == parcela_id)
    if usuario_id:
        query = query.filter(Parcela.usuario_id == usuario_id)
    parcela = query.first()
    if parcela:
        for h in parcela.historial:
            if h.tipo_cultivo:
                h.tipo_cultivo_nombre = h.tipo_cultivo.nombre
    return parcela


def actualizar_parcela(db: Session, parcela_id: int, data: dict, usuario_id: int = None) -> Parcela:
    query = db.query(Parcela).filter(Parcela.id == parcela_id)
    if usuario_id:
        query = query.filter(Parcela.usuario_id == usuario_id)
    parcela = query.first()
    if not parcela:
        return None
    for key, val in data.items():
        if val is not None:
            setattr(parcela, key, val)
    db.commit()
    db.refresh(parcela)
    return parcela


def eliminar_parcela(db: Session, parcela_id: int, usuario_id: int = None) -> bool:
    query = db.query(Parcela).filter(Parcela.id == parcela_id)
    if usuario_id:
        query = query.filter(Parcela.usuario_id == usuario_id)
    parcela = query.first()
    if not parcela:
        return False
    db.delete(parcela)
    db.commit()
    return True


# ── Sensores de parcela ───────────────────────────────
def asignar_sensor(db: Session, parcela_id: int, data: ParcelaSensorEntrada) -> tuple:
    parcela = db.query(Parcela).filter(Parcela.id == parcela_id).first()
    if not parcela:
        return None, "Parcela no encontrada"

    existente = db.query(ParcelaSensor).filter(
        ParcelaSensor.parcela_id == parcela_id,
        ParcelaSensor.id_logico == data.id_logico,
        ParcelaSensor.activo == True
    ).first()
    if existente:
        return None, f"El sensor {data.id_logico} ya esta asignado a esta parcela"

    dispositivo = verificar_dispositivo(data.id_logico)
    dispositivo_id = dispositivo["id"] if dispositivo else data.dispositivo_id

    sensor = ParcelaSensor(
        parcela_id=parcela_id,
        dispositivo_id=dispositivo_id,
        id_logico=data.id_logico,
        notas=data.notas,
        activo=True
    )
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor, None


def listar_sensores_parcela(db: Session, parcela_id: int) -> list:
    return db.query(ParcelaSensor).filter(
        ParcelaSensor.parcela_id == parcela_id
    ).all()


def desasignar_sensor(db: Session, parcela_id: int, sensor_id: int) -> bool:
    sensor = db.query(ParcelaSensor).filter(
        ParcelaSensor.id == sensor_id,
        ParcelaSensor.parcela_id == parcela_id
    ).first()
    if not sensor:
        return False
    sensor.activo = False
    db.commit()
    return True


# ── Historial de cultivos ─────────────────────────────
def agregar_historial(db: Session, parcela_id: int, data: HistorialCultivoEntrada) -> tuple:
    parcela = db.query(Parcela).filter(Parcela.id == parcela_id).first()
    if not parcela:
        return None, "Parcela no encontrada"

    tipo = db.query(TipoCultivo).filter(TipoCultivo.id == data.tipo_cultivo_id).first()
    if not tipo:
        return None, "Tipo de cultivo no encontrado"

    historial = HistorialCultivo(parcela_id=parcela_id, **data.model_dump())
    db.add(historial)
    db.commit()
    db.refresh(historial)
    historial.tipo_cultivo_nombre = tipo.nombre
    return historial, None


def listar_historial(db: Session, parcela_id: int) -> list:
    registros = db.query(HistorialCultivo).options(
        joinedload(HistorialCultivo.tipo_cultivo)
    ).filter(
        HistorialCultivo.parcela_id == parcela_id
    ).order_by(HistorialCultivo.fecha_siembra.desc()).all()
    for r in registros:
        if r.tipo_cultivo:
            r.tipo_cultivo_nombre = r.tipo_cultivo.nombre
    return registros


def actualizar_historial(db: Session, historial_id: int, data: dict) -> HistorialCultivo:
    h = db.query(HistorialCultivo).options(
        joinedload(HistorialCultivo.tipo_cultivo)
    ).filter(HistorialCultivo.id == historial_id).first()
    if not h:
        return None
    for key, val in data.items():
        if val is not None:
            setattr(h, key, val)
    db.commit()
    db.refresh(h)
    if h.tipo_cultivo:
        h.tipo_cultivo_nombre = h.tipo_cultivo.nombre
    return h


# ── Tipos de cultivo ──────────────────────────────────
def listar_tipos_cultivo(db: Session) -> list:
    return db.query(TipoCultivo).filter(TipoCultivo.activo == True).all()


def crear_tipo_cultivo(db: Session, data) -> TipoCultivo:
    tipo = TipoCultivo(**data.model_dump())
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo


# ── Resumen de parcelas ───────────────────────────────
def resumen_parcelas(db: Session, usuario_id: int = None) -> list:
    query = db.query(Parcela).options(
        joinedload(Parcela.sensores),
        joinedload(Parcela.historial).joinedload(HistorialCultivo.tipo_cultivo)
    )
    if usuario_id:
        query = query.filter(Parcela.usuario_id == usuario_id)
    parcelas = query.all()
    resultado = []
    for p in parcelas:
        sensores_activos = sum(1 for s in p.sensores if s.activo)
        cultivo_activo = next(
            (h.tipo_cultivo.nombre for h in p.historial
             if h.estado == 'activo' and h.tipo_cultivo),
            None
        )
        resultado.append({
            "id":             p.id,
            "nombre":         p.nombre,
            "area_hectareas": p.area_hectareas,
            "tipo_suelo":     p.tipo_suelo,
            "municipio":      p.municipio,
            "departamento":   p.departamento,
            "estado":         p.estado,
            "total_sensores": sensores_activos,
            "cultivo_activo": cultivo_activo,
            "latitud":        p.latitud,
            "longitud":       p.longitud,
        })
    return resultado