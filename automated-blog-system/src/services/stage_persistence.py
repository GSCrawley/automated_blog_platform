"""Per-stage Article persistence (PR #3).

The Flow writes each stage's output to its dedicated JSON column on the
``articles`` row, and updates ``current_stage`` + ``stage_status`` +
``last_transition_at`` in the same transaction. PR #3's acceptance test #5
walks an article through all four stages and asserts every column is
populated.

This module is the seam between :class:`BlogCreationFlow` (CrewAI-flavored)
and the SQLAlchemy session — kept as plain Python so unit tests can drive
it without spinning up CrewAI.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from src.models.observability import EditorialReport
from src.models.product import Article
from src.models.user import db


# Stage label -> column on the Article row. Stage labels are the canonical
# strings written into ``Article.current_stage`` and into ``CostEvent.stage``.
STAGE_OUTPUT_COLUMNS: Dict[str, str] = {
    "stage_0_research": "research_report_json",
    "stage_1_strategy": "strategy_json",
    "stage_2_creation": "draft_sections_json",
    "stage_2_monetization_map": "monetization_map_json",
    "stage_3_editorial": "last_verdict_json",
}


def _to_json_text(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    return json.dumps(output, default=str)


def persist_stage_output(
    article_id: int,
    stage: str,
    output: Any,
    *,
    stage_status: str = "complete",
) -> Optional[Article]:
    """Write the stage's output JSON to its column and advance the article.

    ``stage`` must be one of the keys in :data:`STAGE_OUTPUT_COLUMNS`. If
    not, the function still updates ``current_stage`` + ``stage_status`` +
    ``last_transition_at`` (so callers can use it for control-flow stages
    like ``awaiting_human_review``) but writes no JSON column.
    """
    article = db.session.get(Article, article_id)
    if article is None:
        return None

    column = STAGE_OUTPUT_COLUMNS.get(stage)
    if column is not None:
        setattr(article, column, _to_json_text(output))

    article.current_stage = stage
    article.stage_status = stage_status
    article.last_transition_at = datetime.utcnow()
    db.session.commit()
    return article


def halt_article_for_budget(article_id: int) -> bool:
    """Flip an article into the ``halted_budget`` terminal state.

    Returns True if the article existed and was halted; False otherwise.
    """
    article = db.session.get(Article, article_id)
    if article is None:
        return False
    article.current_stage = "halted_budget"
    article.stage_status = "halted"
    article.last_transition_at = datetime.utcnow()
    db.session.commit()
    return True


def check_and_halt_if_over_budget(article_id: int) -> bool:
    """Halt the article if its running cost exceeded its per-article cap.

    Returns True if the article was halted. The caller should treat True
    as "stop running further stages on this article".
    """
    # Lazy import to avoid pulling CostMeter into modules that don't need it.
    from src.services.cost_meter import CostMeter

    if CostMeter.is_article_over_budget(article_id):
        return halt_article_for_budget(article_id)
    return False


def record_editorial_report(
    article_id: int,
    verdict: str,
    blocking_axes: list,
    report_json: str,
    blueprint_id: Optional[str] = None,
) -> EditorialReport:
    """Persist a normalized :class:`EditorialReport` row.

    PR #2 wrote the verdict JSON to ``Article.last_verdict_json``; PR #3
    additionally normalizes it here so PR #6's review queue and PR #7's
    feedback engine have a clean join target.
    """
    row = EditorialReport(
        article_id=article_id,
        verdict=verdict,
        blocking_axes=json.dumps(list(blocking_axes or [])),
        report_json=report_json,
        blueprint_id=blueprint_id,
    )
    db.session.add(row)
    db.session.commit()
    return row


__all__ = [
    "STAGE_OUTPUT_COLUMNS",
    "persist_stage_output",
    "halt_article_for_budget",
    "check_and_halt_if_over_budget",
    "record_editorial_report",
]
