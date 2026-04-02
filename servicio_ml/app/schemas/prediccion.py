from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Modelo Registro ───────────────────────────────────
class ModeloRegistroRespuesta(BaseModel):
    id:              int
    nombre:          str
    version:         str
    tipo:            str
    descripcion:     Optional[str]
    variable_target: str
    features:        Optional[List[str]]
    metricas:        Optional[Dict[str, float]]
    estado:          str
    registrado_en:   datetime

    model_config = {"from_attributes": True}


# ── Prediccion de agua ────────────────────────────────
class PrediccionAguaEntrada(BaseModel):
    parcela_id:        Optional[int] = None
    id_logico:         Optional[str] = None
    humedad_suelo:     float = Field(..., ge=0, le=100,  description="% humedad actual del suelo")
    temperatura_aire:  float = Field(..., ge=-10, le=60, description="Temperatura en Celsius")
    lluvia:            float = Field(0.0, ge=0,          description="mm de lluvia reciente")
    area_hectareas:    float = Field(1.0, gt=0,          description="Hectareas de la parcela")
    tipo_cultivo:      Optional[str] = "maiz"


class PrediccionAguaRespuesta(BaseModel):
    litros_recomendados: float
    frecuencia_horas:    int
    urgencia:            str
    confianza:           float
    explicacion:         str
    solicitud_id:        int


# ── Prediccion de rendimiento ─────────────────────────
class PrediccionRendimientoEntrada(BaseModel):
    parcela_id:        Optional[int] = None
    id_logico:         Optional[str] = None
    area_hectareas:    float = Field(..., gt=0)
    tipo_cultivo:      str = Field(..., min_length=2)
    humedad_suelo:     float = Field(..., ge=0, le=100)
    temperatura_aire:  float = Field(..., ge=-10, le=60)
    ph_suelo:          float = Field(6.5, ge=0, le=14)
    lluvia_acumulada:  float = Field(0.0, ge=0)
    etapa_fenologica:  Optional[str] = "vegetativo"


class PrediccionRendimientoRespuesta(BaseModel):
    rendimiento_kg_ha:   float
    rendimiento_total_kg: float
    calificacion:        str
    confianza:           float
    factores_riesgo:     List[str]
    recomendaciones:     List[str]
    solicitud_id:        int


# ── Prediccion de riesgo ──────────────────────────────
class PrediccionRiesgoEntrada(BaseModel):
    parcela_id:       Optional[int] = None
    id_logico:        Optional[str] = None
    temperatura_aire: float = Field(..., ge=-40, le=60)
    humedad_aire:     float = Field(60.0, ge=0, le=100)
    humedad_suelo:    float = Field(50.0, ge=0, le=100)
    velocidad_viento: float = Field(0.0, ge=0)
    lluvia:           float = Field(0.0, ge=0)
    tipo_riesgo:      str   = Field(..., pattern="^(helada|sequia|hongo|inundacion)$")


class PrediccionRiesgoRespuesta(BaseModel):
    tipo_riesgo:      str
    probabilidad:     float
    nivel:            str
    # bajo | medio | alto | critico
    acciones:         List[str]
    confianza:        float
    solicitud_id:     int


# ── Historial y consultas ─────────────────────────────
class SolicitudPrediccionRespuesta(BaseModel):
    id:              int
    modelo_id:       int
    parcela_id:      Optional[int]
    id_logico:       Optional[str]
    tipo_prediccion: str
    estado:          str
    solicitado_en:   datetime

    model_config = {"from_attributes": True}


class ResultadoPrediccionRespuesta(BaseModel):
    id:             int
    solicitud_id:   int
    valor_predicho: float
    confianza:      Optional[float]
    unidad:         Optional[str]
    explicacion:    Optional[str]
    generado_en:    datetime

    model_config = {"from_attributes": True}


class ResumenMLRespuesta(BaseModel):
    total_predicciones:    int
    predicciones_agua:     int
    predicciones_riesgo:   int
    predicciones_rendimiento: int
    modelos_activos:       int
    ultima_prediccion:     Optional[datetime]