from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.usuario import (
    RegistrarUsuario, LoginUsuario, RefreshTokenEntrada,
    RespuestaToken, RespuestaRefresh, CambiarPassword,
)
from app.services.auth_service import (
    registrar_usuario, login_usuario,
    refrescar_token, logout_usuario, cambiar_password,
)
from app.utils.jwt import verificar_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticacion"])


def get_current_user_id(request: Request) -> int:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    token = auth.split(" ")[1]
    payload = verificar_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    return int(payload.get("sub"))


# ── Health ────────────────────────────────────────────
@router.get("/health")
def health():
    return {
        "estado":   "ok",
        "servicio": "auth-service",
        "version":  "1.0.0",
    }


# ── Registro ──────────────────────────────────────────
@router.post("/registro", status_code=201)
def registro(
    payload: RegistrarUsuario,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en AgriSense.
    Cumple con la Ley 1581 de 2012 — Habeas Data Colombia.
    Requiere aceptacion de tratamiento de datos y terminos.
    """
    ip = request.client.host if request.client else None
    return registrar_usuario(db, payload, ip)


# ── Login ─────────────────────────────────────────────
@router.post("/login", response_model=RespuestaToken)
def login(
    payload: LoginUsuario,
    request: Request,
    db: Session = Depends(get_db)
):
    """Autentica al usuario y retorna access token + refresh token."""
    ip = request.client.host if request.client else None
    return login_usuario(db, payload, ip)


# ── Refresh ───────────────────────────────────────────
@router.post("/refresh", response_model=RespuestaRefresh)
def refresh(
    payload: RefreshTokenEntrada,
    db: Session = Depends(get_db)
):
    """Genera un nuevo access token usando el refresh token."""
    return refrescar_token(db, payload.refresh_token)


# ── Logout ────────────────────────────────────────────
@router.post("/logout")
def logout(
    payload: RefreshTokenEntrada,
    db: Session = Depends(get_db)
):
    """Cierra la sesion invalidando el refresh token."""
    return logout_usuario(db, payload.refresh_token)


# ── Cambiar contrasena ────────────────────────────────
@router.put("/cambiar-password")
def cambiar_pwd(
    payload: CambiarPassword,
    request: Request,
    db: Session = Depends(get_db)
):
    """Cambia la contrasena del usuario autenticado."""
    usuario_id = get_current_user_id(request)
    return cambiar_password(
        db, usuario_id,
        payload.password_actual,
        payload.password_nuevo,
    )


# ── Verificar token ───────────────────────────────────
@router.get("/verificar")
def verificar_token(request: Request):
    """Verifica si el access token es valido. Usado por microservicios."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    token = auth.split(" ")[1]
    payload = verificar_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    return {
        "valido":     True,
        "usuario_id": int(payload.get("sub")),
        "email":      payload.get("email"),
        "rol":        payload.get("rol"),
        "nombre":     payload.get("nombre"),
    }