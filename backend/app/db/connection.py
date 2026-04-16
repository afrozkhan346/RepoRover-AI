from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from urllib.parse import quote_plus

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatabaseInfo:
    backend: str
    url: str


def is_sqlite_url(url: str) -> bool:
    normalized = (url or "").strip().lower()
    return normalized.startswith("sqlite")


@lru_cache
def get_database_info() -> DatabaseInfo:
    url = settings.resolved_database_url
    backend = settings.resolved_database_backend
    return DatabaseInfo(backend=backend, url=url)


@lru_cache
def get_database_engine() -> Engine:
    database_info = get_database_info()
    engine_kwargs: dict[str, object] = {}

    logger.info("Initializing database engine for backend=%s", database_info.backend)

    # Guard against misconfigured DATABASE_BACKEND values by trusting the URL
    # scheme for driver-specific connect args.
    if is_sqlite_url(database_info.url):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 1800
        engine_kwargs["pool_size"] = settings.db_pool_size
        engine_kwargs["max_overflow"] = settings.db_max_overflow

    return create_engine(database_info.url, **engine_kwargs)


@lru_cache
def get_session_factory() -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_database_engine())


def create_tables() -> None:
    Base.metadata.create_all(bind=get_database_engine())


def should_create_sqlite_tables() -> bool:
    return is_sqlite_url(get_database_info().url)


def missing_required_tables(required_tables: list[str]) -> list[str]:
    engine = get_database_engine()
    inspector = inspect(engine)
    missing: list[str] = []
    for table_name in required_tables:
        if not inspector.has_table(table_name):
            missing.append(table_name)
    return missing


def build_postgres_url(
    username: str,
    password: str,
    host: str,
    port: int = 5432,
    database: str = "Reponium",
) -> str:
    safe_password = quote_plus(password)
    return f"postgresql+psycopg://{username}:{safe_password}@{host}:{port}/{database}"
