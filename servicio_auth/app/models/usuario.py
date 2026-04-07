from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class Usuario(Base):
    """Usuarios del sistema AgriSense — normativa colombiana Ley 1581 de 2012."""
    __tablename__ = "usuario"

    id                  = Column(Integer, primary_key=True, autoincrement=True, index=True)
    # Datos personales
    nombres             = Column(String(100), nullable=False)
    apellidos           = Column(String(100), nullable=False)
    tipo_documento      = Column(String(10), nullable=False, default="CC")
    # CC | CE | NIT | PA | TI
    numero_documento    = Column(String(20), nullable=False, unique=True, index=True)
    email               = Column(String(200), nullable=False, unique=True, index=True)
    telefono            = Column(String(15), nullable=True)
    # Formato colombiano: 10 digitos, ej: 3001234567
    # Autenticacion
    password_hash       = Column(String(255), nullable=False)
    # Rol y estado
    rol                 = Column(String(20), default="agricultor")
    # agricultor | administrador
    activo              = Column(Boolean, default=True)
    email_verificado    = Column(Boolean, default=False)
    # Ubicacion
    ciudad              = Column(String(100), nullable=True)
    departamento        = Column(String(100), nullable=True)
    # Cumplimiento Ley 1581 de 2012 — Habeas Data
    acepta_tratamiento  = Column(Boolean, nullable=False, default=False)
    # Debe ser True para registrarse
    acepta_terminos     = Column(Boolean, nullable=False, default=False)
    fecha_aceptacion    = Column(DateTime(timezone=True), nullable=True)
    # Auditoria
    creado_en           = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en      = Column(DateTime(timezone=True), onupdate=func.now())
    ultimo_login        = Column(DateTime(timezone=True), nullable=True)


class RefreshToken(Base):
    """Tokens de refresco para renovacion de sesion."""
    __tablename__ = "refresh_token"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id  = Column(Integer, nullable=False, index=True)
    token       = Column(String(500), nullable=False, unique=True)
    activo      = Column(Boolean, default=True)
    expira_en   = Column(DateTime(timezone=True), nullable=False)
    creado_en   = Column(DateTime(timezone=True), server_default=func.now())
    ip_origen   = Column(String(50), nullable=True)
    user_agent  = Column(String(255), nullable=True)


class PerfilUsuario(Base):
    """Perfil extendido del agricultor — parcelas y sensores asignados."""
    __tablename__ = "perfil_usuario"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id      = Column(Integer, nullable=False, unique=True, index=True)
    parcelas_ids    = Column(JSON, default=list)
    sensores_ids    = Column(JSON, default=list)
    preferencias    = Column(JSON, default=dict)
    notas           = Column(Text, nullable=True)
    actualizado_en  = Column(DateTime(timezone=True), onupdate=func.now())