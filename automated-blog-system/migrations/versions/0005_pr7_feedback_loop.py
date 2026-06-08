"""PR #7 — feedback loop + retroactive editing tables.

Revision ID: 0005
Revises: 65ce81a88136
Create Date: 2026-06-07

Creates:

- ``article_analytics_daily``       — per-(article, date, source) metrics
- ``article_performance``           — 28-day roll-up per article
- ``article_blueprint_snapshots``   — immutable audit trail at publish time
- ``blueprint_proposals``           — human-reviewed field-level proposals
- ``article_improvement_proposals`` — retroactive per-article edit proposals
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0005"
down_revision = "65ce81a88136"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # article_analytics_daily
    # ------------------------------------------------------------------
    op.create_table(
        "article_analytics_daily",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("impressions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ctr", sa.Numeric(8, 6), nullable=False, server_default="0"),
        sa.Column("avg_position", sa.Numeric(8, 2), nullable=True),
        sa.Column("conversions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("revenue_usd", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "article_id", "date", "source", name="uq_analytics_article_date_source"
        ),
    )
    op.create_index(
        "ix_analytics_article_id", "article_analytics_daily", ["article_id"]
    )
    op.create_index(
        "ix_analytics_date", "article_analytics_daily", ["date"]
    )

    # ------------------------------------------------------------------
    # article_performance  (rolled-up 28-day view)
    # ------------------------------------------------------------------
    op.create_table(
        "article_performance",
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), primary_key=True),
        sa.Column("first_published_at", sa.DateTime, nullable=True),
        sa.Column("days_live", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_impressions_28d", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_clicks_28d", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_ctr_28d", sa.Numeric(8, 6), nullable=False, server_default="0"),
        sa.Column("avg_position_28d", sa.Numeric(8, 2), nullable=True),
        sa.Column("total_epc_28d", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("total_revenue_28d", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("roi", sa.Numeric(12, 4), nullable=True),
        sa.Column("performance_tier", sa.String(10), nullable=False, server_default="'tbd'"),
        sa.Column(
            "refreshed_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # ------------------------------------------------------------------
    # article_blueprint_snapshots  (immutable audit trail)
    # ------------------------------------------------------------------
    op.create_table(
        "article_blueprint_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column("blueprint_id", sa.String(64), nullable=False),
        sa.Column("blueprint_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("profile_aggregate_json", sa.Text, nullable=True),
        sa.Column("confidence_tiers_json", sa.Text, nullable=True),
        sa.Column("coverage_gaps_json", sa.Text, nullable=True),
        sa.Column(
            "snapshotted_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_blueprint_snapshots_article_id",
        "article_blueprint_snapshots",
        ["article_id"],
    )

    # ------------------------------------------------------------------
    # blueprint_proposals
    # ------------------------------------------------------------------
    op.create_table(
        "blueprint_proposals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("niche_id", sa.Integer, sa.ForeignKey("niches.id"), nullable=True),
        sa.Column("blueprint_id", sa.String(64), nullable=False),
        sa.Column("blueprint_field", sa.String(80), nullable=False),
        sa.Column("current_value_json", sa.Text, nullable=False),
        sa.Column("proposed_value_json", sa.Text, nullable=False),
        sa.Column("evidence_json", sa.Text, nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column("reviewed_by", sa.String(100), nullable=True),
        sa.Column("reviewed_at", sa.DateTime, nullable=True),
        sa.Column("resulting_blueprint_id", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_blueprint_proposals_niche_status",
        "blueprint_proposals",
        ["niche_id", "status"],
    )

    # ------------------------------------------------------------------
    # article_improvement_proposals
    # ------------------------------------------------------------------
    op.create_table(
        "article_improvement_proposals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("article_id", sa.Integer, sa.ForeignKey("articles.id"), nullable=False),
        sa.Column(
            "blueprint_proposal_id",
            sa.Integer,
            sa.ForeignKey("blueprint_proposals.id"),
            nullable=True,
        ),
        sa.Column("blueprint_field", sa.String(80), nullable=False),
        sa.Column("current_value_json", sa.Text, nullable=False),
        sa.Column("recommended_value_json", sa.Text, nullable=False),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("evidence_json", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column("dismissed_reason", sa.Text, nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("reviewed_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint(
            "article_id",
            "blueprint_field",
            "status",
            name="uq_improvement_proposals_article_field_status",
        ),
    )
    op.create_index(
        "ix_improvement_proposals_article_status",
        "article_improvement_proposals",
        ["article_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_improvement_proposals_article_status",
        table_name="article_improvement_proposals",
    )
    op.drop_table("article_improvement_proposals")

    op.drop_index("ix_blueprint_proposals_niche_status", table_name="blueprint_proposals")
    op.drop_table("blueprint_proposals")

    op.drop_index(
        "ix_blueprint_snapshots_article_id", table_name="article_blueprint_snapshots"
    )
    op.drop_table("article_blueprint_snapshots")

    op.drop_table("article_performance")

    op.drop_index("ix_analytics_date", table_name="article_analytics_daily")
    op.drop_index("ix_analytics_article_id", table_name="article_analytics_daily")
    op.drop_table("article_analytics_daily")
