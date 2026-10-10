"""Author-model gate: Muse Spark for the author agent after the system is verified.

Decision (Gideon, Oct 9, 2026): the author agent moves to Meta's Muse Spark
only once the whole system has been verified to work end to end. Until then
it stays on the current default (CrewAI's OpenAI default, gpt-4o-mini). Only
the author agent switches; the monetization specialist and the research
crews keep the cheaper default.

"Verified" is deterministic and checked by the Chief on every cycle:

1. Every overseer ran cleanly in this cycle (no ``overseer_crashed``).
2. No open critical or high findings anywhere in the overseer layer.
3. GOALS.md first-blog Definition of Done, as positive evidence:
   - at least one published article with a live URL on the Article record,
   - the distribution routine fired at least once (an applied or verified
     ``distribute_to_facebook_page`` action),
   - Search Console impressions recorded for a live article.
4. Money is observed end to end:
   - CrewAI generation spend is metered (``crewai_generation`` cost events),
   - affiliate earnings data has been ingested at least once.
5. ``META_MODEL_API_KEY`` is configured.
6. Checks 1-5 have held continuously for ``AUTHOR_MODEL_STABLE_HOURS``
   (default 24) across overseer cycles, so one lucky cycle can't flip it.

When all six pass, the gate writes ``OverseerControl["author_llm"]`` with
``provider="meta"`` and the author agent picks it up on its next crew build.
The switch is sticky: a later fault does not silently flip models mid-run.
A human can revert with ``POST /api/overseer/controls/author-model/revert``
(which also locks the gate until ``.../author-model/rearm``), and the Chief's $100/month burn guard still applies to every call.

``AUTHOR_LLM_PROVIDER`` overrides the gate:
  ``gated``   (default) - behaviour above
  ``default`` - never switch; always the current default
  ``meta``    - force Muse Spark now (skips verification)
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.models.user import db

CONTROL_KEY = "author_llm"
CANDIDATE_KEY = "author_llm_candidate_since"
DEFAULT_STABLE_HOURS = 24


def gate_mode() -> str:
    mode = (os.getenv("AUTHOR_LLM_PROVIDER") or "gated").lower()
    return mode if mode in ("gated", "default", "meta") else "gated"


def _stable_hours() -> float:
    try:
        return float(os.getenv("AUTHOR_MODEL_STABLE_HOURS", DEFAULT_STABLE_HOURS))
    except ValueError:
        return float(DEFAULT_STABLE_HOURS)


def _check(name: str, ok: bool, detail: str = "") -> Dict[str, Any]:
    return {"check": name, "ok": bool(ok), "detail": detail}


def verification_checks(*, crashed_overseers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Return every verification check with its pass/fail state."""
    from flask import current_app
    from sqlalchemy import func

    from src.models.analytics import ArticleAnalyticsDaily
    from src.models.observability import CostEvent
    from src.models.overseer import OverseerAction, OverseerFinding
    from src.models.product import Article

    checks: List[Dict[str, Any]] = []
    crashed = crashed_overseers or []
    checks.append(_check("overseers_healthy", not crashed, ", ".join(crashed)))

    blocking = (
        OverseerFinding.query.filter(OverseerFinding.status == "open")
        .filter(OverseerFinding.severity.in_(("critical", "high")))
        .all()
    )
    checks.append(
        _check(
            "no_open_critical_or_high_findings",
            not blocking,
            "; ".join(f"{r.severity}: {r.code}" for r in blocking[:10]),
        )
    )

    live = (
        Article.query.filter(Article.status == "published")
        .filter(Article.published_url.isnot(None))
        .filter(Article.published_url != "")
        .count()
    )
    checks.append(_check("live_article_on_ghost", live > 0, f"{live} live"))

    distributed = (
        OverseerAction.query.filter(OverseerAction.kind == "distribute_to_facebook_page")
        .filter(OverseerAction.status.in_(("applied", "verified")))
        .count()
    )
    checks.append(_check("distribution_fired", distributed > 0, f"{distributed} distributions"))

    impressions = (
        db.session.query(func.coalesce(func.sum(ArticleAnalyticsDaily.impressions), 0))
        .filter(ArticleAnalyticsDaily.source == "gsc")
        .scalar()
    )
    checks.append(_check("search_impressions_recorded", (impressions or 0) > 0, f"{impressions or 0} impressions"))

    metered = CostEvent.query.filter(CostEvent.stage == "crewai_generation").count()
    checks.append(_check("generation_spend_metered", metered > 0, f"{metered} cost events"))

    affiliate_rows = ArticleAnalyticsDaily.query.filter(ArticleAnalyticsDaily.source == "affiliate").count()
    checks.append(_check("affiliate_earnings_ingested", affiliate_rows > 0, f"{affiliate_rows} rows"))

    key = os.getenv("META_MODEL_API_KEY") or current_app.config.get("META_MODEL_API_KEY")
    checks.append(_check("meta_api_key_configured", bool(key)))
    return checks


def current_author_provider() -> str:
    """Provider the author agent should use right now: ``meta`` or ``default``."""
    mode = gate_mode()
    if mode in ("default", "meta"):
        return mode
    from src.models.overseer import OverseerControl

    state = OverseerControl.get(CONTROL_KEY) or {}
    return "meta" if state.get("provider") == "meta" else "default"


def evaluate(now: datetime, *, crashed_overseers: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run once per overseer cycle. Flips the control when verification holds."""
    from src.models.overseer import OverseerControl

    mode = gate_mode()
    state = OverseerControl.get(CONTROL_KEY) or {}
    if mode != "gated":
        return {"mode": mode, "provider": mode, "switched": False}
    if state.get("provider") == "meta":
        return {"mode": mode, "provider": "meta", "switched": False, "verified_at": state.get("verified_at")}
    if state.get("locked"):
        return {"mode": mode, "provider": "default", "switched": False, "locked": True, "reason": state.get("reason")}

    checks = verification_checks(crashed_overseers=crashed_overseers)
    passing = all(c["ok"] for c in checks)
    stable_for = timedelta(hours=_stable_hours())
    result: Dict[str, Any] = {
        "mode": mode,
        "provider": "default",
        "switched": False,
        "checks": checks,
        "required_stable_hours": stable_for.total_seconds() / 3600,
    }
    if not passing:
        OverseerControl.set(CANDIDATE_KEY, None)
        db.session.commit()
        return result

    since_raw = OverseerControl.get(CANDIDATE_KEY)
    since = datetime.fromisoformat(since_raw) if since_raw else None
    if since is None:
        OverseerControl.set(CANDIDATE_KEY, now.isoformat())
        db.session.commit()
        since = now
    result["passing_since"] = since.isoformat()
    if now - since < stable_for:
        return result

    model = os.getenv("META_TEXT_MODEL", "muse-spark-1.3")
    OverseerControl.set(
        CONTROL_KEY,
        {
            "provider": "meta",
            "model": model,
            "verified_at": now.isoformat(),
            "passing_since": since.isoformat(),
            "checks": [c["check"] for c in checks],
        },
        by="overseer:author_model_gate",
    )
    OverseerControl.set(CANDIDATE_KEY, None)
    db.session.commit()
    result.update({"provider": "meta", "switched": True, "verified_at": now.isoformat()})
    return result


def revert(*, by: str, reason: str) -> Dict[str, Any]:
    from src.models.overseer import OverseerControl

    value = {"provider": "default", "locked": True, "reverted_at": datetime.utcnow().isoformat(), "reason": reason}
    OverseerControl.set(CONTROL_KEY, value, by=by)
    OverseerControl.set(CANDIDATE_KEY, None, by=by)
    db.session.commit()
    return value


def rearm(*, by: str) -> Dict[str, Any]:
    """Clear a human revert so the gate can verify and switch again."""
    from src.models.overseer import OverseerControl

    OverseerControl.set(CONTROL_KEY, None, by=by)
    OverseerControl.set(CANDIDATE_KEY, None, by=by)
    db.session.commit()
    return {"provider": "default", "rearmed_at": datetime.utcnow().isoformat()}


def status() -> Dict[str, Any]:
    from src.models.overseer import OverseerControl

    return {
        "mode": gate_mode(),
        "provider": current_author_provider(),
        "state": OverseerControl.get(CONTROL_KEY),
        "passing_since": OverseerControl.get(CANDIDATE_KEY),
        "required_stable_hours": _stable_hours(),
        "checks": verification_checks(),
    }


__all__ = ["CONTROL_KEY", "current_author_provider", "evaluate", "rearm", "revert", "status", "verification_checks"]
