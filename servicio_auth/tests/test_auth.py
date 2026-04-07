import os
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

SQLALCHEMY_TEST_URL = "sqlite:///./test_auth.db"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False}
)
SesionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = SesionTest()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


client = TestClient(app)

USUARIO_VALIDO = {
    "nombres":            "Juan Carlos",
    "apellidos":          "Rodriguez Perez",
    "tipo_documento":     "CC",
    "numero_documento":   "1234567890",
    "email":              "juan@agrisense.co",
    "telefono":           "3001234567",
    "ciudad":             "Medellin",
    "departamento":       "Antioquia",
    "password":           "Agri$2026",
    "confirmar_password": "Agri$2026",
    "acepta_tratamiento": True,
    "acepta_terminos":    True,
}


# ── Health ────────────────────────────────────────────
def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["estado"] == "ok"


def test_health_router():
    res = client.get("/api/v1/auth/health")
    assert res.status_code == 200


# ── Registro ──────────────────────────────────────────
def test_registro_exitoso():
    res = client.post("/api/v1/auth/registro", json=USUARIO_VALIDO)
    assert res.status_code == 201
    data = res.json()
    assert "usuario_id" in data
    assert data["usuario_id"] > 0


def test_registro_email_duplicado():
    client.post("/api/v1/auth/registro", json=USUARIO_VALIDO)
    res = client.post("/api/v1/auth/registro", json=USUARIO_VALIDO)
    assert res.status_code == 400
    assert "correo" in res.json()["detail"].lower()


def test_registro_documento_duplicado():
    client.post("/api/v1/auth/registro", json=USUARIO_VALIDO)
    usuario2 = {**USUARIO_VALIDO, "email": "otro@agrisense.co"}
    res = client.post("/api/v1/auth/registro", json=usuario2)
    assert res.status_code == 400
    assert "documento" in res.json()["detail"].lower()


def test_registro_passwords_no_coinciden():
    usuario = {**USUARIO_VALIDO, "confirmar_password": "OtraPass$1"}
    res = client.post("/api/v1/auth/registro", json=usuario)
    assert res.status_code == 422


def test_registro_password_sin_mayuscula():
    usuario = {**USUARIO_VALIDO, "password": "agri$2026", "confirmar_password": "agri$2026"}
    res = client.post("/api/v1/auth/registro", json=usuario)
    assert res.status_code == 422


def test_registro_password_sin_numero():
    usuario = {**USUARIO_VALIDO, "password": "Agrisense$", "confirmar_password": "Agrisense$"}
    res = client.post("/api/v1/auth/registro", json=usuario)
    assert res.status_code == 422


def test_registro_password_sin_especial():
    usuario = {**USUARIO_VALIDO, "password": "Agrisense1", "confirmar_password": "Agrisense1"}
    res = client.post("/api/v1/auth/registro", json=usuario)
    assert res.status_code == 422


def test_registro_telefono_invalido():
    usuario = {**USUARIO_VALIDO, "telefono": "123456"}
    res = client.post("/api/v1/auth/registro", json=usuario)
    assert res.status_code == 422


def test_registro_sin_aceptar_tratamiento():
    usuario = {**USUARIO_VALIDO, "acepta_tratamiento": False}
    res = client.post("/api/v1/auth/registro", json=usuario)
    assert res.status_code == 422


def test_registro_sin_aceptar_terminos():
    usuario = {**USUARIO_VALIDO, "acepta_terminos": False}
    res = client.post("/api/v1/auth/registro", json=usuario)
    assert res.status_code == 422


def test_registro_email_invalido():
    usuario = {**USUARIO_VALIDO, "email": "no-es-email"}
    res = client.post("/api/v1/auth/registro", json=usuario)
    assert res.status_code == 422


# ── Login ─────────────────────────────────────────────
def test_login_exitoso():
    client.post("/api/v1/auth/registro", json=USUARIO_VALIDO)
    res = client.post("/api/v1/auth/login", json={
        "email":    USUARIO_VALIDO["email"],
        "password": USUARIO_VALIDO["password"],
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token"  in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["usuario"]["email"] == USUARIO_VALIDO["email"]


def test_login_password_incorrecto():
    client.post("/api/v1/auth/registro", json=USUARIO_VALIDO)
    res = client.post("/api/v1/auth/login", json={
        "email":    USUARIO_VALIDO["email"],
        "password": "WrongPass$1",
    })
    assert res.status_code == 401


def test_login_email_inexistente():
    res = client.post("/api/v1/auth/login", json={
        "email":    "noexiste@agrisense.co",
        "password": "Agri$2026",
    })
    assert res.status_code == 401


# ── Token y perfil ────────────────────────────────────
def _get_token():
    client.post("/api/v1/auth/registro", json=USUARIO_VALIDO)
    res = client.post("/api/v1/auth/login", json={
        "email":    USUARIO_VALIDO["email"],
        "password": USUARIO_VALIDO["password"],
    })
    return res.json()["access_token"], res.json()["refresh_token"]


def test_verificar_token():
    token, _ = _get_token()
    res = client.get("/api/v1/auth/verificar",
                     headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["valido"] == True
    assert data["email"] == USUARIO_VALIDO["email"]


def test_verificar_token_invalido():
    res = client.get("/api/v1/auth/verificar",
                     headers={"Authorization": "Bearer tokenfalso123"})
    assert res.status_code == 401


def test_obtener_mi_perfil():
    token, _ = _get_token()
    res = client.get("/api/v1/usuarios/me",
                     headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"]    == USUARIO_VALIDO["email"]
    assert data["nombres"]  == "Juan Carlos"
    assert data["apellidos"]== "Rodriguez Perez"
    assert data["rol"]      == "agricultor"


def test_actualizar_mi_perfil():
    token, _ = _get_token()
    res = client.put("/api/v1/usuarios/me",
                     headers={"Authorization": f"Bearer {token}"},
                     json={"ciudad": "Bogota", "departamento": "Cundinamarca"})
    assert res.status_code == 200
    assert res.json()["ciudad"] == "Bogota"


def test_perfil_iot():
    token, _ = _get_token()
    res = client.get("/api/v1/usuarios/me/perfil",
                     headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "parcelas_ids" in data
    assert "sensores_ids" in data
    assert isinstance(data["parcelas_ids"], list)


def test_actualizar_perfil_iot():
    token, _ = _get_token()
    res = client.put("/api/v1/usuarios/me/perfil",
                     headers={"Authorization": f"Bearer {token}"},
                     json={
                         "parcelas_ids": [1, 2, 3],
                         "sensores_ids": ["SOIL_HUM_01", "AIR_TEMP_01"],
                     })
    assert res.status_code == 200
    data = res.json()
    assert 1 in data["parcelas_ids"]
    assert "SOIL_HUM_01" in data["sensores_ids"]


# ── Refresh y logout ──────────────────────────────────
def test_refresh_token():
    _, refresh = _get_token()
    res = client.post("/api/v1/auth/refresh",
                      json={"refresh_token": refresh})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_refresh_token_invalido():
    res = client.post("/api/v1/auth/refresh",
                      json={"refresh_token": "tokenfalso"})
    assert res.status_code == 401


def test_logout():
    _, refresh = _get_token()
    res = client.post("/api/v1/auth/logout",
                      json={"refresh_token": refresh})
    assert res.status_code == 200
    # Despues del logout el refresh token ya no sirve
    res2 = client.post("/api/v1/auth/refresh",
                       json={"refresh_token": refresh})
    assert res2.status_code == 401


# ── Cambiar contrasena ────────────────────────────────
def test_cambiar_password():
    token, _ = _get_token()
    res = client.put("/api/v1/auth/cambiar-password",
                     headers={"Authorization": f"Bearer {token}"},
                     json={
                         "password_actual":    "Agri$2026",
                         "password_nuevo":     "NuevaClave$99",
                         "confirmar_password": "NuevaClave$99",
                     })
    assert res.status_code == 200


def test_cambiar_password_actual_incorrecto():
    token, _ = _get_token()
    res = client.put("/api/v1/auth/cambiar-password",
                     headers={"Authorization": f"Bearer {token}"},
                     json={
                         "password_actual":    "ClaveIncorrecta$1",
                         "password_nuevo":     "NuevaClave$99",
                         "confirmar_password": "NuevaClave$99",
                     })
    assert res.status_code == 400


# ── Admin ─────────────────────────────────────────────
def test_agricultor_no_puede_listar_usuarios():
    token, _ = _get_token()
    res = client.get("/api/v1/usuarios/",
                     headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403