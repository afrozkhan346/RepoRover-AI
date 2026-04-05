from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db.models import Achievement, LearningPath, Lesson, Quiz
from app.db.session import SessionLocal


@dataclass(frozen=True)
class UpsertResult:
    table: str
    processed: int
    inserted: int
    updated: int


@dataclass(frozen=True)
class SeedConfig:
    data_dir: Path
    chunk_size: int
    dry_run: bool


def _required_columns(row: dict[str, str], required: list[str], file_name: str) -> None:
    missing = [column for column in required if row.get(column, "").strip() == ""]
    if missing:
        raise ValueError(f"Missing required columns in {file_name}: {', '.join(missing)}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            normalized = {str(key).strip(): (value or "").strip() for key, value in row.items()}
            if not any(normalized.values()):
                continue
            rows.append(normalized)
        return rows


def _to_int(value: str, field_name: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"Field '{field_name}' must be an integer. Received: {value}") from error


def _collect_existing_keys(session: Session, model, conflict_columns: list[str], keys: list[tuple[Any, ...]]) -> set[tuple[Any, ...]]:
    if not keys:
        return set()

    unique_keys = list(dict.fromkeys(keys))
    if len(conflict_columns) == 1:
        column = getattr(model, conflict_columns[0])
        values = [key[0] for key in unique_keys]
        rows = session.execute(select(column).where(column.in_(values))).all()
        return {(row[0],) for row in rows}

    columns = [getattr(model, column_name) for column_name in conflict_columns]
    rows = session.execute(select(*columns).where(tuple_(*columns).in_(unique_keys))).all()
    return {tuple(row) for row in rows}


def _build_upsert_statement(session: Session, model, chunk: list[dict[str, Any]], conflict_columns: list[str], update_columns: list[str]):
    bind_name = session.bind.dialect.name if session.bind is not None else "sqlite"
    if bind_name == "postgresql":
        statement = pg_insert(model).values(chunk)
    elif bind_name == "sqlite":
        statement = sqlite_insert(model).values(chunk)
    else:
        raise ValueError(f"Unsupported database dialect for upsert: {bind_name}")

    updates = {column: getattr(statement.excluded, column) for column in update_columns}
    return statement.on_conflict_do_update(index_elements=conflict_columns, set_=updates)


def _bulk_upsert(
    session: Session,
    *,
    model,
    rows: list[dict[str, Any]],
    conflict_columns: list[str],
    update_columns: list[str],
    chunk_size: int,
) -> UpsertResult:
    processed = 0
    inserted = 0
    updated = 0

    for start in range(0, len(rows), chunk_size):
        chunk = rows[start : start + chunk_size]
        keys = [tuple(row[column] for column in conflict_columns) for row in chunk]
        existing = _collect_existing_keys(session, model, conflict_columns, keys)
        processed += len(chunk)

        existing_count = sum(1 for key in keys if key in existing)
        updated += existing_count
        inserted += len(chunk) - existing_count

        statement = _build_upsert_statement(
            session,
            model,
            chunk,
            conflict_columns=conflict_columns,
            update_columns=update_columns,
        )
        session.execute(statement)

    return UpsertResult(
        table=model.__tablename__,
        processed=processed,
        inserted=inserted,
        updated=updated,
    )


def _seed_learning_paths(session: Session, config: SeedConfig) -> UpsertResult:
    file_path = config.data_dir / "learning_paths.csv"
    rows = _read_csv(file_path)
    payload: list[dict[str, Any]] = []

    for row in rows:
        _required_columns(row, ["title", "difficulty", "estimated_hours", "order_index", "created_at"], file_path.name)
        payload.append(
            {
                "title": row["title"],
                "description": row.get("description") or None,
                "difficulty": row["difficulty"],
                "estimated_hours": _to_int(row["estimated_hours"], "estimated_hours"),
                "icon": row.get("icon") or None,
                "order_index": _to_int(row["order_index"], "order_index"),
                "created_at": row["created_at"],
            }
        )

    return _bulk_upsert(
        session,
        model=LearningPath,
        rows=payload,
        conflict_columns=["title"],
        update_columns=["description", "difficulty", "estimated_hours", "icon", "order_index", "created_at"],
        chunk_size=config.chunk_size,
    )


def _learning_path_lookup(session: Session) -> dict[str, int]:
    rows = session.execute(select(LearningPath.id, LearningPath.title)).all()
    return {title: path_id for path_id, title in rows}


def _seed_lessons(session: Session, config: SeedConfig) -> UpsertResult:
    file_path = config.data_dir / "lessons.csv"
    rows = _read_csv(file_path)
    payload: list[dict[str, Any]] = []
    path_lookup = _learning_path_lookup(session)

    for row in rows:
        _required_columns(
            row,
            ["title", "difficulty", "xp_reward", "order_index", "estimated_minutes", "created_at"],
            file_path.name,
        )

        learning_path_id = row.get("learning_path_id")
        if learning_path_id:
            resolved_path_id = _to_int(learning_path_id, "learning_path_id")
        else:
            learning_path_title = row.get("learning_path_title", "")
            if not learning_path_title:
                raise ValueError("Lessons CSV requires either learning_path_id or learning_path_title")
            if learning_path_title not in path_lookup:
                raise ValueError(f"Unknown learning_path_title '{learning_path_title}' in {file_path.name}")
            resolved_path_id = path_lookup[learning_path_title]

        payload.append(
            {
                "learning_path_id": resolved_path_id,
                "title": row["title"],
                "description": row.get("description") or None,
                "content": row.get("content") or None,
                "difficulty": row["difficulty"],
                "xp_reward": _to_int(row["xp_reward"], "xp_reward"),
                "order_index": _to_int(row["order_index"], "order_index"),
                "estimated_minutes": _to_int(row["estimated_minutes"], "estimated_minutes"),
                "created_at": row["created_at"],
            }
        )

    return _bulk_upsert(
        session,
        model=Lesson,
        rows=payload,
        conflict_columns=["learning_path_id", "title"],
        update_columns=["description", "content", "difficulty", "xp_reward", "order_index", "estimated_minutes", "created_at"],
        chunk_size=config.chunk_size,
    )


def _seed_achievements(session: Session, config: SeedConfig) -> UpsertResult:
    file_path = config.data_dir / "achievements.csv"
    rows = _read_csv(file_path)
    payload: list[dict[str, Any]] = []

    for row in rows:
        _required_columns(
            row,
            ["title", "xp_reward", "requirement_type", "requirement_value", "created_at"],
            file_path.name,
        )
        payload.append(
            {
                "title": row["title"],
                "description": row.get("description") or None,
                "icon": row.get("icon") or None,
                "xp_reward": _to_int(row["xp_reward"], "xp_reward"),
                "requirement_type": row["requirement_type"],
                "requirement_value": _to_int(row["requirement_value"], "requirement_value"),
                "created_at": row["created_at"],
            }
        )

    return _bulk_upsert(
        session,
        model=Achievement,
        rows=payload,
        conflict_columns=["title"],
        update_columns=["description", "icon", "xp_reward", "requirement_type", "requirement_value", "created_at"],
        chunk_size=config.chunk_size,
    )


def _lesson_lookup(session: Session) -> dict[str, int]:
    rows = session.execute(select(Lesson.id, Lesson.title)).all()
    return {title: lesson_id for lesson_id, title in rows}


def _seed_quizzes(session: Session, config: SeedConfig) -> UpsertResult:
    file_path = config.data_dir / "quizzes.csv"
    rows = _read_csv(file_path)
    payload: list[dict[str, Any]] = []
    lesson_lookup = _lesson_lookup(session)

    for row in rows:
        _required_columns(
            row,
            ["question", "options", "correct_answer", "difficulty", "xp_reward", "created_at"],
            file_path.name,
        )

        lesson_id = row.get("lesson_id")
        if lesson_id:
            resolved_lesson_id = _to_int(lesson_id, "lesson_id")
        else:
            lesson_title = row.get("lesson_title", "")
            if not lesson_title:
                raise ValueError("Quizzes CSV requires either lesson_id or lesson_title")
            if lesson_title not in lesson_lookup:
                raise ValueError(f"Unknown lesson_title '{lesson_title}' in {file_path.name}")
            resolved_lesson_id = lesson_lookup[lesson_title]

        payload.append(
            {
                "lesson_id": resolved_lesson_id,
                "question": row["question"],
                "options": row["options"],
                "correct_answer": row["correct_answer"],
                "explanation": row.get("explanation") or None,
                "difficulty": row["difficulty"],
                "xp_reward": _to_int(row["xp_reward"], "xp_reward"),
                "created_at": row["created_at"],
            }
        )

    return _bulk_upsert(
        session,
        model=Quiz,
        rows=payload,
        conflict_columns=["lesson_id", "question"],
        update_columns=["options", "correct_answer", "explanation", "difficulty", "xp_reward", "created_at"],
        chunk_size=config.chunk_size,
    )


def run_seed(config: SeedConfig) -> list[UpsertResult]:
    session = SessionLocal()
    results: list[UpsertResult] = []
    try:
        results.append(_seed_learning_paths(session, config))
        if config.dry_run:
            session.flush()
        else:
            session.commit()

        results.append(_seed_lessons(session, config))
        if config.dry_run:
            session.flush()
        else:
            session.commit()

        results.append(_seed_achievements(session, config))
        if config.dry_run:
            session.flush()
        else:
            session.commit()

        results.append(_seed_quizzes(session, config))
        if config.dry_run:
            session.flush()
            session.rollback()
        else:
            session.commit()

        return results
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _default_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "seed"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Idempotent SQLAlchemy CSV seed loader")
    parser.add_argument("--data-dir", type=Path, default=_default_data_dir(), help="CSV directory path")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Bulk upsert chunk size")
    parser.add_argument("--dry-run", action="store_true", help="Parse and compute upsert stats without writing")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = SeedConfig(data_dir=args.data_dir, chunk_size=max(args.chunk_size, 1), dry_run=args.dry_run)

    if not config.data_dir.exists():
        raise SystemExit(f"Seed data directory not found: {config.data_dir}")

    results = run_seed(config)
    mode = "DRY-RUN" if config.dry_run else "APPLY"
    print(f"[{mode}] Seed summary for {config.data_dir}:")
    for result in results:
        print(
            f" - {result.table}: processed={result.processed}, "
            f"inserted={result.inserted}, updated={result.updated}"
        )


if __name__ == "__main__":
    main()
