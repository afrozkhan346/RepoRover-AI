from functools import lru_cache
import json
from typing import Any
from urllib.parse import quote_plus

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Reponium AI"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "https://reponium.com",
            "https://reponium.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
            "http://localhost:5176",
            "http://127.0.0.1:5176",
        ]
    )
    database_backend: str = "sqlite"
    database_url: str = "sqlite:///./repoorover.db"
    postgres_host: str | None = None
    postgres_port: int = 5432
    postgres_database: str = "repoorover"
    postgres_username: str | None = None
    postgres_password: str | None = None
    postgres_sslmode: str = "prefer"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    projects_workspace_path: str = "./projects"
    projects_retention_days: int = 14
    projects_max_entries: int = 200
    projects_cleanup_enabled: bool = True
    projects_max_file_count: int = 20000
    projects_max_total_size_bytes: int = 268435456
    projects_max_zip_entry_count: int = 50000
    projects_max_zip_uncompressed_bytes: int = 536870912
    projects_allowed_extensions: list[str] = Field(default_factory=list)
    projects_disallow_symlinks: bool = True
    llm_provider: str = "groq"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    ollama_timeout_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5174",
                "http://localhost:5175",
                "http://127.0.0.1:5175",
                "http://localhost:5176",
                "http://127.0.0.1:5176",
            ]
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
            "http://localhost:5176",
            "http://127.0.0.1:5176",
        ]

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return bool(value)

    @field_validator("database_backend", mode="before")
    @classmethod
    def parse_database_backend(cls, value: Any) -> str:
        if value is None:
            return "sqlite"
        normalized = str(value).strip().lower()
        if normalized in {"postgres", "postgresql", "pg"}:
            return "postgresql"
        if normalized in {"sqlite", "sqlite3"}:
            return "sqlite"
        if normalized in {"auto"}:
            return "auto"
        raise ValueError("DATABASE_BACKEND must be one of: sqlite, postgresql, auto")

    @field_validator("projects_cleanup_enabled", mode="before")
    @classmethod
    def parse_projects_cleanup_enabled(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "enabled"}:
                return True
            if normalized in {"0", "false", "no", "off", "disabled"}:
                return False
        return bool(value)

    @field_validator("projects_allowed_extensions", mode="before")
    @classmethod
    def parse_projects_allowed_extensions(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped == "[]":
                return []

            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    loaded = json.loads(stripped)
                except json.JSONDecodeError:
                    loaded = None
                if isinstance(loaded, list):
                    normalized: list[str] = []
                    for item in loaded:
                        text = str(item).strip().lower()
                        if not text:
                            continue
                        normalized.append(text if text.startswith(".") else f".{text}")
                    return normalized

            parsed = [item.strip().lower() for item in stripped.split(",") if item.strip()]
            normalized: list[str] = []
            for item in parsed:
                normalized.append(item if item.startswith(".") else f".{item}")
            return normalized
        if isinstance(value, list):
            normalized: list[str] = []
            for item in value:
                text = str(item).strip().lower()
                if not text:
                    continue
                normalized.append(text if text.startswith(".") else f".{text}")
            return normalized
        return []

    @field_validator("projects_disallow_symlinks", mode="before")
    @classmethod
    def parse_projects_disallow_symlinks(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "enabled"}:
                return True
            if normalized in {"0", "false", "no", "off", "disabled"}:
                return False
        return bool(value)

    @field_validator("llm_provider", mode="before")
    @classmethod
    def parse_llm_provider(cls, value: Any) -> str:
        if value is None:
            return "groq"
        normalized = str(value).strip().lower()
        return normalized or "groq"

    @field_validator("ollama_timeout_seconds", mode="before")
    @classmethod
    def parse_ollama_timeout_seconds(cls, value: Any) -> int:
        if value is None or value == "":
            return 120
        try:
            return max(int(value), 1)
        except (TypeError, ValueError):
            return 120

    @model_validator(mode="after")
    def validate_database_configuration(self) -> "Settings":
        backend = self.database_backend
        url = self.database_url.strip()
        is_postgres_url = url.startswith("postgresql") or url.startswith("postgres")

        if backend == "postgresql" and not is_postgres_url:
            required = [self.postgres_host, self.postgres_username, self.postgres_password, self.postgres_database]
            if not all(required):
                raise ValueError(
                    "PostgreSQL backend selected but DATABASE_URL is not PostgreSQL and one or more POSTGRES_* fields are missing"
                )

        return self

    @property
    def resolved_database_backend(self) -> str:
        if self.database_backend == "auto":
            url = self.database_url.strip()
            if url.startswith("postgresql") or url.startswith("postgres"):
                return "postgresql"
            return "sqlite"
        return self.database_backend

    @property
    def resolved_database_url(self) -> str:
        # DATABASE_URL always wins when explicitly PostgreSQL.
        url = self.database_url.strip()
        if self.resolved_database_backend == "postgresql":
            if url.startswith("postgresql") or url.startswith("postgres"):
                return url

            username = self.postgres_username or ""
            password = self.postgres_password or ""
            host = self.postgres_host or "localhost"
            database = self.postgres_database
            safe_password = quote_plus(password)
            return (
                f"postgresql+psycopg://{username}:{safe_password}@{host}:{self.postgres_port}/{database}"
                f"?sslmode={self.postgres_sslmode}"
            )

        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
