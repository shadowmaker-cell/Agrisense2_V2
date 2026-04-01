from sqlalchemy import (
    Column, Integer, String, DateTime,
    Float, Text, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TipoCultivo(Base):
    """Catalogo de tipos de cultivo."""
    __tablename__ = "tipo_cultivo"

    id          = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre      = Column(String(100), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    temporada   = Column(String(50), nullable=True)
    # primavera / verano / otono / invierno / todo_anio
    activo      = Column(Boolean, default=True)
    creado_en   = Column(DateTime(timezone=True), server_default=func.now())

    historial   = relationship("HistorialCultivo", back_populates="tipo_cultivo")


class Parcela(Base):
    """Parcela agricola con informacion geografica basica."""
    __tablename__ = "parcela"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre          = Column(String(100), nullable=False)
    descripcion     = Column(Text, nullable=True)
    area_hectareas  = Column(Float, nullable=False)
    tipo_suelo      = Column(String(50), nullable=True)
    # arcilloso / arenoso / limoso / franco / otro
    latitud         = Column(Float, nullable=True)
    longitud        = Column(Float, nullable=True)
    altitud_msnm    = Column(Float, nullable=True)
    departamento    = Column(String(100), nullable=True)
    municipio       = Column(String(100), nullable=True)
    vereda          = Column(String(100), nullable=True)
    estado          = Column(String(20), default='activa')
    # activa / inactiva / en_preparacion
    propietario_id  = Column(Integer, nullable=True)
    creada_en       = Column(DateTime(timezone=True), server_default=func.now())
    actualizada_en  = Column(DateTime(timezone=True), onupdate=func.now())

    sensores        = relationship("ParcelaSensor",    back_populates="parcela", cascade="all, delete-orphan")
    historial       = relationship("HistorialCultivo", back_populates="parcela", cascade="all, delete-orphan")


class ParcelaSensor(Base):
    """Asignacion de sensores IoT a parcelas."""
    __tablename__ = "parcela_sensor"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    parcela_id      = Column(Integer, ForeignKey("parcela.id"), nullable=False, index=True)
    dispositivo_id  = Column(Integer, nullable=False)
    id_logico       = Column(String(50), nullable=False, index=True)
    # Referencia externa al servicio de dispositivos
    fecha_instalacion = Column(DateTime(timezone=True), server_default=func.now())
    activo          = Column(Boolean, default=True)
    notas           = Column(Text, nullable=True)

    parcela         = relationship("Parcela", back_populates="sensores")


class HistorialCultivo(Base):
    """Historial de cultivos por parcela."""
    __tablename__ = "historial_cultivo"

    id                  = Column(Integer, primary_key=True, autoincrement=True, index=True)
    parcela_id          = Column(Integer, ForeignKey("parcela.id"), nullable=False, index=True)
    tipo_cultivo_id     = Column(Integer, ForeignKey("tipo_cultivo.id"), nullable=False)
    fecha_siembra       = Column(DateTime(timezone=True), nullable=False)
    fecha_cosecha       = Column(DateTime(timezone=True), nullable=True)
    etapa_fenologica    = Column(String(50), nullable=True)
    # germinacion / vegetativo / floracion / fructificacion / maduracion / cosecha
    rendimiento_kg      = Column(Float, nullable=True)
    observaciones       = Column(Text, nullable=True)
    estado              = Column(String(20), default='activo')
    # activo / finalizado / perdido
    creado_en           = Column(DateTime(timezone=True), server_default=func.now())

    parcela             = relationship("Parcela",      back_populates="historial")
    tipo_cultivo        = relationship("TipoCultivo",  back_populates="historial")