from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, usuarios
from app.database import SessionLocal, engine
from app.models.usuario import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Auth Service",
    description="Servicio de autenticacion y gestion de usuarios AgriSense — Ley 1581 de 2012",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)


@app.get("/health")
def health_check():
    return {
        "estado":   "ok",
        "servicio": "auth-service",
        "version":  "1.0.0",
    }