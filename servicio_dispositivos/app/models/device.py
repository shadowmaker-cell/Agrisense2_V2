from sqlalchemy import (
    Column, Integer, String, DateTime,
    SmallInteger, ForeignKey, CheckConstraint, Float, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TipoDispositivo(Base):
    """Tipos de sensor predefinidos — solo lectura para el usuario."""
    __tablename__ = "tipo_dispositivo"

    id                  = Column(Integer, primary_key=True, index=True)
    nombre              = Column(String(100), nullable=False, unique=True)
    categoria           = Column(String(50), nullable=False)
    
    unidad              = Column(String(30))
    rango_minimo        = Column(Float)
    rango_maximo        = Column(Float)
    umbral_alerta       = Column(String(100))
    tipo_pin            = Column(String(50))
    metricas_permitidas = Column(JSON, nullable=False, default=list)
    


class Dispositivo(Base):
    """Inventario de sensores registrados."""
    __tablename__ = "dispositivo"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('activo','inactivo','mantenimiento','averiado')",
            name="ck_dispositivo_estado"
        ),
    )

    id                  = Column(Integer, primary_key=True, index=True)
    usuario_id          = Column(Integer, nullable=True, index=True)
    # NULL = dato global/admin, entero = pertenece a ese usuario
    tipo_dispositivo_id = Column(Integer, ForeignKey("tipo_dispositivo.id"), nullable=False)
    id_logico           = Column(String(50), unique=True, nullable=False)
    numero_serial       = Column(String(100), nullable=False, unique=True)
    version_firmware    = Column(String(50))
    estado              = Column(String(20), default="activo")
    registrado_en       = Column(DateTime(timezone=True), server_default=func.now())
    ultima_conexion     = Column(DateTime(timezone=True))

    tipo_dispositivo  = relationship("TipoDispositivo")
    configuracion     = relationship("ConfiguracionDispositivo",
                                     back_populates="dispositivo", uselist=False)
    historial_estados = relationship("HistorialEstadoDispositivo",
                                     back_populates="dispositivo")
    despliegues       = relationship("DespliegueDispositivo",
                                     foreign_keys="DespliegueDispositivo.dispositivo_id",
                                     back_populates="dispositivo")

class ConfiguracionDispositivo(Base):
    """Parametros tecnicos del sensor — editables por el usuario."""
    __tablename__ = "configuracion_dispositivo"

    id                     = Column(Integer, primary_key=True, index=True)
    dispositivo_id         = Column(Integer, ForeignKey("dispositivo.id"),
                                    nullable=False, unique=True)
    intervalo_muestreo     = Column(Integer, default=300)
    protocolo_transmision  = Column(String(10), default="HTTP")
    umbral_bateria         = Column(SmallInteger, default=20)
    # Limites personalizados por sensor
    limite_minimo          = Column(Float, nullable=True)
    limite_maximo          = Column(Float, nullable=True)
    # Parcela asignada
    parcela_id             = Column(Integer, nullable=True)
    parcela_nombre         = Column(String(100), nullable=True)
    posicion_campo         = Column(String(100), nullable=True)
    actualizado_en         = Column(DateTime(timezone=True), onupdate=func.now())

    dispositivo = relationship("Dispositivo", back_populates="configuracion")


class HistorialEstadoDispositivo(Base):
    """Historial de cambios de estado — solo lectura."""
    __tablename__ = "historial_estado_dispositivo"

    id               = Column(Integer, primary_key=True, index=True)
    dispositivo_id   = Column(Integer, ForeignKey("dispositivo.id"), nullable=False)
    estado_anterior  = Column(String(20))
    estado_nuevo     = Column(String(20), nullable=False)
    cambiado_en      = Column(DateTime(timezone=True), server_default=func.now())

    dispositivo = relationship("Dispositivo", back_populates="historial_estados")


class DespliegueDispositivo(Base):
    """Registro de dónde y cuándo está instalado cada sensor en el huerto."""
    __tablename__ = "despliegue_dispositivo"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('activo','retirado','mantenimiento','averiado')",
            name="ck_despliegue_estado"
        ),
    )

    id               = Column(Integer, primary_key=True, index=True)
    dispositivo_id   = Column(Integer, ForeignKey("dispositivo.id"), nullable=False)

    
    lote_id          = Column(String(50), nullable=False)
    
    posicion         = Column(String(100))
    

    
    instalado_en     = Column(DateTime(timezone=True), server_default=func.now())
    retirado_en      = Column(DateTime(timezone=True), nullable=True)
  

   
    estado           = Column(String(20), default="activo")
    motivo_retiro    = Column(String(200), nullable=True)
   
    
    reemplazado_por  = Column(Integer, ForeignKey("dispositivo.id"), nullable=True)
    

    dispositivo = relationship("Dispositivo", foreign_keys=[dispositivo_id],
                               back_populates="despliegues")
    reemplazo   = relationship("Dispositivo", foreign_keys=[reemplazado_por])