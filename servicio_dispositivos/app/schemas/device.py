from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EstadoDispositivo(str, Enum):
    activo        = "activo"
    inactivo      = "inactivo"
    mantenimiento = "mantenimiento"
    averiado      = "averiado"


class Protocolo(str, Enum):
    HTTP = "HTTP"
    MQTT = "MQTT"


class EstadoDespliegue(str, Enum):
    activo        = "activo"
    retirado      = "retirado"
    mantenimiento = "mantenimiento"
    averiado      = "averiado"


# ── Tipos de sensor ───────────────────────────────────
class RespuestaTipoDispositivo(BaseModel):
    id:                  int
    nombre:              str
    categoria:           str
    unidad:              Optional[str]
    rango_minimo:        Optional[float]
    rango_maximo:        Optional[float]
    umbral_alerta:       Optional[str]
    tipo_pin:            Optional[str]
    metricas_permitidas: List[str]

    model_config = {"from_attributes": True}


# ── Configuracion del sensor ──────────────────────────
class RespuestaConfiguracion(BaseModel):
    intervalo_muestreo:    Optional[int]
    protocolo_transmision: Optional[str]
    umbral_bateria:        Optional[int]
    limite_minimo:         Optional[float]
    limite_maximo:         Optional[float]
    parcela_id:            Optional[int]
    parcela_nombre:        Optional[str]
    posicion_campo:        Optional[str]

    model_config = {"from_attributes": True}


# ── Crear dispositivo ─────────────────────────────────
class CrearDispositivo(BaseModel):
    tipo_dispositivo_id: int  = Field(..., description="ID del tipo de sensor")
    id_logico:           str  = Field(..., min_length=3, max_length=50)
    numero_serial:       str  = Field(..., min_length=3, max_length=100)
    version_firmware:    Optional[str] = Field(None, max_length=50)
    estado:              EstadoDispositivo = EstadoDispositivo.activo
    parcela_id:          Optional[int]   = None
    parcela_nombre:      Optional[str]   = None
    posicion_campo:      Optional[str]   = None
    limite_minimo:       Optional[float] = None
    limite_maximo:       Optional[float] = None


# ── Actualizar dispositivo ────────────────────────────
class ActualizarDispositivo(BaseModel):
    version_firmware:      Optional[str]               = None
    estado:                Optional[EstadoDispositivo]  = None
    intervalo_muestreo:    Optional[int]                = Field(None, ge=10, le=86400)
    protocolo_transmision: Optional[Protocolo]          = None
    umbral_bateria:        Optional[int]                = Field(None, ge=0, le=100)
    limite_minimo:         Optional[float]              = None
    limite_maximo:         Optional[float]              = None
    parcela_id:            Optional[int]                = None
    parcela_nombre:        Optional[str]                = None
    posicion_campo:        Optional[str]                = None

    @model_validator(mode="before")
    @classmethod
    def bloquear_campos_inmutables(cls, values):
        campos_protegidos = {"tipo_dispositivo_id", "id_logico", "numero_serial"}
        for campo in campos_protegidos:
            if campo in values:
                raise ValueError(f"El campo '{campo}' no puede modificarse.")
        return values


# ── Respuesta dispositivo ─────────────────────────────
class RespuestaDispositivo(BaseModel):
    id:                  int
    usuario_id:          Optional[int]
    tipo_dispositivo_id: int
    id_logico:           str
    numero_serial:       str
    version_firmware:    Optional[str]
    estado:              str
    registrado_en:       Optional[datetime]
    ultima_conexion:     Optional[datetime]
    configuracion:       Optional[RespuestaConfiguracion] = None

    model_config = {"from_attributes": True}


# ── Metricas ──────────────────────────────────────────
class RespuestaMetricasDispositivo(BaseModel):
    dispositivo_id:      int
    id_logico:           str
    tipo_dispositivo:    str
    metricas_permitidas: List[str]
    estado:              str
    limite_minimo:       Optional[float] = None
    limite_maximo:       Optional[float] = None

    model_config = {"from_attributes": True}


# ── Despliegues ───────────────────────────────────────
class CrearDespliegue(BaseModel):
    dispositivo_id: int = Field(..., description="ID del sensor")
    lote_id:        str = Field(..., min_length=2, max_length=50)
    posicion:       Optional[str] = Field(None, max_length=100)


class RetirarDespliegue(BaseModel):
    motivo_retiro:   str = Field(..., min_length=5, max_length=200)
    estado:          EstadoDespliegue = EstadoDespliegue.retirado
    reemplazado_por: Optional[int]    = None


class RespuestaDespliegue(BaseModel):
    id:              int
    dispositivo_id:  int
    lote_id:         str
    posicion:        Optional[str]
    instalado_en:    Optional[datetime]
    retirado_en:     Optional[datetime]
    estado:          str
    motivo_retiro:   Optional[str]
    reemplazado_por: Optional[int]

    model_config = {"from_attributes": True}