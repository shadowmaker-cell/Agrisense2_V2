from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NotificacionRespuesta(BaseModel):
    id:             int
    dispositivo_id: int
    id_logico:      str
    titulo:         str
    mensaje:        str
    tipo:           str
    severidad:      str
    canal:          str
    estado:         str
    creada_en:      datetime
    enviada_en:     Optional[datetime]
    leida:          bool

    model_config = {"from_attributes": True}


class NotificacionManualEntrada(BaseModel):
    dispositivo_id: int
    id_logico:      str   = Field(..., min_length=3, max_length=50)
    tipo_alerta:    str   = Field(..., min_length=2, max_length=50)
    tipo_metrica:   str   = Field(..., min_length=2, max_length=50)
    valor:          float
    condicion:      str   = Field(..., min_length=3, max_length=255)
    severidad:      str   = Field(..., pattern="^(baja|media|alta|critica)$")
    canal:          str   = Field(default="email")
    email_destino:  Optional[str] = Field(default="")


class PreferenciaEntrada(BaseModel):
    canal_preferido:  str  = Field(default="email")
    activo:           bool = True
    alertas_criticas: bool = True
    alertas_altas:    bool = True
    alertas_medias:   bool = False
    alertas_bajas:    bool = False


class PreferenciaRespuesta(BaseModel):
    id:               int
    usuario_id:       int
    canal_preferido:  str
    activo:           bool
    alertas_criticas: bool
    alertas_altas:    bool
    alertas_medias:   bool
    alertas_bajas:    bool

    model_config = {"from_attributes": True}


class ResumenNotificaciones(BaseModel):
    total:     int
    pendientes: int
    enviadas:  int
    fallidas:  int
    no_leidas: int
    criticas:  int