"""Ghost publisher routes.

Endpoints (all under /api/publisher):
    POST /publish/<article_id>   -> publish or update on Ghost
    POST /draft/<article_id>     -> create as draft on Ghost
    GET  /health                 -> verify config + auth without publishing
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify

from src.models.product import Article
from src.models.user import db
from src.services.ghost_service import GhostPublishError, GhostService

logger = logging.getLogger(__name__)
publisher_bp = Blueprint("publisher", __name__)


def _refuse_unless_publishable(article: Article):
    """Enforce APE-71 lesson: Publisher only publishes passing articles."""
    if (article.editorial_verdict or "PENDING").upper() != "PUBLISH":
        return (
            jsonify(
                {
                    "success": False,
                    "error": (
                        f"Article {article.id} editorial_verdict is "
                        f"{article.editorial_verdict!r}; refusing to publish. "
                        "Only articles with verdict 'PUBLISH' may be sent to Ghost."
                    ),
                }
            ),
            409,
        )
    return None


@publisher_bp.route("/health", methods=["GET"])
def health():
    try:
        svc = GhostService()
        # cheap auth check: list one post
        svc._get("/ghost/api/admin/posts/?limit=1")
        return jsonify({"success": True, "ghost": "reachable"})
    except GhostPublishError as e:
        return jsonify({"success": False, "error": str(e)}), 502


@publisher_bp.route("/publish/<int:article_id>", methods=["POST"])
def publish(article_id: int):
    article = Article.query.get_or_404(article_id)
    refusal = _refuse_unless_publishable(article)
    if refusal is not None:
        return refusal

    payload = article.to_headless_contract()
    try:
        svc = GhostService()
        if article.ghost_post_id:
            result = svc.update_article(article.ghost_post_id, payload)
        else:
            result = svc.publish_article(payload)
    except GhostPublishError as e:
        logger.exception("Ghost publish failed for article %s", article_id)
        return jsonify({"success": False, "error": str(e)}), 502

    article.ghost_post_id = result.post_id
    article.published_url = result.url
    article.status = "published"
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "article_id": article.id,
            "post_id": result.post_id,
            "url": result.url,
            "ghost_status": result.status,
        }
    )


@publisher_bp.route("/draft/<int:article_id>", methods=["POST"])
def draft(article_id: int):
    article = Article.query.get_or_404(article_id)
    payload = article.to_headless_contract()
    try:
        result = GhostService().save_draft(payload)
    except GhostPublishError as e:
        logger.exception("Ghost draft failed for article %s", article_id)
        return jsonify({"success": False, "error": str(e)}), 502

    article.ghost_post_id = result.post_id
    article.published_url = result.url
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "article_id": article.id,
            "post_id": result.post_id,
            "url": result.url,
            "ghost_status": result.status,
        }
    )