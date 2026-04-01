from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Tipo Cultivo ──────────────────────────────────────
class TipoCultivoRespuesta(BaseModel):
    id:          int
    nombre:      str
    descripcion: Optional[str]
    temporada:   Optional[str]
    activo:      bool

    class Config:
        from_attributes = True


class TipoCultivoEntrada(BaseModel):
    nombre:      str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    temporada:   Optional[str] = None


# ── Parcela Sensor ────────────────────────────────────
class ParcelaSensorRespuesta(BaseModel):
    id:                int
    parcela_id:        int
    dispositivo_id:    int
    id_logico:         str
    fecha_instalacion: datetime
    activo:            bool
    notas:             Optional[str]

    class Config:
        from_attributes = True


class ParcelaSensorEntrada(BaseModel):
    dispositivo_id: int
    id_logico:      str = Field(..., min_length=3, max_length=50)
    notas:          Optional[str] = None


# ── Historial Cultivo ─────────────────────────────────
class HistorialCultivoRespuesta(BaseModel):
    id:                int
    parcela_id:        int
    tipo_cultivo_id:   int
    tipo_cultivo_nombre: Optional[str] = None
    fecha_siembra:     datetime
    fecha_cosecha:     Optional[datetime]
    etapa_fenologica:  Optional[str]
    rendimiento_kg:    Optional[float]
    observaciones:     Optional[str]
    estado:            str
    creado_en:         datetime

    class Config:
        from_attributes = True


class HistorialCultivoEntrada(BaseModel):
    tipo_cultivo_id:  int
    fecha_siembra:    datetime
    fecha_cosecha:    Optional[datetime] = None
    etapa_fenologica: Optional[str] = None
    rendimiento_kg:   Optional[float] = None
    observaciones:    Optional[str] = None
    estado:           str = Field(default='activo', pattern='^(activo|finalizado|perdido)$')


# ── Parcela ───────────────────────────────────────────
class ParcelaRespuesta(BaseModel):
    id:             int
    nombre:         str
    descripcion:    Optional[str]
    area_hectareas: float
    tipo_suelo:     Optional[str]
    latitud:        Optional[float]
    longitud:       Optional[float]
    altitud_msnm:   Optional[float]
    departamento:   Optional[str]
    municipio:      Optional[str]
    vereda:         Optional[str]
    estado:         str
    creada_en:      datetime
    sensores:       List[ParcelaSensorRespuesta] = []
    historial:      List[HistorialCultivoRespuesta] = []

    class Config:
        from_attributes = True


class ParcelaEntrada(BaseModel):
    nombre:         str = Field(..., min_length=2, max_length=100)
    descripcion:    Optional[str] = None
    area_hectareas: float = Field(..., gt=0)
    tipo_suelo:     Optional[str] = None
    latitud:        Optional[float] = Field(None, ge=-90,  le=90)
    longitud:       Optional[float] = Field(None, ge=-180, le=180)
    altitud_msnm:   Optional[float] = None
    departamento:   Optional[str] = None
    municipio:      Optional[str] = None
    vereda:         Optional[str] = None
    estado:         str = Field(default='activa', pattern='^(activa|inactiva|en_preparacion)$')


class ParcelaResumen(BaseModel):
    id:             int
    nombre:         str
    area_hectareas: float
    tipo_suelo:     Optional[str]
    municipio:      Optional[str]
    departamento:   Optional[str]
    estado:         str
    total_sensores: int
    cultivo_activo: Optional[str]
    latitud:        Optional[float]
    longitud:       Optional[float]

    class Config:
        from_attributes = True