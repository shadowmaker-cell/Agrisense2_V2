from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class EventoRespuesta(BaseModel):
    id:                int
    dispositivo_id:    int
    id_logico:         str
    tipo_metrica:      str
    valor_metrica:     float
    unidad:            Optional[str]
    timestamp_lectura: datetime
    procesado_en:      datetime
    tiene_alerta:      bool

    class Config:
        from_attributes = True


class AlertaStreamRespuesta(BaseModel):
    id:              int
    dispositivo_id:  int
    id_logico:       str
    tipo_metrica:    str
    valor_detectado: float
    condicion:       str
    severidad:       str
    tipo_alerta:     str
    generada_en:     datetime
    notificada:      bool

    class Config:
        from_attributes = True


class ResumenProcesamiento(BaseModel):
    total_eventos:    int
    total_alertas:    int
    alertas_criticas: int
    alertas_altas:    int
    alertas_medias:   int


class ProcesarManualEntrada(BaseModel):
    dispositivo_id: int
    id_logico:      str = Field(..., min_length=3, max_length=50)
    tipo_metrica:   str = Field(..., min_length=2, max_length=50)
    valor_metrica:  float
    unidad:         Optional[str] = None