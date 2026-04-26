"""Deprecated — superseded by Alembic in PR #3.

The Ghost columns (``ghost_post_id``, ``published_url``,
``editorial_verdict``) are part of the baseline migration
``migrations/versions/0001_baseline.py``.

To bring a fresh database up to date::

    cd automated-blog-system
    FLASK_APP=src.main:create_app flask db upgrade
"""
from __future__ import annotations


def run() -> None:
    print(
        "ℹ️  scripts/migrate_add_ghost_columns.py is a no-op since PR #3.\n"
        "    Use:  FLASK_APP=src.main:create_app flask db upgrade"
    )


if __name__ == "__main__":
    run()
