"""PR #5a — Pattern Library: blueprints + serp_profiles tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-26

Adds the two tables that back the SERP-forensics-driven Pattern Library.

- ``blueprints``     — one row per published Blueprint version. Each row's
                       ``id`` is a stable string (e.g. ``bp_smb_cybersec_v3``)
                       so PR #6's review UI can reference a Blueprint without
                       chasing autoincrement ids across regenerations.
- ``serp_profiles``  — cached :class:`ArticleProfile` per (url, query) within
                       a freshness window. Lets PR #5b's retrieval (and PR
                       #7's feedback engine) read from a normalized table
                       instead of re-scraping.

Downgrade reverses both, leaving PR #1–#4 schema intact.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "blueprints",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("niche_id", sa.Integer, sa.ForeignKey("niches.id"), nullable=True),
        sa.Column("target_query_cluster", sa.Text, nullable=True),  # JSON list
        sa.Column("profile_aggregate", sa.Text, nullable=True),  # JSON dict
        sa.Column("coverage_gaps", sa.Text, nullable=True),  # JSON list
        sa.Column("source_urls", sa.Text, nullable=True),  # JSON list
        sa.Column("confidence_tiers", sa.Text, nullable=True),  # JSON dict {field: tier}
        sa.Column("word_count_lo", sa.Integer, nullable=True),
        sa.Column("word_count_hi", sa.Integer, nullable=True),
        sa.Column("h2_count_lo", sa.Integer, nullable=True),
        sa.Column("h2_count_hi", sa.Integer, nullable=True),
        sa.Column("required_sections", sa.Text, nullable=True),  # JSON list
        sa.Column("min_internal_links", sa.Integer, nullable=False, server_default="0"),
        sa.Column("requires_feature_image", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("requires_schema_markup", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("confidence_tier", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("generated_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("generated_cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("parent_blueprint_id", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_blueprints_niche_generated",
        "blueprints",
        ["niche_id", "generated_at"],
    )

    op.create_table(
        "serp_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("query", sa.String(500), nullable=False),
        sa.Column("profile_json", sa.Text, nullable=False),
        sa.Column("fetched_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(
        "ix_serp_profiles_url_query",
        "serp_profiles",
        ["url", "query"],
        unique=True,
    )

    # Hook articles → blueprints. The column already exists from PR #2 (just
    # a free-form String); we don't promote it to a real FK because Blueprint
    # ids can be regenerated and PR #7's audit story wants the historical
    # snapshot, not a live join.


def downgrade() -> None:
    op.drop_index("ix_serp_profiles_url_query", table_name="serp_profiles")
    op.drop_table("serp_profiles")
    op.drop_index("ix_blueprints_niche_generated", table_name="blueprints")
    op.drop_table("blueprints")
