from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base


@dataclass(frozen=True)
class DatabaseInfo:
    backend: str
    url: str


@lru_cache
def get_database_info() -> DatabaseInfo:
    url = settings.resolved_database_url
    backend = settings.resolved_database_backend
    return DatabaseInfo(backend=backend, url=url)


@lru_cache
def get_database_engine() -> Engine:
    database_info = get_database_info()
    engine_kwargs: dict[str, object] = {}

    if database_info.backend == "sqlite":
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


def build_postgres_url(
    username: str,
    password: str,
    host: str,
    port: int = 5432,
    database: str = "repoorover",
) -> str:
    safe_password = quote_plus(password)
    return f"postgresql+psycopg://{username}:{safe_password}@{host}:{port}/{database}"
