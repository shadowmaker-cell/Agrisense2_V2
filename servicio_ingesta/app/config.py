from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    API_BASE_URL: str = "http://localhost:8002"
    BROKER_URL: str = "localhost:9092"
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5432/ingesta_db"
    JWT_SECRET: str = "cambia-esto-en-produccion"
    REFRESH_SECRET: str = "cambia-esto-tambien"
    DEVICE_SERVICE_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()