from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5432/auth_db"
    JWT_SECRET: str = "agrisense_jwt_secret_2026"
    REFRESH_SECRET: str = "agrisense_refresh_secret_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()