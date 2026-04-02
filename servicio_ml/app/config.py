from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5432/ml_db"
    DEVICE_SERVICE_URL: str = "http://localhost:8001"
    INGESTA_SERVICE_URL: str = "http://localhost:8002"
    PARCELAS_SERVICE_URL: str = "http://localhost:8005"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()