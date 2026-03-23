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

    class Config:
        from_attributes = True



class CrearDispositivo(BaseModel):
    tipo_dispositivo_id: int   = Field(..., description="ID del tipo de sensor")
    id_logico:           str   = Field(..., min_length=3, max_length=50,
                                       description="ID lógico único, ej: SOIL_HUM_02")
    numero_serial:       str   = Field(..., min_length=3, max_length=100,
                                       description="Serial físico del dispositivo")
    version_firmware:    Optional[str] = Field(None, max_length=50)
    estado:              EstadoDispositivo = EstadoDispositivo.activo



class ActualizarDispositivo(BaseModel):
    version_firmware:     Optional[str]              = None
    estado:               Optional[EstadoDispositivo] = None
    intervalo_muestreo:   Optional[int]               = Field(None, ge=10, le=86400,
                                                        description="Intervalo en segundos")
    protocolo_transmision: Optional[Protocolo]        = None
    umbral_bateria:        Optional[int]              = Field(None, ge=0, le=100,
                                                        description="% mínimo de batería")

    @model_validator(mode="before")
    @classmethod
    def bloquear_campos_inmutables(cls, values):
        campos_protegidos = {"tipo_dispositivo_id", "id_logico", "numero_serial"}
        for campo in campos_protegidos:
            if campo in values:
                raise ValueError(
                    f"El campo '{campo}' no puede modificarse una vez registrado el sensor."
                )
        return values



class RespuestaDispositivo(BaseModel):
    id:                  int
    tipo_dispositivo_id: int
    id_logico:           str
    numero_serial:       str
    version_firmware:    Optional[str]
    estado:              str
    registrado_en:       Optional[datetime]
    ultima_conexion:     Optional[datetime]

    class Config:
        from_attributes = True



class RespuestaMetricasDispositivo(BaseModel):
    dispositivo_id:      int
    id_logico:           str
    tipo_dispositivo:    str
    metricas_permitidas: List[str]
    estado:              str

    class Config:
        from_attributes = True



class CrearDespliegue(BaseModel):
    dispositivo_id: int  = Field(..., description="ID del sensor a desplegar")
    lote_id:        str  = Field(..., min_length=2, max_length=50,
                                  description="ID del lote, ej: LOTE-A1")
    posicion:       Optional[str] = Field(None, max_length=100,
                                           description="Posición dentro del lote")



class RetirarDespliegue(BaseModel):
    motivo_retiro:   str = Field(..., min_length=5, max_length=200,
                                  description="Motivo del retiro o reemplazo")
    estado:          EstadoDespliegue = EstadoDespliegue.retirado
    reemplazado_por: Optional[int]    = Field(None,
                                              description="ID del sensor de reemplazo")




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

    class Config:
        from_attributes = True