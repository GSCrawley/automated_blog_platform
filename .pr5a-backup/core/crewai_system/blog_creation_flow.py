"""BlogCreationFlow (PR #3 rewrite).

Pipeline:
    Research → Strategy → Creation → Editorial → awaiting_human_review.

PR #3 changes vs. PR #2:

- Before kickoff, the monthly cap is checked via
  :meth:`CostMeter.assert_can_start_flow`. If exceeded, the flow refuses.
- After every stage, the stage output is persisted to its dedicated JSON
  column on the Article row via :func:`persist_stage_output`, and
  ``current_stage`` + ``stage_status`` + ``last_transition_at`` advance.
- After every stage, the per-article budget is checked via
  :func:`check_and_halt_if_over_budget`; if the article is over its cap
  it transitions to ``halted_budget`` and subsequent stages skip.

The terminal state is still ``awaiting_human_review`` (PR #2 invariant) —
PR #6 puts a human in the loop on every article, PUBLISH or REJECT.

Cost wiring (token-by-token attribution from CrewAI's LLM hooks) is left
as a TODO — :meth:`CostMeter.track` exposes the API the wrapper needs;
the test path exercises CostMeter directly via :func:`record`. PR #3
acceptance tests pass without the LLM wrap.

Legacy versions are at ``.pr2-backup/`` and ``.pr3-backup/``.
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
    halted: bool = False  # PR #3 — set True on budget halt; subsequent stages skip

    # Article being worked on
    current_topic: str = ""
    current_article_id: Optional[int] = None


def _persist_and_check(article_id: Optional[int], stage: str, output: Any) -> bool:
    """Persist stage output then check the per-article budget.

    Returns True if the article was halted by the budget check (caller
    should stop running stages for it).
    """
    if article_id is None:
        return False
    # Lazy import — keeps core/ free of Flask deps at import time.
    from src.services.stage_persistence import (  # noqa: WPS433
        check_and_halt_if_over_budget,
        persist_stage_output,
    )

    persist_stage_output(article_id, stage, output)
    return check_and_halt_if_over_budget(article_id)


class BlogCreationFlow(Flow[BlogCreationState]):
    """5-stage flow ending at the human review queue."""

    @start()
    def initialize_pipeline(self):
        from datetime import datetime

        self.state.current_year = str(datetime.now().year)
        self.state.pipeline_status = "research_phase"
        log.info("[BlogCreationFlow] Starting pipeline for niche: %s", self.state.niche)

        # PR #3 — refuse to start when the monthly cap is reached.
        try:
            from src.services.cost_meter import (  # noqa: WPS433
                BudgetExceeded,
                CostMeter,
            )

            CostMeter.assert_can_start_flow()
        except BudgetExceeded as e:
            self.state.halted = True
            self.state.pipeline_status = "halted_monthly_cap"
            log.warning("Pipeline refused to start: %s", e)
        except Exception:
            # Don't let observability bugs kill the pipeline.
            log.exception("Budget pre-check failed; continuing.")

    @listen(initialize_pipeline)
    def run_research_stage(self):
        if self.state.halted:
            return
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
        if _persist_and_check(
            self.state.current_article_id, "stage_0_research", self.state.research_output
        ):
            self.state.halted = True
            return
        self.remember(
            f"Research completed for {self.state.niche}. "
            f"Key findings: {result.raw[:500]}",
            scope=f"/flow/{self.state.blog_instance_id}/research",
        )

    @listen(run_research_stage)
    def run_strategy_stage(self):
        if self.state.halted:
            return
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
        if _persist_and_check(
            self.state.current_article_id, "stage_1_strategy", self.state.content_plan
        ):
            self.state.halted = True
            return
        if result.json_dict and "priority_topics" in result.json_dict:
            self.state.current_topic = result.json_dict["priority_topics"][0]["topic"]
        else:
            self.state.current_topic = (
                f"Best {self.state.niche} Products {self.state.current_year}"
            )

    @listen(run_strategy_stage)
    def run_creation_stage(self):
        if self.state.halted:
            return
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
        if _persist_and_check(
            self.state.current_article_id, "stage_2_creation", {"draft": result.raw}
        ):
            self.state.halted = True
            return

    @listen(run_creation_stage)
    def run_editorial_stage(self):
        """Stage 3: Editorial review. Terminal state is awaiting_human_review."""
        if self.state.halted:
            return
        log.info("[BlogCreationFlow] Stage 3: Editorial Review")

        verdict_dict: Optional[Dict[str, Any]] = None
        if self.state.current_article_id:
            try:
                from src.services.editorial_review import run_editorial_review  # noqa: WPS433

                verdict = run_editorial_review(int(self.state.current_article_id))
                verdict_dict = verdict.to_json()
            except Exception:
                log.exception(
                    "Editorial review failed for article %s",
                    self.state.current_article_id,
                )

        self.state.editorial_verdict = verdict_dict
        self.state.pipeline_status = "awaiting_human_review"
        if verdict_dict:
            log.info(
                "[BlogCreationFlow] Editorial verdict=%s blocking_axes=%s",
                verdict_dict.get("verdict"),
                verdict_dict.get("blocking_axes"),
            )
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
