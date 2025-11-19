import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "LOCAL"

    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "granular_registry")
    
    DATABASE_HOST_READ: str = os.getenv("DATABASE_HOST_READ", "db_read")
    DATABASE_HOST_WRITE: str = os.getenv("DATABASE_HOST_WRITE", "db_write")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    GCP_INSTANCE_READ: str = os.getenv("GCP_INSTANCE_READ", "")
    GCP_INSTANCE_WRITE: str = os.getenv("GCP_INSTANCE_WRITE", "")
    STATIC_DIR_FP: str = os.getenv("STATIC_DIR_FP", "/code/gc_registry/static")
    ESDB_CONNECTION_STRING: str = os.getenv("ESDB_CONNECTION_STRING", "eventstore.db")

    JWT_SECRET_KEY: str = "secret_key"
    JWT_ALGORITHM: str = "HS256"
    MIDDLEWARE_SECRET_KEY: str = "secret_key"

    LOG_LEVEL: str = "INFO"

    CERTIFICATE_GRANULARITY_HOURS: float = 1.0
    CAPACITY_MARGIN: float = 1.1
    CERTIFICATE_EXPIRY_YEARS: int = 2
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_KEY_EXPIRE_DAYS: int = 365
    API_KEY_MAX_EXPIRE_DAYS: int = 1095
    REFRESH_WARNING_MINS: int = 5
    PROFILING_ENABLED: bool = False

settings = Settings()
