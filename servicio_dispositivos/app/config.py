from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    API_BASE_URL: str = "http://localhost:8001"
    BROKER_URL: str = "localhost:9092"
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5432/device_db"
    JWT_SECRET: str = "cambia-esto-en-produccion"
    REFRESH_SECRET: str = "cambia-esto-tambien"

    class Config:
        env_file = ".env"

settings = Settings()