"""EditorCrew (PR #2 rewrite).

The Editor's job is no longer "is this article good" — it is "does this
article conform to the empirically-winning blueprint for its target query?"
That's deterministic and measurable. Prose quality is a side-check.

This module is deliberately framework-free: no CrewAI agents, no Flask, no
SQLAlchemy. It composes four axis evaluators (see :mod:`axes`) into an
:class:`EditorialVerdict`. Persistence lives in the Flask-side service
``automated_blog_system.src.services.editorial_review``.

The verdict is **binary** — PUBLISH or REJECT. There is no automated revision
loop; PR #6 puts a human in the loop on every article.

The legacy CrewAI-driven EditorCrew lives at
``.pr2-backup/core/crewai_system/crews/editor_crew/editor_crew.py``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.crewai_system.contracts.blueprint import Blueprint, load_stub_blueprint
from core.crewai_system.contracts.editorial_verdict import (
    AxisReport,
    EditorialVerdict,
)
from core.crewai_system.crews.editor_crew.axes import (
    LLMCaller,
    compliance_axis,
    conformance_axis,
    content_quality_axis,
    monetization_axis,
)


class EditorCrew:
    """Pure-Python editor that emits an :class:`EditorialVerdict`."""

    def review(
        self,
        article: Dict[str, Any],
        blueprint: Blueprint,
        llm: Optional[LLMCaller] = None,
    ) -> EditorialVerdict:
        reports: List[AxisReport] = [
            conformance_axis(article, blueprint),
            content_quality_axis(article, blueprint, llm=llm),
            monetization_axis(article, blueprint),
            compliance_axis(article, blueprint, llm=llm),
        ]
        blocking = [r.axis for r in reports if not r.passed]
        verdict = "PUBLISH" if not blocking else "REJECT"
        return EditorialVerdict(
            verdict=verdict,
            axis_reports=reports,
            blocking_axes=blocking,
            article_id=article.get("id"),
            blueprint_id=blueprint.id,
        )


def review_article(
    article: Dict[str, Any],
    blueprint: Optional[Blueprint] = None,
    niche_name: Optional[str] = None,
    llm: Optional[LLMCaller] = None,
) -> EditorialVerdict:
    """Convenience entry point. Accepts an article dict (headless contract
    shape). If no Blueprint is provided, loads the stub for ``niche_name``."""
    if blueprint is None:
        blueprint = load_stub_blueprint(niche_name)
    return EditorCrew().review(article, blueprint, llm=llm)


__all__ = ["EditorCrew", "review_article"]
