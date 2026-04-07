from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import HTTPException, status

from app.models.usuario import Usuario, RefreshToken, PerfilUsuario
from app.schemas.usuario import RegistrarUsuario, LoginUsuario, ActualizarPerfil
from app.utils.hashing import hashear_password, verificar_password
from app.utils.jwt import crear_access_token, crear_refresh_token, verificar_refresh_token
from app.config import settings


def registrar_usuario(db: Session, data: RegistrarUsuario, ip: str = None) -> dict:
    """Registra un nuevo usuario en el sistema."""

    if db.query(Usuario).filter(Usuario.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electronico ya esta registrado en el sistema"
        )

    if db.query(Usuario).filter(
        Usuario.numero_documento == data.numero_documento
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El numero de documento ya esta registrado en el sistema"
        )

    usuario = Usuario(
        nombres=data.nombres.strip().title(),
        apellidos=data.apellidos.strip().title(),
        tipo_documento=data.tipo_documento,
        numero_documento=data.numero_documento.strip(),
        email=data.email.lower().strip(),
        telefono=data.telefono.strip(),
        ciudad=data.ciudad.strip().title() if data.ciudad else None,
        departamento=data.departamento.strip().title() if data.departamento else None,
        password_hash=hashear_password(data.password),
        rol="agricultor",
        activo=True,
        email_verificado=False,
        acepta_tratamiento=data.acepta_tratamiento,
        acepta_terminos=data.acepta_terminos,
        fecha_aceptacion=datetime.now(timezone.utc),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    perfil = PerfilUsuario(
        usuario_id=usuario.id,
        parcelas_ids=[],
        sensores_ids=[],
        preferencias={
            "notificaciones_email": True,
            "notificaciones_push":  True,
            "notificaciones_sms":   False,
            "idioma":               "es",
            "zona_horaria":         "America/Bogota",
        },
    )
    db.add(perfil)
    db.commit()

    return {"mensaje": "Usuario registrado exitosamente", "usuario_id": usuario.id}


def login_usuario(db: Session, data: LoginUsuario, ip: str = None) -> dict:
    """Autentica un usuario y retorna tokens JWT."""

    usuario = db.query(Usuario).filter(
        Usuario.email == data.email.lower().strip()
    ).first()

    if not usuario or not verificar_password(data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electronico o contrasena incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada. Contacta al administrador.",
        )

    token_data = {
        "sub":    str(usuario.id),
        "email":  usuario.email,
        "rol":    usuario.rol,
        "nombre": usuario.nombres,
    }
    access_token  = crear_access_token(token_data)
    refresh_token = crear_refresh_token({"sub": str(usuario.id)})

    expira_en = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        usuario_id=usuario.id,
        token=refresh_token,
        activo=True,
        expira_en=expira_en,
        ip_origen=ip,
    )
    db.add(rt)

    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()

    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_type":    "bearer",
        "expires_in":    settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "usuario":       usuario,
    }


def refrescar_token(db: Session, refresh_token: str) -> dict:
    """Genera un nuevo access token usando el refresh token."""

    payload = verificar_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o expirado"
        )

    rt = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.activo == True,
    ).first()

    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no encontrado o ya fue usado"
        )

    # Normalizar timezone para compatibilidad SQLite / PostgreSQL
    expira = rt.expira_en
    if expira.tzinfo is None:
        expira = expira.replace(tzinfo=timezone.utc)

    if expira < datetime.now(timezone.utc):
        rt.activo = False
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expirado. Inicia sesion nuevamente."
        )

    usuario_id = int(payload.get("sub"))
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )

    token_data = {
        "sub":    str(usuario.id),
        "email":  usuario.email,
        "rol":    usuario.rol,
        "nombre": usuario.nombres,
    }
    nuevo_access = crear_access_token(token_data)

    return {
        "access_token": nuevo_access,
        "token_type":   "bearer",
        "expires_in":   settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def logout_usuario(db: Session, refresh_token: str) -> dict:
    """Invalida el refresh token del usuario."""
    rt = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.activo == True,
    ).first()
    if rt:
        rt.activo = False
        db.commit()
    return {"mensaje": "Sesion cerrada correctamente"}


def obtener_usuario_por_id(db: Session, usuario_id: int) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


def actualizar_perfil(db: Session, usuario_id: int, data: ActualizarPerfil) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    datos = data.model_dump(exclude_unset=True)
    for campo, valor in datos.items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return usuario


def cambiar_password(db: Session, usuario_id: int, password_actual: str, password_nuevo: str) -> dict:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verificar_password(password_actual, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contrasena actual es incorrecta"
        )

    usuario.password_hash = hashear_password(password_nuevo)
    db.commit()
    return {"mensaje": "Contrasena actualizada correctamente"}


def obtener_perfil_usuario(db: Session, usuario_id: int) -> PerfilUsuario:
    perfil = db.query(PerfilUsuario).filter(
        PerfilUsuario.usuario_id == usuario_id
    ).first()
    if not perfil:
        perfil = PerfilUsuario(
            usuario_id=usuario_id,
            parcelas_ids=[],
            sensores_ids=[],
            preferencias={},
        )
        db.add(perfil)
        db.commit()
        db.refresh(perfil)
    return perfil


def actualizar_perfil_usuario(db: Session, usuario_id: int, data: dict) -> PerfilUsuario:
    perfil = obtener_perfil_usuario(db, usuario_id)
    if "parcelas_ids" in data and data["parcelas_ids"] is not None:
        perfil.parcelas_ids = data["parcelas_ids"]
    if "sensores_ids" in data and data["sensores_ids"] is not None:
        perfil.sensores_ids = data["sensores_ids"]
    if "preferencias" in data and data["preferencias"] is not None:
        perfil.preferencias = {**perfil.preferencias, **data["preferencias"]}
    db.commit()
    db.refresh(perfil)
    return perfil


def listar_usuarios(db: Session, rol: str = None, activo: bool = None) -> list:
    query = db.query(Usuario)
    if rol:
        query = query.filter(Usuario.rol == rol)
    if activo is not None:
        query = query.filter(Usuario.activo == activo)
    return query.order_by(Usuario.creado_en.desc()).all()


def activar_desactivar_usuario(db: Session, usuario_id: int, activo: bool) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    usuario.activo = activo
    db.commit()
    db.refresh(usuario)
    return usuario