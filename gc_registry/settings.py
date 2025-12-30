import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.production"), extra="ignore")

    ENVIRONMENT: str = "LOCAL"
    
    # Database URLs (Railway / Cloud)
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    DATABASE_PRIVATE_URL: str | None = os.getenv("DATABASE_PRIVATE_URL")
    POSTGRES_URL: str | None = os.getenv("POSTGRES_URL")

    # Fallback/Manual Configuration - Prioritize Railway names if available
    POSTGRES_HOST: str = os.getenv("DATABASE_HOST_WRITE", os.getenv("POSTGRES_HOST", "127.0.0.1"))
    POSTGRES_PORT: int = int(os.getenv("DATABASE_PORT", os.getenv("POSTGRES_PORT", "5432")))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", os.getenv("DATABASE_USER", "postgres"))
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", os.getenv("DATABASE_PASSWORD", "postgres"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", os.getenv("DATABASE_NAME", "railway"))
    
    # Internal routing
    DATABASE_HOST_READ: str = "db_read"
    DATABASE_HOST_WRITE: str = "db_write"
    DATABASE_PORT: int = 5432
    GCP_INSTANCE_READ: str = os.getenv("GCP_INSTANCE_READ", "")
    GCP_INSTANCE_WRITE: str = os.getenv("GCP_INSTANCE_WRITE", "")
    STATIC_DIR_FP: str = os.getenv("STATIC_DIR_FP", "/code/gc_registry/static")
    ESDB_CONNECTION_STRING: str = os.getenv("ESDB_CONNECTION_STRING", "eventstore.db")

    JWT_SECRET_KEY: str = "secret_key"
    JWT_ALGORITHM: str = "HS256"
    MIDDLEWARE_SECRET_KEY: str = "secret_key"

    LOG_LEVEL: str = "INFO"
    CORS_ALLOWED_ORIGINS: str = ""

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins into a clean list."""
        if not self.CORS_ALLOWED_ORIGINS:
            return []
        return [
            o.strip().strip("'\"").rstrip("/") 
            for o in self.CORS_ALLOWED_ORIGINS.split(",") 
            if o.strip()
        ]
        """Parse CORS origins into a clean list."""
        if not self.CORS_ALLOWED_ORIGINS:
            return []
        return [
            o.strip().strip("'\"").rstrip("/") 
            for o in self.CORS_ALLOWED_ORIGINS.split(",") 
            if o.strip()
        ]

    CERTIFICATE_GRANULARITY_HOURS: float = 1.0
    CAPACITY_MARGIN: float = 1.1
    CERTIFICATE_EXPIRY_YEARS: int = 2
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_KEY_EXPIRE_DAYS: int = 365
    API_KEY_MAX_EXPIRE_DAYS: int = 1095
    REFRESH_WARNING_MINS: int = 5
    PROFILING_ENABLED: bool = False

settings = Settings()
