from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Categoria ─────────────────────────────────────────
class CategoriaRespuesta(BaseModel):
    id:          int
    nombre:      str
    descripcion: Optional[str]
    icono:       Optional[str]
    activo:      bool

    model_config = {"from_attributes": True}


# ── Evidencia ─────────────────────────────────────────
class EvidenciaRespuesta(BaseModel):
    id:               int
    recomendacion_id: int
    tipo_fuente:      str
    descripcion:      str
    valor_observado:  Optional[float]
    valor_esperado:   Optional[float]
    unidad:           Optional[str]
    creado_en:        datetime

    model_config = {"from_attributes": True}


class EvidenciaEntrada(BaseModel):
    tipo_fuente:     str
    descripcion:     str
    valor_observado: Optional[float] = None
    valor_esperado:  Optional[float] = None
    unidad:          Optional[str]   = None


# ── Recomendacion ─────────────────────────────────────
class RecomendacionRespuesta(BaseModel):
    id:             int
    categoria_id:   int
    categoria_nombre: Optional[str] = None
    parcela_id:     Optional[int]
    id_logico:      Optional[str]
    titulo:         str
    descripcion:    str
    accion:         str
    prioridad:      str
    estado:         str
    fuente:         Optional[str]
    datos_contexto: Optional[Dict[str, Any]]
    valida_hasta:   Optional[datetime]
    generada_en:    datetime
    evidencias:     List[EvidenciaRespuesta] = []

    model_config = {"from_attributes": True}


class RecomendacionEntrada(BaseModel):
    categoria_id:   int
    parcela_id:     Optional[int]  = None
    id_logico:      Optional[str]  = None
    titulo:         str = Field(..., min_length=5, max_length=200)
    descripcion:    str = Field(..., min_length=10)
    accion:         str = Field(..., min_length=5)
    prioridad:      str = Field(default="media", pattern="^(baja|media|alta|critica)$")
    fuente:         Optional[str]  = None
    datos_contexto: Optional[Dict[str, Any]] = None


# ── Generacion automatica ─────────────────────────────
class GenerarRecomendacionesEntrada(BaseModel):
    parcela_id:   Optional[int]   = None
    id_logico:    Optional[str]   = None
    humedad_suelo:    Optional[float] = None
    temperatura_aire: Optional[float] = None
    ph_suelo:         Optional[float] = None
    lluvia:           Optional[float] = None
    velocidad_viento: Optional[float] = None
    humedad_aire:     Optional[float] = None
    tipo_cultivo:     Optional[str]   = None
    area_hectareas:   Optional[float] = None
    etapa_fenologica: Optional[str]   = None


class GenerarRecomendacionesRespuesta(BaseModel):
    total_generadas:  int
    criticas:         int
    altas:            int
    medias:           int
    bajas:            int
    recomendaciones:  List[RecomendacionRespuesta]
    ejecucion_id:     int


# ── Actualizacion de estado ───────────────────────────
class ActualizarEstadoEntrada(BaseModel):
    estado: str = Field(..., pattern="^(activa|aplicada|descartada|vencida)$")


# ── Resumen ───────────────────────────────────────────
class ResumenRecomendacionesRespuesta(BaseModel):
    total:          int
    activas:        int
    aplicadas:      int
    criticas:       int
    altas:          int
    por_categoria:  Dict[str, int]
    ultima_generacion: Optional[datetime]