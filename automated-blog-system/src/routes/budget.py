"""Budget status route (PR #3).

Single endpoint:

    GET /api/budget/status[?month=YYYY-MM]

Returns the requested month's cap + spend + remaining + per-niche breakdown.
``month`` defaults to the current UTC month.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from src.models.niche import Niche
from src.models.observability import Budget, CostEvent
from src.models.product import Article
from src.models.user import db
from src.services.cost_meter import CostMeter, DEFAULT_MONTHLY_CAP_USD

budget_bp = Blueprint("budget", __name__)


@budget_bp.route("/status", methods=["GET"])
def status():
    month = request.args.get("month") or datetime.utcnow().strftime("%Y-%m")

    row = Budget.query.filter_by(month=month).first()
    cap = Decimal(row.cap_usd) if row else DEFAULT_MONTHLY_CAP_USD
    spent = CostMeter.total_for_month(month)
    remaining = cap - spent

    # Per-niche breakdown for this month, joined via Article.
    rows = (
        db.session.query(
            Niche.id,
            Niche.name,
            func.coalesce(func.sum(CostEvent.cost_usd), 0).label("spent_usd"),
        )
        .outerjoin(Article, Article.niche_id == Niche.id)
        .outerjoin(CostEvent, CostEvent.article_id == Article.id)
        .group_by(Niche.id, Niche.name)
        .all()
    )
    per_niche = [
        {"niche_id": r.id, "niche_name": r.name, "spent_usd": str(Decimal(r.spent_usd or 0))}
        for r in rows
        if Decimal(r.spent_usd or 0) > 0
    ]

    return jsonify(
        {
            "success": True,
            "month": month,
            "cap_usd": str(cap),
            "spent_usd": str(spent),
            "remaining_usd": str(remaining),
            "exhausted": spent >= cap,
            "per_niche": per_niche,
        }
    )
