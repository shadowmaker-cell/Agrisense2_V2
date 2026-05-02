import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test
)

Base.metadata.create_all(bind=engine_test)


@pytest.fixture(scope="function")
def db():
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_http_vacio():
    with patch("app.services.detector.httpx.get") as mock:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = []
        mock.return_value = resp
        yield mock


@pytest.fixture
def mock_jwt_anonimo():
    with patch("app.routers.eventos.get_usuario_id_opcional") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_jwt_usuario():
    with patch("app.routers.eventos.get_usuario_id_opcional") as mock:
        mock.return_value = 1
        yield mock