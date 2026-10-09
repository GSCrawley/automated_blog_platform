"""Action handlers + the risk gate (PR #21).

Every state change the overseer layer can make lives here, in one
reviewable file. Each handler returns ``(result, undo)`` — ``undo`` is a
JSON recipe stored on the action row so a human can reverse it.

Risk gate
---------
``AUTO_SAFE`` is the *only* set of handlers that may run without a human
``approve``. Membership rule: the handler is reversible, spends no money,
touches no live/public surface, and never edits article content. An
overseer requesting ``risk="auto"`` for anything else is downgraded to
``approval`` by :func:`effective_risk`.

Never automatable (by design, not configuration):
- publishing or unpublishing on Ghost
- spending money (Meta campaigns are created PAUSED and still need approval)
- posting publicly (Facebook Page)
- code changes (engineering tickets go to a PR, not a hot patch)
"""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from src.models.overseer import OverseerAction, OverseerControl
from src.models.product import Article
from src.models.user import db

log = logging.getLogger(__name__)

Result = Tuple[Dict[str, Any], Optional[Dict[str, Any]]]
Handler = Callable[[Dict[str, Any]], Result]

AUTO_SAFE = {
    "notify_human",
    "mark_article_error",
    "generate_improvement_proposals",
    "refresh_performance",
    "pause_pipeline",
    "reject_action",
}

# Injection seam for tests and for alternative runners (e.g. a Grok Bot
# routine that re-runs the flow on its own cloud computer).
FLOW_RUNNER: Optional[Callable[[int], None]] = None


class ActionError(RuntimeError):
    pass


def effective_risk(kind: str, requested: str) -> str:
    return "auto" if (requested == "auto" and kind in AUTO_SAFE) else "approval"


def _article(params: Dict[str, Any]) -> Article:
    a = db.session.get(Article, int(params["article_id"]))
    if a is None:
        raise ActionError(f"article {params.get('article_id')} not found")
    return a


# ----------------------------------------------------------------- handlers
def h_notify_human(params):
    return {"surfaced": True, "where": "/api/overseer/findings"}, None


def h_engineering_ticket(params):
    # Approval moves the ticket into the engineering queue that a coding
    # agent consumes (GET /api/overseer/engineering-queue).
    return {"queued": True, "area": params.get("area")}, None


def h_mark_article_error(params):
    a = _article(params)
    undo = {"kind": "restore_article_fields", "article_id": a.id, "stage_status": a.stage_status, "last_error": a.last_error}
    a.stage_status = "error"
    a.last_error = f"[overseer] no stage transition for >6h at {a.current_stage}; marked error. " + (a.last_error or "")
    return {"article_id": a.id, "stage_status": "error"}, undo


def _retries_used(article_id: int) -> int:
    return int(OverseerControl.get(f"retries:{article_id}", 0) or 0)


def _default_flow_runner(article_id: int) -> None:  # pragma: no cover - needs CrewAI
    from flask import current_app

    app = current_app._get_current_object()

    def _run():
        with app.app_context():
            from core.crewai_system.blog_creation_flow import BlogCreationFlow

            a = db.session.get(Article, article_id)
            BlogCreationFlow().kickoff(
                inputs={
                    "niche": a.niche.name if a.niche else "",
                    "blog_instance_id": str(a.niche_id or ""),
                    "current_article_id": a.id,
                    "current_topic": a.product.name if a.product else a.title,
                }
            )

    threading.Thread(target=_run, name=f"overseer-retry-{article_id}", daemon=True).start()


def h_retry_article(params):
    a = _article(params)
    budget = int(params.get("budget", 2))
    used = _retries_used(a.id)
    if used >= budget:
        raise ActionError(f"retry budget exhausted ({used}/{budget}); archive or swap the offer instead")
    undo = {"kind": "restore_article_fields", "article_id": a.id, "stage_status": a.stage_status, "current_stage": a.current_stage}
    a.stage_status = "pending"
    a.current_stage = "stage_0"
    a.last_transition_at = datetime.utcnow()
    OverseerControl.set(f"retries:{a.id}", used + 1)
    db.session.commit()
    (FLOW_RUNNER or _default_flow_runner)(a.id)
    return {"article_id": a.id, "retry": used + 1, "budget": budget}, undo


def h_archive_article(params):
    a = _article(params)
    undo = {"kind": "restore_article_fields", "article_id": a.id, "status": a.status}
    a.status = "archived"
    return {"article_id": a.id, "status": "archived", "reason": params.get("reason")}, undo


def h_unpublish_article(params):
    from src.services.ghost_service import GhostService

    a = _article(params)
    if not a.ghost_post_id:
        raise ActionError("article has no ghost_post_id")
    GhostService().set_status(a.ghost_post_id, "draft")
    undo = {"kind": "manual", "note": "re-publish via /api/review/<id>/publish after fixing the verdict"}
    a.status = "draft"
    a.current_stage = "awaiting_human_review"
    return {"article_id": a.id, "ghost_status": "draft"}, undo


def h_generate_improvement_proposals(params):
    from src.services.feedback_engine import generate_improvement_proposals

    try:
        created = generate_improvement_proposals(int(params["article_id"]))
    except Exception as e:  # no blueprint yet, etc.
        return {"created": 0, "skipped": str(e)[:200]}, None
    return {"created": len(created), "review_at": "/api/review"}, None


def h_refresh_performance(params):
    from src.services.analytics.ingest import refresh_performance

    n = refresh_performance(params.get("niche_id"))
    return {"articles_refreshed": n}, None


def h_pause_pipeline(params):
    prev = OverseerControl.get("pipeline_paused")
    OverseerControl.set("pipeline_paused", {"paused": True, "reason": params.get("reason", "overseer"), "at": datetime.utcnow().isoformat()})
    return {"paused": True}, {"kind": "set_control", "key": "pipeline_paused", "value": prev}


def h_resume_pipeline(params):
    prev = OverseerControl.get("pipeline_paused")
    OverseerControl.set("pipeline_paused", {"paused": False, "reason": "resumed by human"}, by="human")
    return {"paused": False}, {"kind": "set_control", "key": "pipeline_paused", "value": prev}


def h_reject_action(params):
    target = db.session.get(OverseerAction, int(params["action_id"]))
    if target and target.status in ("proposed", "approved"):
        target.status = "rejected"
        target.decided_by = "compliance-overseer"
        target.decided_at = datetime.utcnow()
    return {"rejected": params["action_id"]}, None


def h_create_meta_campaign_draft(params):
    from src.overseers.compliance import is_amazon_url
    from src.services.meta_ai import MetaMarketingClient

    dest = params.get("destination_url", "")
    if not dest or is_amazon_url(dest):
        raise ActionError("destination must be the blog article URL, never Amazon")
    a = _article(params)
    body = MetaMarketingClient().create_campaign_draft(
        f"[overseer] {a.title}"[:250], objective=params.get("objective", "OUTCOME_TRAFFIC")
    )
    cid = body.get("id")
    return (
        {"campaign_id": cid, "status": "PAUSED", "destination_url": dest,
         "next": "Add ad set, creative and budget in Ads Manager, then activate."},
        {"kind": "meta_campaign_status", "campaign_id": cid, "status": "ARCHIVED"},
    )


def h_distribute_to_facebook_page(params):
    from src.services.meta_ai import MetaMarketingClient

    body = MetaMarketingClient().post_link_to_page(params.get("message", ""), params["link"])
    return {"post_id": body.get("id")}, {"kind": "manual", "note": "delete the Page post in Meta Business Suite"}


HANDLERS: Dict[str, Handler] = {
    "notify_human": h_notify_human,
    "engineering_ticket": h_engineering_ticket,
    "mark_article_error": h_mark_article_error,
    "retry_article": h_retry_article,
    "archive_article": h_archive_article,
    "unpublish_article": h_unpublish_article,
    "generate_improvement_proposals": h_generate_improvement_proposals,
    "refresh_performance": h_refresh_performance,
    "pause_pipeline": h_pause_pipeline,
    "resume_pipeline": h_resume_pipeline,
    "reject_action": h_reject_action,
    "create_meta_campaign_draft": h_create_meta_campaign_draft,
    "distribute_to_facebook_page": h_distribute_to_facebook_page,
}


def apply_action(action: OverseerAction, *, by: str = "overseer") -> OverseerAction:
    """Run one action through the gate. Commits."""
    if action.status not in ("proposed", "approved"):
        raise ActionError(f"action {action.id} is {action.status}")
    if action.status == "proposed" and action.risk != "auto":
        raise ActionError(f"action {action.id} ({action.kind}) needs approval first")
    handler = HANDLERS.get(action.kind)
    if handler is None:
        raise ActionError(f"no handler for {action.kind}")
    try:
        result, undo = handler(action.params)
        action.status = "applied"
        action.applied_at = datetime.utcnow()
        action.result_json = json.dumps(result, default=str)
        action.undo_json = json.dumps(undo, default=str) if undo else None
        if action.decided_by is None:
            action.decided_by = by
            action.decided_at = action.applied_at
    except Exception as e:
        db.session.rollback()
        action = db.session.get(OverseerAction, action.id)
        action.status = "failed"
        action.result_json = json.dumps({"error": str(e)[:500]})
        log.warning("Overseer action %s (%s) failed: %s", action.id, action.kind, e)
    db.session.commit()
    return action


__all__ = ["AUTO_SAFE", "HANDLERS", "apply_action", "effective_risk", "ActionError"]
