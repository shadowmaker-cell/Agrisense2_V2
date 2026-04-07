from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.usuario import (
    RespuestaUsuario, ActualizarPerfil,
    RespuestaPerfilUsuario, ActualizarPerfilUsuario,
)
from app.services.auth_service import (
    obtener_usuario_por_id, actualizar_perfil,
    obtener_perfil_usuario, actualizar_perfil_usuario,
    listar_usuarios, activar_desactivar_usuario,
)
from app.utils.jwt import verificar_access_token

router = APIRouter(prefix="/api/v1/usuarios", tags=["Usuarios"])


def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    token = auth.split(" ")[1]
    payload = verificar_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    usuario = obtener_usuario_por_id(db, int(payload.get("sub")))
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")
    return usuario


def require_admin(request: Request, db: Session = Depends(get_db)):
    usuario = get_current_user(request, db)
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=403,
            detail="Solo los administradores pueden realizar esta accion"
        )
    return usuario


# ── Perfil propio ─────────────────────────────────────
@router.get("/me", response_model=RespuestaUsuario)
def obtener_mi_perfil(
    request: Request,
    db: Session = Depends(get_db)
):
    """Retorna los datos del usuario autenticado."""
    return get_current_user(request, db)


@router.put("/me", response_model=RespuestaUsuario)
def actualizar_mi_perfil(
    payload: ActualizarPerfil,
    request: Request,
    db: Session = Depends(get_db)
):
    """Actualiza nombre, apellido, telefono, ciudad y departamento."""
    usuario = get_current_user(request, db)
    return actualizar_perfil(db, usuario.id, payload)


# ── Perfil IoT del usuario ────────────────────────────
@router.get("/me/perfil", response_model=RespuestaPerfilUsuario)
def obtener_mi_perfil_iot(
    request: Request,
    db: Session = Depends(get_db)
):
    """Retorna las parcelas y sensores asignados al usuario."""
    usuario = get_current_user(request, db)
    return obtener_perfil_usuario(db, usuario.id)


@router.put("/me/perfil")
def actualizar_mi_perfil_iot(
    payload: ActualizarPerfilUsuario,
    request: Request,
    db: Session = Depends(get_db)
):
    """Actualiza parcelas, sensores y preferencias del usuario."""
    usuario = get_current_user(request, db)
    return actualizar_perfil_usuario(db, usuario.id, payload.model_dump(exclude_unset=True))


# ── Admin — gestión de usuarios ───────────────────────
@router.get("/", response_model=List[RespuestaUsuario])
def listar_todos(
    rol:    Optional[str]  = None,
    activo: Optional[bool] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Lista todos los usuarios. Solo administradores."""
    require_admin(request, db)
    return listar_usuarios(db, rol, activo)


@router.get("/{usuario_id}", response_model=RespuestaUsuario)
def obtener_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Obtiene un usuario por ID. Solo administradores."""
    require_admin(request, db)
    return obtener_usuario_por_id(db, usuario_id)


@router.put("/{usuario_id}/activar")
def activar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Activa una cuenta de usuario. Solo administradores."""
    require_admin(request, db)
    return activar_desactivar_usuario(db, usuario_id, True)


@router.put("/{usuario_id}/desactivar")
def desactivar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Desactiva una cuenta de usuario. Solo administradores."""
    require_admin(request, db)
    return activar_desactivar_usuario(db, usuario_id, False)


@router.get("/{usuario_id}/perfil", response_model=RespuestaPerfilUsuario)
def obtener_perfil_iot(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Perfil IoT de un usuario especifico. Solo administradores."""
    require_admin(request, db)
    return obtener_perfil_usuario(db, usuario_id)


@router.put("/{usuario_id}/perfil")
def actualizar_perfil_iot(
    usuario_id: int,
    payload: ActualizarPerfilUsuario,
    request: Request,
    db: Session = Depends(get_db)
):
    """Asigna parcelas y sensores a un usuario. Solo administradores."""
    require_admin(request, db)
    return actualizar_perfil_usuario(db, usuario_id, payload.model_dump(exclude_unset=True))