"""BlogCreationFlow (PR #2 rewrite).

Pipeline:
    Research → Strategy → Creation → Editorial → awaiting_human_review.

PR #2 changes vs. the prior version:

- The Editor returns a binary :class:`EditorialVerdict` (PUBLISH | REJECT),
  not a tri-state APPROVED/REVISION_REQUIRED/REJECTED.
- The flow no longer loops back to Creation on a REJECT — there is **no
  automated revision**. Every article ends at ``awaiting_human_review``.
- If ``current_article_id`` resolves to a real Article row, the verdict is
  persisted via :func:`run_editorial_review`. Otherwise the verdict lives
  only in flow state (test path).

The legacy CrewAI router-based flow is preserved at
``.pr2-backup/core/crewai_system/blog_creation_flow.py``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from core.crewai_system.crews.research_crew.research_crew import ResearchCrew
from core.crewai_system.crews.content_strategy_crew.content_strategy_crew import (
    ContentStrategyCrew,
)
from core.crewai_system.crews.content_creation_crew.content_creation_crew import (
    ContentCreationCrew,
)
from core.crewai_system.knowledge_graph import TARGET_BLOG_KG

log = logging.getLogger(__name__)


class BlogCreationState(BaseModel):
    """Typed state that persists across all stages of the blog creation pipeline."""

    # Inputs
    niche: str = ""
    blog_instance_id: str = ""
    current_year: str = ""

    # Stage outputs
    research_output: Optional[Dict[str, Any]] = None
    content_plan: Optional[Dict[str, Any]] = None
    article_draft: Optional[str] = None
    editorial_verdict: Optional[Dict[str, Any]] = None

    # Pipeline control
    pipeline_status: str = "pending"

    # Article being worked on
    current_topic: str = ""
    current_article_id: Optional[int] = None


class BlogCreationFlow(Flow[BlogCreationState]):
    """5-stage flow ending at the human review queue.

    Execution:
    1. Research          (Stage 0)  — real-time intelligence gathering
    2. Strategy          (Stage 1)  — content planning from research
    3. Creation          (Stage 2)  — article writing
    4. Editorial         (Stage 3)  — Conformance/Quality/Monetization/Compliance
    5. awaiting_human_review        — terminal state for every article
    """

    @start()
    def initialize_pipeline(self):
        from datetime import datetime

        self.state.current_year = str(datetime.now().year)
        self.state.pipeline_status = "research_phase"
        log.info("[BlogCreationFlow] Starting pipeline for niche: %s", self.state.niche)

    @listen(initialize_pipeline)
    def run_research_stage(self):
        log.info("[BlogCreationFlow] Stage 0: Research")
        result = ResearchCrew().crew().kickoff(
            inputs={
                "niche": self.state.niche,
                "current_year": self.state.current_year,
                "blog_instance_id": self.state.blog_instance_id,
            }
        )
        self.state.research_output = result.json_dict or {"raw": result.raw}
        self.state.pipeline_status = "strategy_phase"
        self.remember(
            f"Research completed for {self.state.niche}. "
            f"Key findings: {result.raw[:500]}",
            scope=f"/flow/{self.state.blog_instance_id}/research",
        )

    @listen(run_research_stage)
    def run_strategy_stage(self):
        log.info("[BlogCreationFlow] Stage 1: Content Strategy")
        result = ContentStrategyCrew().crew().kickoff(
            inputs={
                "niche": self.state.niche,
                "current_year": self.state.current_year,
                "research_summary": str(self.state.research_output),
            }
        )
        self.state.content_plan = result.json_dict or {"raw": result.raw}
        self.state.pipeline_status = "creation_phase"
        if result.json_dict and "priority_topics" in result.json_dict:
            self.state.current_topic = result.json_dict["priority_topics"][0]["topic"]
        else:
            self.state.current_topic = (
                f"Best {self.state.niche} Products {self.state.current_year}"
            )

    @listen(run_strategy_stage)
    def run_creation_stage(self):
        log.info("[BlogCreationFlow] Stage 2: Writing '%s'", self.state.current_topic)
        result = ContentCreationCrew().crew().kickoff(
            inputs={
                "niche": self.state.niche,
                "topic": self.state.current_topic,
                "content_plan_context": str(self.state.content_plan),
            }
        )
        self.state.article_draft = result.raw
        self.state.pipeline_status = "editorial_phase"

    @listen(run_creation_stage)
    def run_editorial_stage(self):
        """Stage 3: Editorial review.

        Always terminates the flow at ``awaiting_human_review`` regardless of
        verdict (PR #2). When ``current_article_id`` resolves to a stored
        Article row, the verdict is persisted via :func:`run_editorial_review`
        and the row's ``current_stage`` flips to ``awaiting_human_review``.
        """
        log.info("[BlogCreationFlow] Stage 3: Editorial Review")

        verdict_dict: Optional[Dict[str, Any]] = None
        if self.state.current_article_id:
            try:
                # Lazy import — keep core/ free of Flask deps at import time.
                from src.services.editorial_review import run_editorial_review

                verdict = run_editorial_review(int(self.state.current_article_id))
                verdict_dict = verdict.to_json()
            except Exception as e:
                log.exception(
                    "Editorial review failed for article %s: %s",
                    self.state.current_article_id,
                    e,
                )

        self.state.editorial_verdict = verdict_dict
        self.state.pipeline_status = "awaiting_human_review"
        if verdict_dict:
            log.info(
                "[BlogCreationFlow] Editorial verdict=%s blocking_axes=%s",
                verdict_dict.get("verdict"),
                verdict_dict.get("blocking_axes"),
            )

        # Save the article pattern to the KG with the verdict label.
        if verdict_dict:
            self.remember(
                f"{verdict_dict.get('verdict', 'UNKNOWN')} article pattern for "
                f"{self.state.niche}: {self.state.current_topic}. "
                f"Blocking axes: {verdict_dict.get('blocking_axes')}",
                scope="/target_blog/content_standards",
            )

        return {
            "status": "awaiting_human_review",
            "article_id": self.state.current_article_id,
            "verdict": verdict_dict,
            "blog_instance_id": self.state.blog_instance_id,
        }
