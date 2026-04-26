"""One-shot migration: add Ghost publishing columns to `articles`.

Idempotent — safe to run more than once. PR #3 will introduce Alembic and
this script will become obsolete.

Usage (from automated-blog-system/):
    python -m scripts.migrate_add_ghost_columns
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text  # noqa: E402

from src.main import create_app  # noqa: E402
from src.models.user import db  # noqa: E402

NEW_COLUMNS = {
    "ghost_post_id": "VARCHAR(64)",
    "published_url": "VARCHAR(500)",
    "editorial_verdict": "VARCHAR(20) DEFAULT 'PENDING'",
}


def run() -> None:
    app = create_app()
    with app.app_context():
        # Ensure all tables exist before trying to ALTER one of them.
        # Safe: create_all() is a no-op for tables that already exist.
        db.create_all()

        insp = inspect(db.engine)
        if "articles" not in insp.get_table_names():
            print("❌ 'articles' table still missing after create_all(); "
                  "check that src.models.product is importable.")
            return

        existing = {c["name"] for c in insp.get_columns("articles")}
        added = []
        with db.engine.begin() as conn:
            for col, ddl in NEW_COLUMNS.items():
                if col in existing:
                    continue
                conn.execute(text(f"ALTER TABLE articles ADD COLUMN {col} {ddl}"))
                added.append(col)
        if added:
            print(f"✅ Added columns to articles: {', '.join(added)}")
        else:
            print("ℹ️  All Ghost columns already present; nothing to do.")


if __name__ == "__main__":
    run()
