"""
Configuration settings for Paraxis AI Intelligence Platform.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Service Network
    INTELLIGENCE_HOST: str = "0.0.0.0"
    INTELLIGENCE_PORT: int = 8001
    CORE_SERVICE_URL: str = "http://localhost:8000"
    INTELLIGENCE_INTERNAL_TOKEN: str = "replace-with-secure-internal-jwt-or-service-secret"
    
    # Storage & Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "postgresql://paraxis_user:paraxis_local_password@localhost:5432/paraxis_dev"
    
    # AI Provider settings
    AI_DEFAULT_PROVIDER: str = "google"
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
