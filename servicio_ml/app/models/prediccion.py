from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ModeloRegistro(Base):
    """Registro de modelos ML entrenados disponibles."""
    __tablename__ = "modelo_registro"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nombre          = Column(String(100), nullable=False)
    version         = Column(String(20), nullable=False, default="1.0.0")
    tipo            = Column(String(50), nullable=False)
    # agua | rendimiento | riesgo_helada | riesgo_sequia | riesgo_plaga
    descripcion     = Column(Text, nullable=True)
    variable_target = Column(String(100), nullable=False)
    features        = Column(JSON, nullable=True)
    metricas        = Column(JSON, nullable=True)
    # {"mae": 0.12, "rmse": 0.18, "r2": 0.87}
    estado          = Column(String(20), default="activo")
    # activo | deprecated | entrenando
    registrado_en   = Column(DateTime(timezone=True), server_default=func.now())

    predicciones    = relationship("SolicitudPrediccion", back_populates="modelo")


class SolicitudPrediccion(Base):
    """Solicitud de prediccion enviada al servicio ML."""
    __tablename__ = "solicitud_prediccion"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    modelo_id       = Column(Integer, ForeignKey("modelo_registro.id"), nullable=False)
    parcela_id      = Column(Integer, nullable=True)
    id_logico       = Column(String(50), nullable=True)
    tipo_prediccion = Column(String(50), nullable=False)
    datos_entrada   = Column(JSON, nullable=False)
    estado          = Column(String(20), default="pendiente")
    # pendiente | procesando | completado | fallido
    solicitado_en   = Column(DateTime(timezone=True), server_default=func.now())

    modelo          = relationship("ModeloRegistro", back_populates="predicciones")
    resultado       = relationship("ResultadoPrediccion", back_populates="solicitud", uselist=False)


class ResultadoPrediccion(Base):
    """Resultado generado por el modelo ML."""
    __tablename__ = "resultado_prediccion"

    id                  = Column(Integer, primary_key=True, autoincrement=True, index=True)
    solicitud_id        = Column(Integer, ForeignKey("solicitud_prediccion.id"), nullable=False)
    valor_predicho      = Column(Float, nullable=False)
    confianza           = Column(Float, nullable=True)
    # 0.0 - 1.0
    unidad              = Column(String(30), nullable=True)
    explicacion         = Column(Text, nullable=True)
    datos_salida        = Column(JSON, nullable=True)
    generado_en         = Column(DateTime(timezone=True), server_default=func.now())

    solicitud           = relationship("SolicitudPrediccion", back_populates="resultado")


class HistorialMetrica(Base):
    """Historial de metricas de sensores para entrenamiento de modelos."""
    __tablename__ = "historial_metrica"

    id              = Column(Integer, primary_key=True, autoincrement=True, index=True)
    id_logico       = Column(String(50), nullable=False, index=True)
    parcela_id      = Column(Integer, nullable=True, index=True)
    tipo_metrica    = Column(String(50), nullable=False)
    valor           = Column(Float, nullable=False)
    timestamp       = Column(DateTime(timezone=True), nullable=False)
    registrado_en   = Column(DateTime(timezone=True), server_default=func.now())