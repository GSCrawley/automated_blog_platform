"""One-shot migration: add PR #2's verdict + blueprint + stage columns.

Idempotent — safe to re-run. PR #3 introduces Alembic and this script
becomes obsolete (per ``PRs_2_through_7.md`` working rules).

Usage (from automated-blog-system/):
    python -m scripts.migrate_add_verdict_columns
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
    "last_verdict_json": "TEXT",
    "blueprint_id": "VARCHAR(64)",
    "current_stage": "VARCHAR(40) DEFAULT 'stage_0'",
}


def run() -> None:
    app = create_app()
    with app.app_context():
        db.create_all()
        insp = inspect(db.engine)
        if "articles" not in insp.get_table_names():
            print("❌ 'articles' table missing after create_all().")
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
            print("ℹ️  All PR #2 columns already present; nothing to do.")


if __name__ == "__main__":
    run()
