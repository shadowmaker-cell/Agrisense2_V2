from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class BanderaCalidad(str, Enum):
    valido     = "valido"
    sospechoso = "sospechoso"
    invalido   = "invalido"


class SeveridadAlerta(str, Enum):
    baja    = "baja"
    media   = "media"
    alta    = "alta"
    critica = "critica"



class LecturaEntrada(BaseModel):
    dispositivo_id:    int
    id_logico:         str  = Field(..., min_length=3, max_length=50)
    tipo_metrica:      str  = Field(..., min_length=2, max_length=50)
    valor_metrica:     float
    unidad:            Optional[str] = None
    timestamp_lectura: Optional[datetime] = None



class LoteEntrada(BaseModel):
    lecturas: List[LecturaEntrada] = Field(..., min_length=1, max_length=1000)
    tipo_origen: str = "HTTP"



class LecturaRespuesta(BaseModel):
    id:                int
    dispositivo_id:    int
    id_logico:         str
    tipo_metrica:      str
    valor_metrica:     float
    unidad:            Optional[str]
    timestamp_lectura: datetime
    recibido_en:       datetime
    bandera_calidad:   str

    class Config:
        from_attributes = True



class LoteRespuesta(BaseModel):
    lote_id:             int
    total_registros:     int
    registros_validos:   int
    registros_invalidos: int
    estado:              str
    alertas_generadas:   int = 0



class AlertaRespuesta(BaseModel):
    id:              int
    dispositivo_id:  int
    id_logico:       str
    tipo_metrica:    str
    valor_detectado: float
    condicion:       str
    severidad:       str
    generada_en:     datetime

    class Config:
        from_attributes = True


class UltimasLecturasRespuesta(BaseModel):
    id_logico:    str
    tipo_metrica: str
    ultimo_valor: float
    unidad:       Optional[str]
    timestamp:    datetime
    calidad:      str