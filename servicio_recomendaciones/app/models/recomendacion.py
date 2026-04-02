from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class CategoriaRecomendacion(Base):
    """Catalogo de categorias de recomendaciones agronomicas."""
    __tablename__ = "categoria_recomendacion"

    id          = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre      = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    icono       = Column(String(10), nullable=True)
    activo      = Column(Boolean, default=True)
    creado_en   = Column(DateTime(timezone=True), server_default=func.now())

    recomendaciones = relationship("Recomendacion", back_populates="categoria")


class Recomendacion(Base):
    """Recomendacion agronomica generada para una parcela o sensor."""
    __tablename__ = "recomendacion"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    categoria_id    = Column(Integer, ForeignKey("categoria_recomendacion.id"), nullable=False)
    parcela_id      = Column(Integer, nullable=True, index=True)
    id_logico       = Column(String(50), nullable=True, index=True)
    titulo          = Column(String(200), nullable=False)
    descripcion     = Column(Text, nullable=False)
    accion          = Column(Text, nullable=False)
    prioridad       = Column(String(20), default="media")
    # baja | media | alta | critica
    estado          = Column(String(20), default="activa")
    # activa | aplicada | descartada | vencida
    fuente          = Column(String(50), nullable=True)
    # ml | alerta | regla | manual
    datos_contexto  = Column(JSON, nullable=True)
    valida_hasta    = Column(DateTime(timezone=True), nullable=True)
    generada_en     = Column(DateTime(timezone=True), server_default=func.now())
    actualizada_en  = Column(DateTime(timezone=True), onupdate=func.now())

    categoria       = relationship("CategoriaRecomendacion", back_populates="recomendaciones")
    evidencias      = relationship("EvidenciaRecomendacion", back_populates="recomendacion", cascade="all, delete-orphan")


class EvidenciaRecomendacion(Base):
    """Evidencia que justifica una recomendacion."""
    __tablename__ = "evidencia_recomendacion"

    id                  = Column(Integer, primary_key=True, autoincrement=True, index=True)
    recomendacion_id    = Column(Integer, ForeignKey("recomendacion.id"), nullable=False)
    tipo_fuente         = Column(String(50), nullable=False)
    # alerta | prediccion_ml | lectura | historial
    descripcion         = Column(Text, nullable=False)
    valor_observado     = Column(Float, nullable=True)
    valor_esperado      = Column(Float, nullable=True)
    unidad              = Column(String(30), nullable=True)
    creado_en           = Column(DateTime(timezone=True), server_default=func.now())

    recomendacion       = relationship("Recomendacion", back_populates="evidencias")


class EjecucionRecomendacion(Base):
    """Registro de cada ejecucion del motor de recomendaciones."""
    __tablename__ = "ejecucion_recomendacion"

    id                      = Column(Integer, primary_key=True, autoincrement=True, index=True)
    parcela_id              = Column(Integer, nullable=True)
    id_logico               = Column(String(50), nullable=True)
    total_recomendaciones   = Column(Integer, default=0)
    criticas                = Column(Integer, default=0)
    altas                   = Column(Integer, default=0)
    medias                  = Column(Integer, default=0)
    bajas                   = Column(Integer, default=0)
    fuentes_consultadas     = Column(JSON, nullable=True)
    ejecutado_en            = Column(DateTime(timezone=True), server_default=func.now())