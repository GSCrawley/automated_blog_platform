"""Observability + budget models (PR #3).

Three tables:

- ``cost_events``       — one row per LLM call. Source of truth for spend.
- ``budgets``           — monthly cap + running spend; from GOALS.md ($100).
- ``editorial_reports`` — one row per Editor run. Replaces PR #2's
                          ``Article.last_verdict_json`` once PR #3 ships;
                          the column stays writable for backwards-compat
                          until PR #4 cleans up.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.models.user import db


class CostEvent(db.Model):
    """One LLM call's cost, attributed to an article + stage."""

    __tablename__ = "cost_events"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=True, index=True)
    stage = db.Column(db.String(40), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    prompt_tokens = db.Column(db.Integer, nullable=False, default=0)
    completion_tokens = db.Column(db.Integer, nullable=False, default=0)
    cost_usd = db.Column(db.Numeric(10, 6), nullable=False, default=Decimal("0"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "article_id": self.article_id,
            "stage": self.stage,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_usd": str(self.cost_usd) if self.cost_usd is not None else "0",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Budget(db.Model):
    """Per-month spend cap.

    ``month`` is ``YYYY-MM``. ``spent_usd`` is a running total kept in sync
    with ``cost_events`` writes — see :class:`CostMeter`.
    """

    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7), nullable=False, unique=True, index=True)  # 'YYYY-MM'
    cap_usd = db.Column(db.Numeric(10, 4), nullable=False, default=Decimal("100.00"))
    spent_usd = db.Column(db.Numeric(10, 4), nullable=False, default=Decimal("0"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        cap = Decimal(self.cap_usd or 0)
        spent = Decimal(self.spent_usd or 0)
        remaining = cap - spent
        return {
            "month": self.month,
            "cap_usd": str(cap),
            "spent_usd": str(spent),
            "remaining_usd": str(remaining),
            "exhausted": spent >= cap,
        }


class EditorialReport(db.Model):
    """Persisted EditorialVerdict — one row per Editor run.

    PR #2 wrote the verdict JSON to ``Article.last_verdict_json``; PR #3
    normalizes it here so the human review queue (PR #6) can show history
    and the feedback engine (PR #7) can correlate verdicts with performance.
    """

    __tablename__ = "editorial_reports"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False, index=True)
    verdict = db.Column(db.String(20), nullable=False)
    blocking_axes = db.Column(db.Text)  # JSON array
    report_json = db.Column(db.Text, nullable=False)
    blueprint_id = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "article_id": self.article_id,
            "verdict": self.verdict,
            "blocking_axes": self.blocking_axes,
            "report_json": self.report_json,
            "blueprint_id": self.blueprint_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


__all__ = ["CostEvent", "Budget", "EditorialReport"]
