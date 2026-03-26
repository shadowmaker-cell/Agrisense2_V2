from sqlalchemy import (
    Column, Integer, String, DateTime,
    Float, Text, Boolean
)
from sqlalchemy.sql import func
from app.database import Base


class Notificacion(Base):
    """Registro de notificaciones generadas."""
    __tablename__ = "notificacion"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    usuario_id      = Column(Integer, nullable=True)
    dispositivo_id  = Column(Integer, nullable=False, index=True)
    id_logico       = Column(String(50), nullable=False, index=True)
    titulo          = Column(String(200), nullable=False)
    mensaje         = Column(Text, nullable=False)
    tipo            = Column(String(50), nullable=False)
    # alerta_helada / alerta_sequia / alerta_hongo / alerta_viento / etc
    severidad       = Column(String(20), nullable=False)
    # baja / media / alta / critica
    canal           = Column(String(20), default="sistema")
    # sistema / email / sms / push
    estado          = Column(String(20), default="pendiente")
    # pendiente / enviada / fallida
    creada_en       = Column(DateTime(timezone=True), server_default=func.now())
    enviada_en      = Column(DateTime(timezone=True), nullable=True)
    leida           = Column(Boolean, default=False)
    origen_evento   = Column(String(50), nullable=True)
    # telemetry.raw / alert.generated / recommendation.generated


class PreferenciaNotificacion(Base):
    """Preferencias de notificación por usuario."""
    __tablename__ = "preferencia_notificacion"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    usuario_id      = Column(Integer, nullable=False, unique=True)
    canal_preferido = Column(String(20), default="sistema")
    activo          = Column(Boolean, default=True)
    alertas_criticas = Column(Boolean, default=True)
    alertas_altas    = Column(Boolean, default=True)
    alertas_medias   = Column(Boolean, default=False)
    alertas_bajas    = Column(Boolean, default=False)
    actualizado_en   = Column(DateTime(timezone=True), onupdate=func.now())


class LogEnvio(Base):
    """Log de intentos de envío de notificaciones."""
    __tablename__ = "log_envio"

    id               = Column(Integer, primary_key=True, autoincrement=True, index=True)
    notificacion_id  = Column(Integer, nullable=False, index=True)
    canal            = Column(String(20), nullable=False)
    estado           = Column(String(20), nullable=False)
    # enviado / fallido
    respuesta        = Column(Text, nullable=True)
    intentado_en     = Column(DateTime(timezone=True), server_default=func.now())