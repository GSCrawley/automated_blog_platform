"""Flask-side service for running the Editor against a stored Article (PR #2).

Loads an :class:`Article` row, builds the headless-contract dict, picks the
stub Blueprint for the article's niche, runs :func:`EditorCrew.review`, and
persists the verdict + the full report JSON. Sets ``current_stage`` to
``awaiting_human_review`` regardless of verdict — the human always sees the
article (PR #6 will surface the queue).

PR #3 will replace ``Article.last_verdict_json`` with a normalized
``editorial_reports`` table; this service's external API will not change.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Optional

# core/ is at the project root; tests + the Flask app set sys.path so this
# import resolves. Done at import time so callers get a clean ImportError if
# the layout drifts.
_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.crewai_system.contracts.blueprint import Blueprint, load_stub_blueprint  # noqa: E402
from core.crewai_system.contracts.editorial_verdict import EditorialVerdict  # noqa: E402
from core.crewai_system.crews.editor_crew.axes import LLMCaller  # noqa: E402
from core.crewai_system.crews.editor_crew.editor_crew import EditorCrew  # noqa: E402

from src.models.product import Article  # noqa: E402
from src.models.user import db  # noqa: E402

logger = logging.getLogger(__name__)


def run_editorial_review(
    article_id: int,
    blueprint: Optional[Blueprint] = None,
    llm: Optional[LLMCaller] = None,
) -> EditorialVerdict:
    """Review the stored Article and persist the verdict.

    On return:

    - ``Article.editorial_verdict`` is ``"PUBLISH"`` or ``"REJECT"``.
    - ``Article.last_verdict_json`` carries the full report JSON.
    - ``Article.blueprint_id`` is the Blueprint id used for the review.
    - ``Article.current_stage == "awaiting_human_review"`` regardless of
      verdict.
    """
    article = Article.query.get(article_id)
    if article is None:
        raise ValueError(f"Article {article_id} not found")

    if blueprint is None:
        niche_name = article.niche.name if article.niche else None
        blueprint = load_stub_blueprint(niche_name)

    article_dict = article.to_headless_contract()
    article_dict["id"] = article.id

    verdict = EditorCrew().review(article_dict, blueprint, llm=llm)

    article.editorial_verdict = verdict.verdict
    article.last_verdict_json = json.dumps(verdict.to_json())
    article.blueprint_id = blueprint.id
    article.current_stage = "awaiting_human_review"
    db.session.commit()

    logger.info(
        "EditorialVerdict for article %s: verdict=%s blocking=%s blueprint=%s",
        article_id,
        verdict.verdict,
        verdict.blocking_axes,
        blueprint.id,
    )
    return verdict


__all__ = ["run_editorial_review"]
