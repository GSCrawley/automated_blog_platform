"""PR #6 — review/publish UI: drift columns + article_revisions table.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-27

Adds:

- ``articles.ghost_updated_at``       — Ghost's reported updated_at, used
                                        for optimistic concurrency on
                                        update_article calls.
- ``articles.last_ghost_sync_hash``   — sha256 of the last (title + html +
                                        meta_description + sorted_tags)
                                        we sent to (or pulled from) Ghost.
                                        Drift detection is "is this hash
                                        still current?"
- ``articles.has_unpushed_changes``   — convenience flag set whenever the
                                        local payload diverges from
                                        ``last_ghost_sync_hash``.
- ``article_revisions``               — append-only snapshots taken
                                        before pull-from-Ghost / push-to-
                                        Ghost / manual edit so any of
                                        those operations is reversible.

Downgrade reverses all of the above.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("articles") as batch:
        batch.add_column(sa.Column("ghost_updated_at", sa.DateTime, nullable=True))
        batch.add_column(sa.Column("last_ghost_sync_hash", sa.String(128), nullable=True))
        batch.add_column(
            sa.Column(
                "has_unpushed_changes",
                sa.Boolean,
                nullable=False,
                server_default=sa.text("0"),
            )
        )

    op.create_table(
        "article_revisions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("snapshot_json", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_article_revisions_article_created",
        "article_revisions",
        ["article_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_article_revisions_article_created", table_name="article_revisions"
    )
    op.drop_table("article_revisions")
    with op.batch_alter_table("articles") as batch:
        batch.drop_column("has_unpushed_changes")
        batch.drop_column("last_ghost_sync_hash")
        batch.drop_column("ghost_updated_at")
