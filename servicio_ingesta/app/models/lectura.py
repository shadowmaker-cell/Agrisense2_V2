from sqlalchemy import (
    Column, Integer, String, DateTime,
    Float, ForeignKey, Text, BigInteger
)
from sqlalchemy.sql import func
from app.database import Base


class LoteIngesta(Base):
    """Registro de lotes de lecturas recibidas."""
    __tablename__ = "lote_ingesta"

    id                  = Column(Integer, primary_key=True, autoincrement=True, index=True)
    tipo_origen         = Column(String(10), nullable=False)
    recibido_en         = Column(DateTime(timezone=True), server_default=func.now())
    total_registros     = Column(Integer, default=0)
    registros_validos   = Column(Integer, default=0)
    registros_invalidos = Column(Integer, default=0)
    estado              = Column(String(20), default="procesado")


class LecturaSensor(Base):
    """
    Tabla principal de lecturas de sensores.
    Optimizada para TimescaleDB como hypertable por timestamp.
    """
    __tablename__ = "lectura_sensor"

    id                = Column(Integer, primary_key=True, autoincrement=True, index=True)
    dispositivo_id    = Column(Integer, nullable=False, index=True)
    id_logico         = Column(String(50), nullable=False, index=True)
    tipo_metrica      = Column(String(50), nullable=False)
    valor_metrica     = Column(Float, nullable=False)
    unidad            = Column(String(20))
    timestamp_lectura = Column(DateTime(timezone=True), nullable=False, index=True)
    recibido_en       = Column(DateTime(timezone=True), server_default=func.now())
    bandera_calidad   = Column(String(10), default="valido")
    lote_id           = Column(Integer, ForeignKey("lote_ingesta.id"), nullable=True)


class ErrorIngesta(Base):
    """Registro de errores de validación en lecturas."""
    __tablename__ = "error_ingesta"

    id          = Column(Integer, primary_key=True, autoincrement=True, index=True)
    lote_id     = Column(Integer, ForeignKey("lote_ingesta.id"), nullable=True)
    payload_raw = Column(Text)
    razon_error = Column(String(255), nullable=False)
    creado_en   = Column(DateTime(timezone=True), server_default=func.now())


class AlertaGenerada(Base):
    """Alertas detectadas automáticamente durante la ingesta."""
    __tablename__ = "alerta_generada"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    dispositivo_id  = Column(Integer, nullable=False, index=True)
    id_logico       = Column(String(50), nullable=False)
    tipo_metrica    = Column(String(50), nullable=False)
    valor_detectado = Column(Float, nullable=False)
    condicion       = Column(String(255), nullable=False)
    severidad       = Column(String(20), default="media")
    generada_en     = Column(DateTime(timezone=True), server_default=func.now())
    enviada         = Column(String(5), default="no")