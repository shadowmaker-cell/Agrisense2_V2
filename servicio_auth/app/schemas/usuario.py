from pydantic import BaseModel, Field, EmailStr, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


class TipoDocumento(str, Enum):
    CC  = "CC"   # Cedula de ciudadania
    CE  = "CE"   # Cedula de extranjeria
    NIT = "NIT"  # NIT empresarial
    PA  = "PA"   # Pasaporte
    TI  = "TI"   # Tarjeta de identidad


class RolUsuario(str, Enum):
    agricultor     = "agricultor"
    administrador  = "administrador"


# ── Registro ──────────────────────────────────────────
class RegistrarUsuario(BaseModel):
    nombres:             str = Field(..., min_length=2, max_length=100,
                                     description="Nombres completos del usuario")
    apellidos:           str = Field(..., min_length=2, max_length=100,
                                     description="Apellidos completos del usuario")
    tipo_documento:      TipoDocumento = TipoDocumento.CC
    numero_documento:    str = Field(..., min_length=5, max_length=20,
                                     description="Numero de documento de identidad")
    email:               EmailStr = Field(..., description="Correo electronico valido")
    telefono:            str = Field(..., min_length=10, max_length=15,
                                     description="Numero celular colombiano — 10 digitos")
    ciudad:              Optional[str] = Field(None, max_length=100)
    departamento:        Optional[str] = Field(None, max_length=100)
    password:            str = Field(..., min_length=8, max_length=100,
                                     description="Contrasena — minimo 8 caracteres")
    confirmar_password:  str = Field(..., description="Confirmar contrasena")
    acepta_tratamiento:  bool = Field(..., description="Acepta tratamiento de datos Ley 1581/2012")
    acepta_terminos:     bool = Field(..., description="Acepta terminos y condiciones")

    @model_validator(mode="after")
    def validar_campos(self):
        # Verificar que las contrasenas coincidan
        if self.password != self.confirmar_password:
            raise ValueError("Las contrasenas no coinciden")

        # Politica de contrasena segura
        password = self.password
        if not any(c.isupper() for c in password):
            raise ValueError("La contrasena debe tener al menos una letra mayuscula")
        if not any(c.islower() for c in password):
            raise ValueError("La contrasena debe tener al menos una letra minuscula")
        if not any(c.isdigit() for c in password):
            raise ValueError("La contrasena debe tener al menos un numero")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise ValueError("La contrasena debe tener al menos un caracter especial (!@#$%...)")

        # Formato telefono colombiano
        tel = re.sub(r'\s+', '', self.telefono)
        if not re.match(r'^(\+57)?[3][0-9]{9}$', tel):
            raise ValueError("Telefono invalido — debe ser un celular colombiano de 10 digitos (ej: 3001234567)")

        # Documento solo numeros (excepto pasaporte)
        if self.tipo_documento != TipoDocumento.PA:
            doc = re.sub(r'[.\s-]', '', self.numero_documento)
            if not doc.isdigit():
                raise ValueError("El numero de documento solo debe contener digitos")

        # Aceptacion obligatoria Ley 1581
        if not self.acepta_tratamiento:
            raise ValueError("Debe aceptar el tratamiento de datos personales segun la Ley 1581 de 2012")
        if not self.acepta_terminos:
            raise ValueError("Debe aceptar los terminos y condiciones del servicio")

        return self


# ── Login ─────────────────────────────────────────────
class LoginUsuario(BaseModel):
    email:    EmailStr
    password: str


# ── Refresh token ─────────────────────────────────────
class RefreshTokenEntrada(BaseModel):
    refresh_token: str


# ── Cambiar contrasena ────────────────────────────────
class CambiarPassword(BaseModel):
    password_actual:    str
    password_nuevo:     str = Field(..., min_length=8)
    confirmar_password: str

    @model_validator(mode="after")
    def validar_passwords(self):
        if self.password_nuevo != self.confirmar_password:
            raise ValueError("Las contrasenas no coinciden")
        password = self.password_nuevo
        if not any(c.isupper() for c in password):
            raise ValueError("La contrasena debe tener al menos una letra mayuscula")
        if not any(c.islower() for c in password):
            raise ValueError("La contrasena debe tener al menos una letra minuscula")
        if not any(c.isdigit() for c in password):
            raise ValueError("La contrasena debe tener al menos un numero")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise ValueError("La contrasena debe tener al menos un caracter especial")
        return self


# ── Actualizar perfil ─────────────────────────────────
class ActualizarPerfil(BaseModel):
    nombres:      Optional[str] = Field(None, min_length=2, max_length=100)
    apellidos:    Optional[str] = Field(None, min_length=2, max_length=100)
    telefono:     Optional[str] = None
    ciudad:       Optional[str] = None
    departamento: Optional[str] = None


# ── Respuestas ────────────────────────────────────────
class RespuestaUsuario(BaseModel):
    id:               int
    nombres:          str
    apellidos:        str
    email:            str
    tipo_documento:   str
    numero_documento: str
    telefono:         Optional[str]
    rol:              str
    activo:           bool
    ciudad:           Optional[str]
    departamento:     Optional[str]
    creado_en:        datetime
    ultimo_login:     Optional[datetime]

    model_config = {"from_attributes": True}


class RespuestaToken(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int
    usuario:       RespuestaUsuario


class RespuestaRefresh(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int


# ── Perfil ────────────────────────────────────────────
class RespuestaPerfilUsuario(BaseModel):
    usuario_id:   int
    parcelas_ids: List[int]
    sensores_ids: List[str]
    preferencias: dict

    model_config = {"from_attributes": True}


class ActualizarPerfilUsuario(BaseModel):
    parcelas_ids: Optional[List[int]]  = None
    sensores_ids: Optional[List[str]]  = None
    preferencias: Optional[dict]       = None