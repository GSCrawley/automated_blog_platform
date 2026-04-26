"""PR #3 — observability + cost metering + drop wordpress_post_id.

- Drops ``articles.wordpress_post_id`` (dead since PR #1 deprecated WordPress).
- Adds nine ``articles`` columns: ``stage_status``, ``cost_usd``,
  ``cost_budget_usd``, ``research_report_json``, ``strategy_json``,
  ``draft_sections_json``, ``monetization_map_json``, ``last_error``,
  ``last_transition_at``.
- Creates ``cost_events``, ``budgets``, ``editorial_reports`` tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-25
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite needs batch_alter_table to drop/alter columns. Wrapping the
    # additions in the same batch keeps everything in one rebuild.
    with op.batch_alter_table("articles") as batch_op:
        batch_op.drop_column("wordpress_post_id")
        batch_op.add_column(
            sa.Column("stage_status", sa.String(length=20), server_default="pending")
        )
        batch_op.add_column(
            sa.Column("cost_usd", sa.Numeric(10, 4), server_default="0")
        )
        batch_op.add_column(
            sa.Column("cost_budget_usd", sa.Numeric(10, 4), server_default="5")
        )
        batch_op.add_column(sa.Column("research_report_json", sa.Text()))
        batch_op.add_column(sa.Column("strategy_json", sa.Text()))
        batch_op.add_column(sa.Column("draft_sections_json", sa.Text()))
        batch_op.add_column(sa.Column("monetization_map_json", sa.Text()))
        batch_op.add_column(sa.Column("last_error", sa.Text()))
        batch_op.add_column(sa.Column("last_transition_at", sa.DateTime()))

    op.create_table(
        "cost_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("articles.id"),
            nullable=True,
        ),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index(
        "ix_cost_events_article_id", "cost_events", ["article_id"]
    )
    op.create_index(
        "ix_cost_events_created_at", "cost_events", ["created_at"]
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month", sa.String(length=7), nullable=False, unique=True),
        sa.Column(
            "cap_usd", sa.Numeric(10, 4), nullable=False, server_default="100.00"
        ),
        sa.Column(
            "spent_usd", sa.Numeric(10, 4), nullable=False, server_default="0"
        ),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_budgets_month", "budgets", ["month"])

    op.create_table(
        "editorial_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("articles.id"),
            nullable=False,
        ),
        sa.Column("verdict", sa.String(length=20), nullable=False),
        sa.Column("blocking_axes", sa.Text()),
        sa.Column("report_json", sa.Text(), nullable=False),
        sa.Column("blueprint_id", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index(
        "ix_editorial_reports_article_id",
        "editorial_reports",
        ["article_id"],
    )
    op.create_index(
        "ix_editorial_reports_created_at",
        "editorial_reports",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_editorial_reports_created_at", table_name="editorial_reports")
    op.drop_index("ix_editorial_reports_article_id", table_name="editorial_reports")
    op.drop_table("editorial_reports")
    op.drop_index("ix_budgets_month", table_name="budgets")
    op.drop_table("budgets")
    op.drop_index("ix_cost_events_created_at", table_name="cost_events")
    op.drop_index("ix_cost_events_article_id", table_name="cost_events")
    op.drop_table("cost_events")

    with op.batch_alter_table("articles") as batch_op:
        batch_op.drop_column("last_transition_at")
        batch_op.drop_column("last_error")
        batch_op.drop_column("monetization_map_json")
        batch_op.drop_column("draft_sections_json")
        batch_op.drop_column("strategy_json")
        batch_op.drop_column("research_report_json")
        batch_op.drop_column("cost_budget_usd")
        batch_op.drop_column("cost_usd")
        batch_op.drop_column("stage_status")
        batch_op.add_column(sa.Column("wordpress_post_id", sa.Integer()))
