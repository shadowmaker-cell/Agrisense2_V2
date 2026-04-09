from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    RespuestaUsuario,
    ActualizarPerfil,
    RespuestaPerfilUsuario,
    ActualizarPerfilUsuario,
)
from app.services.auth_service import (
    obtener_usuario_por_id,
    obtener_perfil_usuario,
    actualizar_perfil_usuario,
)
from app.utils.jwt import verificar_access_token

router = APIRouter(prefix="/api/v1/usuarios", tags=["usuarios"])


def get_usuario_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token   = auth.split(" ")[1]
    payload = verificar_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido")
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Token invalido")
    return int(uid)


def require_admin(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token   = auth.split(" ")[1]
    payload = verificar_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido")
    if payload.get("rol") != "administrador":
        raise HTTPException(status_code=403, detail="Se requiere rol administrador")


# ── Perfil propio ─────────────────────────────────────
@router.get("/me", response_model=RespuestaUsuario)
def obtener_mi_perfil(request: Request, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id(request)
    usuario    = obtener_usuario_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/me", response_model=RespuestaUsuario)
def actualizar_mi_perfil(
    payload: ActualizarPerfil,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    usuario    = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    datos = payload.model_dump(exclude_unset=True)
    for key, val in datos.items():
        if val is not None:
            setattr(usuario, key, val)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("/me/perfil", response_model=RespuestaPerfilUsuario)
def obtener_mi_perfil_iot(request: Request, db: Session = Depends(get_db)):
    usuario_id = get_usuario_id(request)
    return obtener_perfil_usuario(db, usuario_id)


@router.put("/me/perfil", response_model=RespuestaPerfilUsuario)
def actualizar_mi_perfil_iot(
    payload: ActualizarPerfilUsuario,
    request: Request,
    db: Session = Depends(get_db)
):
    usuario_id = get_usuario_id(request)
    return actualizar_perfil_usuario(db, usuario_id, payload.model_dump(exclude_unset=True))


# ── Admin ─────────────────────────────────────────────
@router.get("/", response_model=list[RespuestaUsuario])
def listar_usuarios(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    return db.query(Usuario).all()


@router.get("/{usuario_id}/perfil", response_model=RespuestaPerfilUsuario)
def obtener_perfil_iot(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    require_admin(request)
    return obtener_perfil_usuario(db, usuario_id)


@router.put("/{usuario_id}/perfil")
def actualizar_perfil_iot(
    usuario_id: int,
    payload: ActualizarPerfilUsuario,
    request: Request,
    db: Session = Depends(get_db)
):
    require_admin(request)
    return actualizar_perfil_usuario(db, usuario_id, payload.model_dump(exclude_unset=True))


# ── Endpoint interno para notificaciones ──────────────
@router.get("/{usuario_id}/email")
def obtener_email(usuario_id: int, db: Session = Depends(get_db)):
    """Endpoint interno — obtiene email de usuario por ID."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"email": usuario.email, "usuario_id": usuario_id}