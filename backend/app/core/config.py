from functools import lru_cache
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    # Application Metadata
    APP_NAME: str = "AI Job Prediction and Career Recommendation System"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS Allowed Origins
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Security & JWT Configuration (Minimum 32 characters for HMAC-SHA256)
    JWT_SECRET_KEY: str = "careerai_super_secure_jwt_signing_key_2026_minimum_32_characters_long"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Protected Admin Viewer Access Key
    ADMIN_ACCESS_KEY: str = "careerai-admin-2026"

    # Database Configuration (MongoDB Atlas with SQLite offline fallback)
    MONGODB_URI: str | None = None
    DATABASE_NAME: str = "ai_job_prediction"
    SQLITE_DB_PATH: str = "backend/data/careerai.db"

    # Local LLM Configuration (Ollama)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"

    @property
    def parsed_cors_origins(self) -> List[str]:
        """Parse comma-separated string of origins or return list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


settings = get_settings()
