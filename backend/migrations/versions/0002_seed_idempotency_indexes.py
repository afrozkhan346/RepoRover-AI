"""Add unique indexes for idempotent seed operations

Revision ID: 0002_seed_idempotency_indexes
Revises: 0001_sqlalchemy_baseline
Create Date: 2026-04-06 21:00:00

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "0002_seed_idempotency_indexes"
down_revision = "0001_sqlalchemy_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use explicit SQL to keep migration compatible across SQLite and PostgreSQL.
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_learning_paths_title ON learning_paths (title)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_lessons_learning_path_title ON lessons (learning_path_id, title)"
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_achievements_title ON achievements (title)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_quizzes_lesson_question ON quizzes (lesson_id, question)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_quizzes_lesson_question")
    op.execute("DROP INDEX IF EXISTS uq_achievements_title")
    op.execute("DROP INDEX IF EXISTS uq_lessons_learning_path_title")
    op.execute("DROP INDEX IF EXISTS uq_learning_paths_title")
