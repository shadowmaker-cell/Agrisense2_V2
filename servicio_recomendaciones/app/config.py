from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5432/recomendaciones_db"
    DEVICE_SERVICE_URL: str = "http://localhost:8001"
    INGESTA_SERVICE_URL: str = "http://localhost:8002"
    PROCESAMIENTO_SERVICE_URL: str = "http://localhost:8003"
    PARCELAS_SERVICE_URL: str = "http://localhost:8005"
    ML_SERVICE_URL: str = "http://localhost:8006"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()