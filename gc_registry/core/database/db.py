import os
from typing import Any, Generator

from sqlmodel import Session, SQLModel, create_engine

from gc_registry.account import models as account_models
from gc_registry.authentication import models as authentication_models
from gc_registry.certificate import models as certificate_models
from gc_registry.device import models as device_models
from gc_registry.measurement import models as measurement_models
from gc_registry.settings import settings
from gc_registry.storage import models as storage_models
from gc_registry.user import models as user_models

"""
This section is used by Alembic to load the all the database related models
"""

__all__ = [
    "SQLModel",
    "user_models",
    "authentication_models",
    "account_models",
    "device_models",
    "certificate_models",
    "storage_models",
    "measurement_models",
]


class DButils:
    def __init__(
        self,
        db_username: str | None = None,
        db_password: str | None = None,
        db_host: str | None = None,
        db_port: int | None = None,
        db_name: str | None = None,
        gcp_instance: str | None = None,
        db_test_fp: str = "gc_registry_test.db",
        test: bool = False,
    ):
        self._db_username = db_username
        self._db_password = db_password
        self._db_host = db_host
        self._db_port = db_port
        self._db_name = db_name
        self._db_test_fp = db_test_fp
        self._gcp_instance = gcp_instance

        if test:
            self.connection_str = f"sqlite:///{self._db_test_fp}"
        else:
            # Check for DATABASE_URL in order of priority
            # 1. Direct from environment (Set by Railway/Heroku/etc)
            # 2. From settings (Populated by Pydantic)
            env_vars = ["DATABASE_URL", "DATABASE_PRIVATE_URL", "POSTGRES_URL"]
            self.connection_str = None
            source = None

            for var in env_vars:
                # Prioritize direct os.getenv to bypass any Pydantic caching/loading issues
                val = os.getenv(var)
                if val:
                    self.connection_str = val
                    source = f"env:{var}"
                    break
            
            if not self.connection_str:
                setting_vals = [settings.DATABASE_URL, settings.DATABASE_PRIVATE_URL, settings.POSTGRES_URL]
                self.connection_str = next((v for v in setting_vals if v), None)
                if self.connection_str:
                    source = "settings:DATABASE_URL"

            if not self.connection_str:
                if self._gcp_instance:
                    # Cloud SQL specific logic
                    socket_path = f"/cloudsql/{self._gcp_instance}"
                    self.connection_str = f"postgresql://{self._db_username}:{self._db_password}@/{self._db_name}?host={socket_path}"
                    source = "gcp_instance"
                else:
                    # Fallback to standard construction
                    host = settings.POSTGRES_HOST if settings.ENVIRONMENT == "RAILWAY" else self._db_host
                    port = settings.POSTGRES_PORT if settings.ENVIRONMENT == "RAILWAY" else self._db_port
                    self.connection_str = f"postgresql://{self._db_username}:{self._db_password}@{host}:{port}/{self._db_name}"
                    source = "standard_fallback"

        # Log connection details (redacted)
        from urllib.parse import urlparse
        try:
            from gc_registry.logging_config import logger
            parsed = urlparse(self.connection_str)
            redacted = self.connection_str.replace(parsed.password, "********") if parsed.password else self.connection_str
            logger.info(f"Database connection initialized from {source}: {redacted}")
        except Exception:
            pass

        self.engine = create_engine(
            self.connection_str,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False,
        )

    def yield_session(self) -> Generator[Any, Any, Any]:
        with Session(self.engine) as session, session.begin():
            yield session

    def yield_twophase_session(self, write_object) -> Generator[Any, Any, Any]:
        with Session(self.engine, twophase=True) as session:
            yield session

    def get_session(self) -> Session:
        return Session(self.engine)


# Initialising the DButil clients
db_name_to_client: dict[str, Any] = {}


def get_db_name_to_client() -> dict[str, Any]:
    global db_name_to_client

    if db_name_to_client == {}:
        if settings.ENVIRONMENT == "RAILWAY":
            # For Railway, use the same database for both read and write
            db_client = DButils(
                db_host=settings.POSTGRES_HOST,
                db_name=settings.POSTGRES_DB,
                db_username=settings.POSTGRES_USER,
                db_password=settings.POSTGRES_PASSWORD,
                db_port=settings.POSTGRES_PORT,
                gcp_instance=None,
            )
            db_name_to_client["db_read"] = db_client
            db_name_to_client["db_write"] = db_client
        else:
            db_mapping = [
                ("db_read", settings.DATABASE_HOST_READ, settings.GCP_INSTANCE_READ),
                ("db_write", settings.DATABASE_HOST_WRITE, settings.GCP_INSTANCE_WRITE),
            ]

            for db_name, db_host, gcp_instance in db_mapping:
                db_client = DButils(
                    db_host=db_host,
                    db_name=settings.POSTGRES_DB,
                    db_username=settings.POSTGRES_USER,
                    db_password=settings.POSTGRES_PASSWORD,
                    db_port=settings.DATABASE_PORT,
                    gcp_instance=gcp_instance,
                )
                db_name_to_client[db_name] = db_client

    return db_name_to_client


def get_session(target: str) -> Generator[Session, None, None]:
    with next(db_name_to_client[target].yield_session()) as session:
        try:
            yield session
        finally:
            session.close()


def get_write_session() -> Session:
    return next(get_session("db_write"))


def get_read_session() -> Session:
    return next(get_session("db_read"))
