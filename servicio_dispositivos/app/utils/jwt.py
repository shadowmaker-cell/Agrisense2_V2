from jose import JWTError, jwt
from fastapi import Request, HTTPException
import os

JWT_SECRET    = os.getenv("JWT_SECRET", "agrisense_jwt_secret_2026")
JWT_ALGORITHM = "HS256"


def get_usuario_id(request: Request) -> int:
    """Extrae el usuario_id del JWT. Lanza 401 si no hay token valido."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    token = auth.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        uid = payload.get("sub")
        if not uid:
            raise HTTPException(status_code=401, detail="Token invalido")
        return int(uid)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")


def get_usuario_id_opcional(request: Request) -> int | None:
    """Extrae el usuario_id del JWT. Retorna None si no hay token."""
    try:
        return get_usuario_id(request)
    except HTTPException:
        return None