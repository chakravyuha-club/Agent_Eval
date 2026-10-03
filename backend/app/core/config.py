import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    APP_NAME: str = "AgentScore"
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    DEBUG: bool = True
    
    SECRET_KEY: str = "agentscore_super_secure_secret_key_change_in_production_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    DATABASE_URL: str = "sqlite:///./agentscore.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_CELERY: bool = False
    
    STORAGE_PROVIDER: str = "local"
    STORAGE_BASE_DIR: str = "./storage"
    
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
    
    MAX_UPLOAD_SIZE_MB: int = 50
    EVALUATION_TIMEOUT_SECONDS: int = 180
    STAGE2_REQUEST_TIMEOUT_SECONDS: float = 10.0
    STAGE2_MAX_CONCURRENCY: int = 5
    STAGE2_REPEATED_RUNS: int = 3
    ENABLE_SSRF_PROTECTION: bool = True
    
    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
