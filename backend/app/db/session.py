from __future__ import annotations

from app.db.connection import (
    create_tables,
    get_database_engine,
    get_database_info,
    get_session_factory,
)

engine = get_database_engine()
SessionLocal = get_session_factory()

__all__ = [
    "create_tables",
    "engine",
    "get_database_engine",
    "get_database_info",
    "get_session_factory",
    "SessionLocal",
]
