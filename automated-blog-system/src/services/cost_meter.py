"""CostMeter (PR #3).

One source of truth for per-article and per-month spend. Every LLM call
that touches the pipeline lands here as a ``cost_events`` row.

The hot path:

    CostMeter.record(article_id, stage, model, prompt_tokens, completion_tokens)

returns the call's USD cost as a :class:`Decimal`, increments
``Article.cost_usd`` and the current-month ``Budget.spent_usd`` in the
same transaction, and writes the ``cost_events`` row.

Querying:

    CostMeter.total_for_article(article_id)
    CostMeter.total_for_month("YYYY-MM")

Budget gates (PR #3 §3.3):

    CostMeter.is_article_over_budget(article_id) -> bool
    CostMeter.is_month_over_budget(month) -> bool

Wrapping LLM call sites in CrewAI is a future hook — this service exposes
the API the wrapper needs (and is what the acceptance tests exercise
directly without involving CrewAI).
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import Iterator, Optional

from sqlalchemy import func

from src.models.observability import Budget, CostEvent
from src.models.product import Article
from src.models.user import db
from src.services.model_rates import cost_for_call


# Default monthly cap (USD) when no Budget row exists yet — sourced from
# GOALS.md.
DEFAULT_MONTHLY_CAP_USD = Decimal("100.00")


class BudgetExceeded(RuntimeError):
    """Raised when a flow tries to start while the cap is reached."""


def _current_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def _ensure_budget_row(month: str) -> Budget:
    row = Budget.query.filter_by(month=month).first()
    if row is None:
        row = Budget(month=month, cap_usd=DEFAULT_MONTHLY_CAP_USD, spent_usd=Decimal("0"))
        db.session.add(row)
        db.session.flush()
    return row


class CostMeter:
    """Stateless namespace — all methods operate on the active Flask DB session."""

    @staticmethod
    def record(
        article_id: Optional[int],
        stage: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> Decimal:
        """Record one LLM call. Returns the USD cost."""
        cost = cost_for_call(model, prompt_tokens, completion_tokens)

        event = CostEvent(
            article_id=article_id,
            stage=stage,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost,
        )
        db.session.add(event)

        # Bump per-article and per-month running totals atomically.
        if article_id is not None:
            article = db.session.get(Article, article_id)
            if article is not None:
                current = Decimal(article.cost_usd or 0)
                article.cost_usd = current + cost

        budget = _ensure_budget_row(_current_month())
        budget.spent_usd = Decimal(budget.spent_usd or 0) + cost

        db.session.commit()
        return cost

    @staticmethod
    def current_month() -> str:
        """Current month key (``YYYY-MM``, UTC). Public alias for callers
        that want CostMeter as the single source of truth for month logic."""
        return _current_month()

    @staticmethod
    def total_for_article(article_id: int) -> Decimal:
        total = (
            db.session.query(func.coalesce(func.sum(CostEvent.cost_usd), 0))
            .filter(CostEvent.article_id == article_id)
            .scalar()
        )
        return Decimal(total or 0)

    @staticmethod
    def total_for_month(month: str) -> Decimal:
        """Return total spend for ``month`` (``YYYY-MM``).

        Reads from the ``budgets`` row, which is kept in lockstep with
        ``cost_events`` writes inside :meth:`record`. Returns 0 if no
        spend has been recorded for that month yet.
        """
        row = Budget.query.filter_by(month=month).first()
        if row is None:
            return Decimal(0)
        return Decimal(row.spent_usd or 0)

    # ---- budget gates ------------------------------------------------------

    @staticmethod
    def is_article_over_budget(article_id: int) -> bool:
        article = db.session.get(Article, article_id)
        if article is None:
            return False
        cap = Decimal(article.cost_budget_usd or 0)
        spent = Decimal(article.cost_usd or 0)
        return spent > cap

    @staticmethod
    def is_month_over_budget(month: Optional[str] = None) -> bool:
        m = month or _current_month()
        row = Budget.query.filter_by(month=m).first()
        if row is None:
            return False
        return Decimal(row.spent_usd or 0) >= Decimal(row.cap_usd or 0)

    @staticmethod
    def assert_can_start_flow() -> None:
        """Raise :class:`BudgetExceeded` if the monthly cap is reached.

        Called by :class:`BlogCreationFlow` before kicking off a new article.
        """
        if CostMeter.is_month_over_budget():
            spent = CostMeter.total_for_month(_current_month())
            raise BudgetExceeded(
                f"Monthly cap reached for {_current_month()} (spent ${spent}). "
                "Refusing to start a new flow."
            )

    # ---- context manager (placeholder for full CrewAI wrapping later) -----

    @staticmethod
    @contextmanager
    def track(article_id: Optional[int], stage: str) -> Iterator["CostMeter"]:
        """Yield a tracker bound to ``(article_id, stage)``.

        Currently the body just calls back into :meth:`record`. Wiring this
        into CrewAI's LLM hooks is deferred — the API is shaped so the
        eventual wrapper can call ``meter.record(model, p_tokens, c_tokens)``
        for each LLM round-trip without changing call-site signatures.
        """
        class _Tracker:
            def record(self, model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
                return CostMeter.record(
                    article_id, stage, model, prompt_tokens, completion_tokens
                )

        yield _Tracker()  # type: ignore[misc]


__all__ = ["CostMeter", "BudgetExceeded", "DEFAULT_MONTHLY_CAP_USD"]
