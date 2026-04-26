"""Deprecated — superseded by Alembic in PR #3.

PR #2's ``last_verdict_json`` / ``blueprint_id`` / ``current_stage`` columns
ship in the baseline migration ``migrations/versions/0001_baseline.py``.

To bring a fresh database up to date::

    cd automated-blog-system
    FLASK_APP=src.main:create_app flask db upgrade
"""
from __future__ import annotations


def run() -> None:
    print(
        "ℹ️  scripts/migrate_add_verdict_columns.py is a no-op since PR #3.\n"
        "    Use:  FLASK_APP=src.main:create_app flask db upgrade"
    )


if __name__ == "__main__":
    run()
