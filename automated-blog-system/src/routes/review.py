"""Human-in-the-loop review + publish routes (PR #6).

The pipeline's terminal state is ``awaiting_human_review`` (PR #2 invariant).
This blueprint is the surface that turns reviewer intent into Ghost writes.

Endpoints (all under ``/api/review``):

    GET    /queue
    GET    /<article_id>
    PATCH  /<article_id>
    POST   /<article_id>/publish
    POST   /<article_id>/unpublish
    GET    /<article_id>/ghost
    POST   /<article_id>/pull-from-ghost
    POST   /<article_id>/push-to-ghost

Concurrency: a per-article :class:`threading.Lock` (keyed by article_id)
serializes PATCH, publish, pull-from-Ghost, and push-to-Ghost. The dict of
locks itself is guarded by a single meta-lock. This is good enough for
single-instance Flask; PR #7+ revisits when we move to a multi-process
WSGI server.

Error envelope follows PR #1's convention:
``{"success": false, "error": "<human-readable>"}``.

Status codes:
    400 — validation failure on PATCH
    403 — article not in a reviewable state
    404 — article not found
    409 — verdict gate failure or missing ``ghost_post_id`` where required
    502 — upstream Ghost API failure
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, jsonify, request

from src.models.observability import ArticleRevision, CostEvent, EditorialReport
from src.models.product import Article
from src.models.user import db
from src.routes.publisher import publish_article_now
from src.services.ghost_service import (
    GhostPublishError,
    GhostService,
    compute_content_hash,
    diff_payloads,
    extract_ghost_payload,
)

logger = logging.getLogger(__name__)
review_bp = Blueprint("review", __name__)


# ---------------------------------------------------------------------------
# Per-article locks
# ---------------------------------------------------------------------------

_article_locks: Dict[int, threading.Lock] = {}
_locks_meta_lock = threading.Lock()


def _article_lock(article_id: int) -> threading.Lock:
    with _locks_meta_lock:
        lock = _article_locks.get(article_id)
        if lock is None:
            lock = threading.Lock()
            _article_locks[article_id] = lock
        return lock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_PATCHABLE_FIELDS = (
    "title",
    "slug",
    "content",
    "summary",
    "meta_description",
    "keywords",
    "calls_to_action",
    "sections",
    "meta",  # carries feature_image / meta_title
)


def _err(message: str, status: int):
    return jsonify({"success": False, "error": message}), status


def _validate_patch(data: Dict[str, Any]) -> Optional[Tuple[Any, int]]:
    """Validate a PATCH body. Returns ``(error_response, status)`` on failure
    or ``None`` on success."""
    if not isinstance(data, dict):
        return _err("PATCH body must be a JSON object.", 400)
    md = data.get("meta_description")
    if md is not None and len(str(md)) > 160:
        return _err(
            f"meta_description is {len(str(md))} chars; max is 160.",
            400,
        )
    kws = data.get("keywords")
    if kws is not None and (not isinstance(kws, list) or len(kws) > 10):
        return _err("keywords must be a list with at most 10 entries.", 400)
    ctas = data.get("calls_to_action")
    if ctas is not None:
        if not isinstance(ctas, list):
            return _err("calls_to_action must be a list.", 400)
        for cta in ctas:
            target = cta.get("target") if isinstance(cta, dict) else None
            if not target or not (
                str(target).startswith("http://") or str(target).startswith("https://")
            ):
                return _err(
                    "Each calls_to_action.target must be a valid http(s) URL.",
                    400,
                )
    return None


def _apply_patch(article: Article, data: Dict[str, Any]) -> None:
    """Mutate ``article`` from the PATCH body. Caller commits."""
    if "title" in data:
        article.title = str(data["title"])
    if "slug" in data:
        # Slug isn't a column on Article today (it's derived in the headless
        # contract). Persisting it would need a migration — until that
        # arrives, accept and silently ignore so PATCH stays additive.
        pass
    if "content" in data:
        article.content = data["content"] or ""
    if "summary" in data:
        # `summary` isn't a column either; PR #6 expects edits to flow into
        # `meta_description` since that's what GhostService projects to the
        # post's custom_excerpt + meta_description fields. Mirror it.
        article.meta_description = str(data["summary"])[:160]
    if "meta_description" in data:
        article.meta_description = str(data["meta_description"])
    if "keywords" in data:
        article.keywords = json.dumps(list(data["keywords"]))
    if "sections" in data:
        # Sections replace content (per the PR #6 spec — GhostService prefers
        # sections over content when both are present). We persist as the
        # canonical content blob so downstream readers see one source of truth.
        sections = data["sections"] or []
        parts = []
        for s in sections:
            heading = (s.get("heading") or "").strip() if isinstance(s, dict) else ""
            body = (s.get("content") or "").strip() if isinstance(s, dict) else ""
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            if body:
                parts.append(body if body.startswith("<") else f"<p>{body}</p>")
        article.content = "\n".join(parts)
    article.updated_at = datetime.utcnow()
    _refresh_unpushed_flag(article)


def _refresh_unpushed_flag(article: Article) -> None:
    """Recompute ``has_unpushed_changes`` from current local state."""
    if not article.ghost_post_id or not article.last_ghost_sync_hash:
        article.has_unpushed_changes = False
        return
    article.has_unpushed_changes = _local_hash(article) != article.last_ghost_sync_hash


def _local_hash(article: Article) -> str:
    """Return the content hash of the local Article in Ghost-payload shape."""
    payload = article.to_headless_contract()
    post = GhostService._article_to_post(payload, status="published")
    return compute_content_hash(
        title=post.get("title"),
        html=post.get("html"),
        meta_description=post.get("meta_description"),
        tags=post.get("tags") or [],
    )


def _local_ghost_payload(article: Article) -> Dict[str, Any]:
    """Return the payload Ghost would receive if we published *now*."""
    payload = article.to_headless_contract()
    post = GhostService._article_to_post(payload, status="published")
    return extract_ghost_payload(post)


def _snapshot(article: Article, source: str) -> ArticleRevision:
    """Append-only snapshot of the article's current state."""
    rev = ArticleRevision(
        article_id=article.id,
        source=source,
        snapshot_json=json.dumps(article.to_dict(), default=str),
    )
    db.session.add(rev)
    db.session.commit()
    return rev


def _ghost_preview(article: Article) -> Dict[str, Any]:
    """The exact HTML payload Ghost will receive on publish."""
    payload = article.to_headless_contract()
    return GhostService._article_to_post(payload, status="published")


def _editorial_report_summary(article: Article) -> Dict[str, Any]:
    report = (
        EditorialReport.query.filter_by(article_id=article.id)
        .order_by(EditorialReport.created_at.desc())
        .first()
    )
    if report is None:
        return {}
    try:
        full = json.loads(report.report_json or "{}")
    except (TypeError, ValueError):
        full = {}
    axis_scores = {
        r.get("axis"): r.get("score")
        for r in (full.get("axis_reports") or [])
        if isinstance(r, dict)
    }
    return {
        "verdict": report.verdict,
        "blueprint_id": report.blueprint_id,
        "axis_scores": axis_scores,
    }


def _cost_breakdown(article_id: int) -> list[Dict[str, Any]]:
    rows = (
        db.session.query(CostEvent.stage, db.func.sum(CostEvent.cost_usd))
        .filter(CostEvent.article_id == article_id)
        .group_by(CostEvent.stage)
        .all()
    )
    return [{"stage": stage, "cost_usd": str(total or 0)} for stage, total in rows]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@review_bp.route("/queue", methods=["GET"])
def queue():
    """Articles awaiting human review.

    Filter: ``current_stage == 'awaiting_human_review'`` AND
    ``status != 'published'``.

    Query params: ``niche_id``, ``editorial_verdict`` (PUBLISH | REJECT),
    ``limit`` (cap 200), ``offset``, ``sort`` (``updated_at`` | ``cost_usd``).
    """
    q = Article.query.filter(Article.current_stage == "awaiting_human_review")
    q = q.filter((Article.status != "published") | (Article.status.is_(None)))

    niche_id = request.args.get("niche_id")
    if niche_id:
        try:
            q = q.filter(Article.niche_id == int(niche_id))
        except ValueError:
            return _err("niche_id must be an integer.", 400)

    verdict = request.args.get("editorial_verdict")
    if verdict:
        q = q.filter(Article.editorial_verdict == verdict.upper())

    sort = (request.args.get("sort") or "updated_at").lower()
    if sort == "cost_usd":
        q = q.order_by(Article.cost_usd.desc().nullslast(), Article.id.desc())
    else:
        q = q.order_by(Article.updated_at.desc().nullslast(), Article.id.desc())

    try:
        limit = max(1, min(200, int(request.args.get("limit", 50))))
        offset = max(0, int(request.args.get("offset", 0)))
    except (TypeError, ValueError):
        limit, offset = 50, 0

    total = q.count()
    rows = q.limit(limit).offset(offset).all()

    out = []
    for a in rows:
        out.append(
            {
                "id": a.id,
                "title": a.title,
                "niche_id": a.niche_id,
                "niche_name": a.niche.name if a.niche else None,
                "editorial_verdict": a.editorial_verdict,
                "current_stage": a.current_stage,
                "word_count": a.word_count,
                "cost_usd": str(a.cost_usd) if a.cost_usd is not None else "0",
                "blueprint_id": a.blueprint_id,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                "editorial_report_summary": _editorial_report_summary(a),
            }
        )
    return jsonify(
        {"success": True, "articles": out, "total": total, "limit": limit, "offset": offset}
    )


@review_bp.route("/<int:article_id>", methods=["GET"])
def get_article(article_id: int):
    """Full payload everything the review UI needs in one round-trip."""
    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)

    if article.current_stage in ("stage_0", "stage_0_5_blueprint_selected", "stage_1_strategy", "stage_2_creation"):
        # In-flight — readable but not actionable. Caller can still GET to
        # show progress, but PATCH/publish refuse below.
        pass

    headless = article.to_headless_contract()

    # Stage outputs (parsed JSON for the dashboard).
    def _parse(raw):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return raw

    return jsonify(
        {
            "success": True,
            "article": article.to_dict(),
            "headless_contract": headless,
            "ghost_preview": _ghost_preview(article),
            "editorial_report": _parse(article.last_verdict_json),
            "blueprint": {"id": article.blueprint_id} if article.blueprint_id else None,
            "stage_outputs": {
                "research_report": _parse(article.research_report_json),
                "strategy": _parse(article.strategy_json),
                "draft_sections": _parse(article.draft_sections_json),
                "monetization_map": _parse(article.monetization_map_json),
            },
            "cost_breakdown": _cost_breakdown(article.id),
            "ghost_sync": {
                "post_id": article.ghost_post_id,
                "published_url": article.published_url,
                "last_sync_hash": article.last_ghost_sync_hash,
                "drift_detected": bool(article.has_unpushed_changes),
                "ghost_updated_at": article.ghost_updated_at.isoformat()
                if article.ghost_updated_at
                else None,
            },
        }
    )


@review_bp.route("/<int:article_id>", methods=["PATCH"])
def patch_article(article_id: int):
    """User edits before publish — local-only, no Ghost write."""
    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)

    data = request.get_json() or {}
    err = _validate_patch(data)
    if err is not None:
        return err

    with _article_lock(article_id):
        _apply_patch(article, data)
        db.session.commit()
        return get_article(article_id)


@review_bp.route("/<int:article_id>/publish", methods=["POST"])
def publish(article_id: int):
    """The only human-triggered publish path."""
    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)

    if (article.editorial_verdict or "PENDING").upper() != "PUBLISH":
        return _err(
            f"Article {article.id} editorial_verdict is "
            f"{article.editorial_verdict!r}; only verdict='PUBLISH' may be sent to Ghost.",
            409,
        )

    with _article_lock(article_id):
        try:
            body = publish_article_now(article)
            return jsonify(body)
        except PermissionError as e:
            return _err(str(e), 409)
        except GhostPublishError as e:
            logger.exception("Ghost publish failed for article %s", article_id)
            return _err(str(e), 502)


@review_bp.route("/<int:article_id>/unpublish", methods=["POST"])
def unpublish(article_id: int):
    """Flip Ghost post to draft + mark Article.status='draft' locally."""
    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)
    if not article.ghost_post_id:
        return _err("Article has no ghost_post_id; nothing to unpublish.", 409)

    with _article_lock(article_id):
        try:
            GhostService().set_status(article.ghost_post_id, "draft")
        except GhostPublishError as e:
            logger.exception("Ghost set_status failed for article %s", article_id)
            return _err(str(e), 502)
        article.status = "draft"
        db.session.commit()
        return jsonify({"success": True, "ghost_status": "draft"})


@review_bp.route("/<int:article_id>/ghost", methods=["GET"])
def get_from_ghost(article_id: int):
    """Pull live Ghost post + drift comparison."""
    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)
    if not article.ghost_post_id:
        return _err("Article has no ghost_post_id; nothing to fetch.", 409)

    try:
        ghost_raw = GhostService().fetch_post(article.ghost_post_id)
    except GhostPublishError as e:
        logger.exception("Ghost fetch failed for article %s", article_id)
        return _err(str(e), 502)

    ghost_payload = extract_ghost_payload(ghost_raw)
    local_payload = _local_ghost_payload(article)
    local_hash = _local_hash(article)
    ghost_hash = compute_content_hash(
        title=ghost_payload.get("title"),
        html=ghost_payload.get("html"),
        meta_description=ghost_payload.get("meta_description"),
        tags=ghost_payload.get("tags") or [],
    )
    diverging = diff_payloads(local_payload, ghost_payload)
    drift = bool(diverging)

    return jsonify(
        {
            "success": True,
            "local": article.to_headless_contract(),
            "ghost": ghost_payload,
            "drift_detected": drift,
            "diverging_fields": diverging,
            "local_hash": local_hash,
            "ghost_hash": ghost_hash,
            "last_sync_hash": article.last_ghost_sync_hash,
        }
    )


@review_bp.route("/<int:article_id>/pull-from-ghost", methods=["POST"])
def pull_from_ghost(article_id: int):
    """Overwrite local Article with Ghost's current version; snapshot first."""
    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)
    if not article.ghost_post_id:
        return _err("Article has no ghost_post_id; nothing to pull.", 409)

    with _article_lock(article_id):
        revision = _snapshot(article, source="pre_pull_from_ghost")

        try:
            ghost_raw = GhostService().fetch_post(
                article.ghost_post_id, use_cache=False
            )
        except GhostPublishError as e:
            return _err(str(e), 502)

        ghost = extract_ghost_payload(ghost_raw)

        article.title = ghost.get("title") or article.title
        article.content = ghost.get("html") or ""
        article.meta_description = ghost.get("meta_description") or ""
        tags = [t.get("name") for t in ghost.get("tags") or [] if isinstance(t, dict)]
        article.keywords = json.dumps([t for t in tags if t])
        article.last_ghost_sync_hash = compute_content_hash(
            title=ghost.get("title"),
            html=ghost.get("html"),
            meta_description=ghost.get("meta_description"),
            tags=ghost.get("tags") or [],
        )
        if ghost.get("updated_at"):
            try:
                article.ghost_updated_at = datetime.fromisoformat(
                    ghost["updated_at"].replace("Z", "+00:00")
                )
            except (TypeError, ValueError):
                pass
        article.has_unpushed_changes = False
        article.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "revision_id": revision.id,
                "pulled_fields": ["title", "html", "meta_description", "tags"],
            }
        )


@review_bp.route("/<int:article_id>/push-to-ghost", methods=["POST"])
def push_to_ghost(article_id: int):
    """Push current local edits to Ghost via update_article."""
    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)
    if not article.ghost_post_id:
        return _err("Article has no ghost_post_id; cannot push.", 409)
    if (article.editorial_verdict or "PENDING").upper() != "PUBLISH":
        return _err(
            f"Article {article.id} editorial_verdict is "
            f"{article.editorial_verdict!r}; only verdict='PUBLISH' may be pushed.",
            409,
        )

    with _article_lock(article_id):
        # Snapshot what's about to be overwritten on the Ghost side, so the
        # user can roll back.
        revision = _snapshot(article, source="pre_push_to_ghost")

        try:
            body = publish_article_now(article)
        except PermissionError as e:
            return _err(str(e), 409)
        except GhostPublishError as e:
            logger.exception("Ghost push failed for article %s", article_id)
            return _err(str(e), 502)

        body["revision_id"] = revision.id
        return jsonify(body)



# ---------------------------------------------------------------------------
# Improvement proposal sub-routes  (PR #7 retroactive editing)
# ---------------------------------------------------------------------------


@review_bp.route("/<int:article_id>/improvements", methods=["GET"])
def get_improvements(article_id: int):
    """Return pending improvement proposals for an article, sorted by
    evidence strength (effect_size desc, then id asc as tiebreaker)."""
    from src.models.analytics import ArticleImprovementProposal
    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)

    status_filter = request.args.get("status", "pending")
    q = ArticleImprovementProposal.query.filter_by(article_id=article_id)
    if status_filter != "all":
        q = q.filter(ArticleImprovementProposal.status == status_filter)

    proposals = q.order_by(ArticleImprovementProposal.generated_at.desc()).all()

    # Sort by effect_size desc (best evidence first).
    def _effect(p):
        ev = p.evidence()
        return float(ev.get("effect_size", 0) or 0)

    proposals.sort(key=_effect, reverse=True)

    return jsonify(
        {
            "success": True,
            "article_id": article_id,
            "proposals": [p.to_dict() for p in proposals],
        }
    )


@review_bp.route("/<int:article_id>/improvements/generate", methods=["POST"])
def generate_improvements(article_id: int):
    """On-demand: generate conformance-gap improvement proposals for one article."""
    from src.services.feedback_engine import generate_improvement_proposals

    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)

    try:
        proposals = generate_improvement_proposals(article_id)
        return jsonify(
            {
                "success": True,
                "article_id": article_id,
                "proposals_created": len(proposals),
                "proposals": [p.to_dict() for p in proposals],
            }
        )
    except Exception:
        logger.exception("generate_improvements failed for article %d", article_id)
        return _err("Failed to generate improvement proposals.", 500)


@review_bp.route(
    "/<int:article_id>/improvements/<int:proposal_id>/apply", methods=["POST"]
)
def apply_improvement(article_id: int, proposal_id: int):
    """Apply a recommended change to the local Article row.

    Writes the change, sets ``has_unpushed_changes=True``, marks the
    proposal ``status='applied'``.
    """
    from src.models.analytics import ArticleImprovementProposal

    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)

    proposal = ArticleImprovementProposal.query.get(proposal_id)
    if proposal is None or proposal.article_id != article_id:
        return _err(f"Proposal {proposal_id} not found for article {article_id}.", 404)
    if proposal.status != "pending":
        return _err(
            f"Proposal is already '{proposal.status}'; only pending proposals can be applied.",
            409,
        )

    with _article_lock(article_id):
        patch = _build_patch_from_proposal(proposal, article)
        if patch:
            err = _validate_patch(patch)
            if err is not None:
                return err
            _apply_patch(article, patch)

        # PR #7 reminder-system behavior: mark local row as needing a push even
        # when no auto-patch is performed.
        if article.ghost_post_id:
            article.has_unpushed_changes = True
            article.updated_at = datetime.utcnow()

        proposal.status = "applied"
        proposal.reviewed_at = datetime.utcnow()
        db.session.commit()

    return get_article(article_id)


@review_bp.route(
    "/<int:article_id>/improvements/<int:proposal_id>/dismiss", methods=["POST"]
)
def dismiss_improvement(article_id: int, proposal_id: int):
    """Dismiss a proposal with an optional reason."""
    from src.models.analytics import ArticleImprovementProposal

    article = Article.query.get(article_id)
    if article is None:
        return _err(f"Article {article_id} not found.", 404)

    proposal = ArticleImprovementProposal.query.get(proposal_id)
    if proposal is None or proposal.article_id != article_id:
        return _err(f"Proposal {proposal_id} not found for article {article_id}.", 404)
    if proposal.status != "pending":
        return _err(
            f"Proposal is already '{proposal.status}'; only pending proposals can be dismissed.",
            409,
        )

    body = request.get_json() or {}
    proposal.status = "dismissed"
    proposal.dismissed_reason = str(body.get("reason", ""))
    proposal.reviewed_at = datetime.utcnow()
    db.session.commit()

    return jsonify(
        {"success": True, "proposal_id": proposal_id, "status": "dismissed"}
    )


def _build_patch_from_proposal(proposal, article: Article) -> dict:
    """Translate a proposal's recommended_value into a PATCH body.

    All Blueprint fields that improvement proposals operate on require
    substantive content rewrites that cannot be auto-applied (word count,
    H2 structure, FAQ insertion, comparison table, image assets, schema
    markup). This function intentionally returns an empty dict for every
    field: the ``apply`` route marks the proposal applied and sets
    ``has_unpushed_changes = True`` to signal the human editor that
    attention is needed, but the actual edit remains the human's
    responsibility. The proposal card in ArticleReview.jsx shows the
    current vs recommended value so the editor knows exactly what to change.
    """
    # All current Blueprint fields require human content edits — see docstring.
    return {}  # noqa: RET504


__all__ = ["review_bp", "publish_article_now"]
