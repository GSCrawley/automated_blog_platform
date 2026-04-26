"""Baseline schema (PR #1 + PR #2 state).

Creates every table that existed when PR #2 shipped: ``user``, ``niches``,
``blog_instances``, ``products``, ``articles`` (with ``wordpress_post_id``,
PR #1 Ghost columns, and PR #2 verdict columns), ``agent_states``,
``agent_tasks``, ``market_data``, ``agent_decisions``.

PR #3's new columns + new tables (``cost_events``, ``budgets``,
``editorial_reports``) live in revision ``0002_pr3_observability``.

Revision ID: 0001
Revises:
Create Date: 2026-04-25
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- user ---------------------------------------------------------------
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False, unique=True),
        sa.Column("email", sa.String(length=120), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime()),
    )

    # ---- niches -------------------------------------------------------------
    op.create_table(
        "niches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("target_keywords", sa.Text()),
        sa.Column("target_audience", sa.Text()),
        sa.Column("monetization_strategy", sa.Text()),
        sa.Column("content_themes", sa.Text()),
        sa.Column("affiliate_networks", sa.Text()),
        sa.Column("competition_level", sa.String(length=20), server_default="medium"),
        sa.Column("profitability_score", sa.Integer(), server_default="0"),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.Column("pipeline_status", sa.String(length=30), server_default="idle"),
        sa.Column("pipeline_message", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    # ---- blog_instances -----------------------------------------------------
    op.create_table(
        "blog_instances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("niche_id", sa.Integer(), sa.ForeignKey("niches.id"), nullable=False),
        sa.Column("assigned_agents", sa.JSON()),
        sa.Column("status", sa.String(length=50), server_default="active"),
        sa.Column("active", sa.Boolean(), server_default=sa.true()),
        sa.Column("selected_at", sa.DateTime()),
        sa.Column("performance_data", sa.JSON()),
        sa.Column("settings", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    # ---- products -----------------------------------------------------------
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(length=100)),
        sa.Column("price", sa.Float()),
        sa.Column("currency", sa.String(length=10), server_default="USD"),
        sa.Column("trend_score", sa.Float(), server_default="0.0"),
        sa.Column("search_volume", sa.Integer(), server_default="0"),
        sa.Column("competition_level", sa.String(length=20), server_default="medium"),
        sa.Column("affiliate_programs", sa.Text()),
        sa.Column("primary_keywords", sa.Text()),
        sa.Column("secondary_keywords", sa.Text()),
        sa.Column("source_url", sa.String(length=500)),
        sa.Column("image_url", sa.String(length=500)),
        sa.Column("niche_id", sa.Integer(), sa.ForeignKey("niches.id"), nullable=True),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    # ---- articles (PR #1 + PR #2 columns; wordpress_post_id still present) --
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("meta_description", sa.String(length=160)),
        sa.Column("keywords", sa.Text()),
        sa.Column("status", sa.String(length=20), server_default="draft"),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("niche_id", sa.Integer(), sa.ForeignKey("niches.id"), nullable=True),
        sa.Column("wordpress_post_id", sa.Integer()),
        sa.Column("ghost_post_id", sa.String(length=64)),
        sa.Column("published_url", sa.String(length=500)),
        sa.Column("editorial_verdict", sa.String(length=20), server_default="PENDING"),
        sa.Column("last_verdict_json", sa.Text()),
        sa.Column("blueprint_id", sa.String(length=64)),
        sa.Column("current_stage", sa.String(length=40), server_default="stage_0"),
        sa.Column("seo_score", sa.Float(), server_default="0.0"),
        sa.Column("readability_score", sa.Float(), server_default="0.0"),
        sa.Column("word_count", sa.Integer(), server_default="0"),
        sa.Column("affiliate_links_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    # ---- agent_states -------------------------------------------------------
    op.create_table(
        "agent_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_name", sa.String(length=100), nullable=False),
        sa.Column("agent_type", sa.String(length=50), nullable=False),
        sa.Column(
            "blog_instance_id",
            sa.Integer(),
            sa.ForeignKey("blog_instances.id"),
            nullable=True,
        ),
        sa.Column("state_data", sa.JSON()),
        sa.Column("last_action", sa.DateTime()),
        sa.Column("status", sa.String(length=20), server_default="idle"),
        sa.Column("performance_metrics", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )

    # ---- agent_tasks --------------------------------------------------------
    op.create_table(
        "agent_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("assigned_agent", sa.String(length=100), nullable=False),
        sa.Column(
            "blog_instance_id",
            sa.Integer(),
            sa.ForeignKey("blog_instances.id"),
            nullable=True,
        ),
        sa.Column("priority", sa.Integer(), server_default="5"),
        sa.Column("status", sa.String(length=20), server_default="pending"),
        sa.Column("task_data", sa.JSON()),
        sa.Column("result_data", sa.JSON()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
    )

    # ---- market_data --------------------------------------------------------
    op.create_table(
        "market_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("data_type", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("product_name", sa.String(length=200)),
        sa.Column("niche_id", sa.Integer(), sa.ForeignKey("niches.id"), nullable=True),
        sa.Column("data_payload", sa.JSON(), nullable=False),
        sa.Column("trend_score", sa.Float(), server_default="0.0"),
        sa.Column("confidence_score", sa.Float(), server_default="0.0"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("expires_at", sa.DateTime()),
    )

    # ---- agent_decisions ----------------------------------------------------
    op.create_table(
        "agent_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agent_name", sa.String(length=100), nullable=False),
        sa.Column("decision_type", sa.String(length=100), nullable=False),
        sa.Column(
            "blog_instance_id",
            sa.Integer(),
            sa.ForeignKey("blog_instances.id"),
            nullable=True,
        ),
        sa.Column("decision_data", sa.JSON(), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), server_default=sa.false()),
        sa.Column("approval_status", sa.String(length=20), server_default="pending"),
        sa.Column("approved_by", sa.String(length=100)),
        sa.Column("impact_level", sa.String(length=20), server_default="low"),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("approved_at", sa.DateTime()),
    )


def downgrade() -> None:
    # FK-aware drop order: children first.
    op.drop_table("agent_decisions")
    op.drop_table("market_data")
    op.drop_table("agent_tasks")
    op.drop_table("agent_states")
    op.drop_table("articles")
    op.drop_table("products")
    op.drop_table("blog_instances")
    op.drop_table("niches")
    op.drop_table("user")
