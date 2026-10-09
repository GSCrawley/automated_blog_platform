"""PR #21 — overseer layer tables.

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-09

Creates ``overseer_runs``, ``overseer_findings``, ``overseer_actions`` and
``overseer_controls``. Purely additive; no existing table is altered.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "overseer_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("trigger", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("started_at", sa.DateTime, nullable=False),
        sa.Column("finished_at", sa.DateTime, nullable=True),
        sa.Column("findings_opened", sa.Integer, nullable=False, server_default="0"),
        sa.Column("findings_resolved", sa.Integer, nullable=False, server_default="0"),
        sa.Column("actions_auto_applied", sa.Integer, nullable=False, server_default="0"),
        sa.Column("summary_json", sa.Text, nullable=True),
    )
    op.create_index("ix_overseer_runs_started_at", "overseer_runs", ["started_at"])

    op.create_table(
        "overseer_findings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("fingerprint", sa.String(200), nullable=False),
        sa.Column("overseer", sa.String(40), nullable=False),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(20), nullable=False, server_default="operational"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("evidence_json", sa.Text, nullable=True),
        sa.Column("subject_type", sa.String(40), nullable=True),
        sa.Column("subject_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("first_seen_at", sa.DateTime, nullable=False),
        sa.Column("last_seen_at", sa.DateTime, nullable=False),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("occurrences", sa.Integer, nullable=False, server_default="1"),
        sa.Column("first_run_id", sa.Integer, sa.ForeignKey("overseer_runs.id"), nullable=True),
    )
    op.create_index("ix_overseer_findings_fingerprint", "overseer_findings", ["fingerprint"])
    op.create_index("ix_overseer_findings_overseer", "overseer_findings", ["overseer"])
    op.create_index("ix_overseer_findings_code", "overseer_findings", ["code"])
    op.create_index("ix_overseer_findings_status", "overseer_findings", ["status"])

    op.create_table(
        "overseer_actions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("finding_id", sa.Integer, sa.ForeignKey("overseer_findings.id"), nullable=False),
        sa.Column("kind", sa.String(60), nullable=False),
        sa.Column("risk", sa.String(10), nullable=False, server_default="approval"),
        sa.Column("params_json", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="proposed"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("decided_by", sa.String(100), nullable=True),
        sa.Column("decided_at", sa.DateTime, nullable=True),
        sa.Column("applied_at", sa.DateTime, nullable=True),
        sa.Column("verified_at", sa.DateTime, nullable=True),
        sa.Column("result_json", sa.Text, nullable=True),
        sa.Column("undo_json", sa.Text, nullable=True),
    )
    op.create_index("ix_overseer_actions_finding_id", "overseer_actions", ["finding_id"])
    op.create_index("ix_overseer_actions_status", "overseer_actions", ["status"])

    op.create_table(
        "overseer_controls",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("value_json", sa.Text, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("overseer_controls")
    op.drop_index("ix_overseer_actions_status", table_name="overseer_actions")
    op.drop_index("ix_overseer_actions_finding_id", table_name="overseer_actions")
    op.drop_table("overseer_actions")
    for ix in ("status", "code", "overseer", "fingerprint"):
        op.drop_index(f"ix_overseer_findings_{ix}", table_name="overseer_findings")
    op.drop_table("overseer_findings")
    op.drop_index("ix_overseer_runs_started_at", table_name="overseer_runs")
    op.drop_table("overseer_runs")
