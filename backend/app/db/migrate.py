"""
migrate.py
----------
Self-healing DDL migration for the AI-DAM backend.

Called once at application startup via main.py.
Uses `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` so it is safe to re-run
on every boot — already-existing columns are silently skipped.

This replaces a full Alembic migration for the columns added in the
AI Retrieval / Search Quality / Version Control / Archive feature gap phases.
"""

from sqlalchemy import text
from app.db.session.database import engine


# ------------------------------------------------------------
# Columns to ensure exist on the 'assets' table.
# Format: (column_name, sql_type_definition)
# ------------------------------------------------------------

_ASSET_COLUMNS: list[tuple[str, str]] = [
    # AI Retrieval — queryable individual columns
    ("perceptual_hash",    "VARCHAR(16)"),
    ("ai_summary",         "TEXT"),
    ("completeness_score", "INTEGER DEFAULT 0"),
    ("ai_tags",            "JSONB"),
    ("detected_objects",   "JSONB"),
    ("extracted_text",     "TEXT"),
    ("image_caption",      "TEXT"),

    # Version Control — changelog
    ("changelog",   "TEXT"),
    ("updated_by",  "VARCHAR"),
    ("updated_at",  "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"),

    # Archive — Phase 3.2 / 3.5
    ("archived_at",     "TIMESTAMP WITH TIME ZONE"),
    ("archive_reason",  "TEXT"),
]

_USER_COLUMNS: list[tuple[str, str]] = [
    ("allowed_domains",    "VARCHAR[]"),
]


def upgrade_db_schema() -> None:
    """
    Idempotently add new columns to the `assets` and `users` tables.
    Safe to call on every startup — existing columns are never touched.
    """
    with engine.connect() as conn:
        # Assets Table
        for col_name, col_type in _ASSET_COLUMNS:
            ddl = text(
                f"ALTER TABLE assets "
                f"ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            )
            try:
                conn.execute(ddl)
                print(f"[MIGRATE] Column ensured: assets.{col_name}")
            except Exception as e:
                print(f"[MIGRATE] Warning — assets.{col_name}: {e}")

        # Users Table
        for col_name, col_type in _USER_COLUMNS:
            ddl = text(
                f"ALTER TABLE users "
                f"ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
            )
            try:
                conn.execute(ddl)
                print(f"[MIGRATE] Column ensured: users.{col_name}")
            except Exception as e:
                print(f"[MIGRATE] Warning — users.{col_name}: {e}")

        conn.commit()

    print("[MIGRATE] Schema upgrade complete.")
