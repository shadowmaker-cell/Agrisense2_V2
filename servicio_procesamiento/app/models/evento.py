from sqlalchemy import (
    Column, Integer, String, DateTime,
    Float, Text, Boolean
)
from sqlalchemy.sql import func
from app.database import Base


class EventoProcesado(Base):
    """Registro de eventos de telemetría procesados."""
    __tablename__ = "evento_procesado"

    id                = Column(Integer, primary_key=True, autoincrement=True, index=True)
    dispositivo_id    = Column(Integer, nullable=False, index=True)
    id_logico         = Column(String(50), nullable=False, index=True)
    tipo_metrica      = Column(String(50), nullable=False)
    valor_metrica     = Column(Float, nullable=False)
    unidad            = Column(String(20))
    timestamp_lectura = Column(DateTime(timezone=True), nullable=False)
    procesado_en      = Column(DateTime(timezone=True), server_default=func.now())
    tiene_alerta      = Column(Boolean, default=False)
    topic_origen      = Column(String(50), default="telemetry.raw")


class AlertaStream(Base):
    """Alertas detectadas por el Stream Processor."""
    __tablename__ = "alerta_stream"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    dispositivo_id  = Column(Integer, nullable=False, index=True)
    id_logico       = Column(String(50), nullable=False, index=True)
    tipo_metrica    = Column(String(50), nullable=False)
    valor_detectado = Column(Float, nullable=False)
    condicion       = Column(String(255), nullable=False)
    severidad       = Column(String(20), nullable=False)
    # baja / media / alta / critica
    tipo_alerta     = Column(String(50), nullable=False)
    # helada / sequia / hongo / viento / inundacion / bateria / etc
    generada_en     = Column(DateTime(timezone=True), server_default=func.now())
    notificada      = Column(Boolean, default=False)
    evento_id       = Column(Integer, nullable=True)


class ReglaAplicada(Base):
    """Registro de reglas de negocio aplicadas."""
    __tablename__ = "regla_aplicada"

    id             = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre_regla   = Column(String(100), nullable=False)
    dispositivo_id = Column(Integer, nullable=False)
    id_logico      = Column(String(50), nullable=False)
    tipo_metrica   = Column(String(50), nullable=False)
    valor          = Column(Float, nullable=False)
    resultado      = Column(String(20), nullable=False)
    # disparada / no_disparada
    detalle        = Column(Text)
    aplicada_en    = Column(DateTime(timezone=True), server_default=func.now())