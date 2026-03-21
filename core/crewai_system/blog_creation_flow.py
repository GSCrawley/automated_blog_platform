from crewai.flow.flow import Flow, listen, start, router
from pydantic import BaseModel
from typing import Optional, Dict, Any
from core.crewai_system.crews.research_crew.research_crew import ResearchCrew
from core.crewai_system.crews.content_strategy_crew.content_strategy_crew import ContentStrategyCrew
from core.crewai_system.crews.content_creation_crew.content_creation_crew import ContentCreationCrew
from core.crewai_system.crews.editor_crew.editor_crew import EditorCrew
from core.crewai_system.knowledge_graph import TARGET_BLOG_KG
import json

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
    revision_count: int = 0
    max_revisions: int = 2
    pipeline_status: str = "pending"
      
    # Article being worked on
    current_topic: str = ""
    current_article_id: str = ""

class BlogCreationFlow(Flow[BlogCreationState]):
    """
    Master orchestration flow for the automated blog platform.
      
    Execution sequence:
    1. Research (Stage 0) — real-time intelligence gathering
    2. Strategy (Stage 1) — content planning from research
    3. Creation (Stage 2) — article writing
    4. Editorial QA (Stage 3) — check against Knowledge Graph
    5. Revise (if needed) — loop back to Stage 2 with editor feedback
    6. Approve — mark ready for publication
    """
      
    @start()
    def initialize_pipeline(self):
        """Set up the pipeline and inject current date context."""
        from datetime import datetime
        self.state.current_year = str(datetime.now().year)
        self.state.pipeline_status = "research_phase"
        print(f"[BlogCreationFlow] Starting pipeline for niche: {self.state.niche}")

    @listen(initialize_pipeline)
    def run_research_stage(self):
        """
        STAGE 0: Real-Time Intelligence Gathering
        Always runs first. Populates the Target Blog Knowledge Graph.
        """
        print("[BlogCreationFlow] Stage 0: Research")
          
        result = ResearchCrew().crew().kickoff(inputs={
            "niche": self.state.niche,
            "current_year": self.state.current_year,
            "blog_instance_id": self.state.blog_instance_id,
        })
          
        self.state.research_output = result.json_dict or {"raw": result.raw}
        self.state.pipeline_status = "strategy_phase"
          
        # Store key research facts in flow memory
        self.remember(
            f"Research completed for {self.state.niche}. "
            f"Key findings: {result.raw[:500]}",
            scope=f"/flow/{self.state.blog_instance_id}/research"
        )

    @listen(run_research_stage)
    def run_strategy_stage(self):
        """
        STAGE 1: Content Strategy
        Uses research results to plan what to create.
        """
        print("[BlogCreationFlow] Stage 1: Content Strategy")
          
        result = ContentStrategyCrew().crew().kickoff(inputs={
            "niche": self.state.niche,
            "current_year": self.state.current_year,
            "research_summary": str(self.state.research_output),
        })
          
        self.state.content_plan = result.json_dict or {"raw": result.raw}
        self.state.pipeline_status = "creation_phase"
          
        # Extract the first topic to write about
        if result.json_dict and "priority_topics" in result.json_dict:
            self.state.current_topic = result.json_dict["priority_topics"][0]["topic"]
        else:
            self.state.current_topic = f"Best {self.state.niche} Products {self.state.current_year}"

    @listen(run_strategy_stage)
    def run_creation_stage(self):
        """
        STAGE 2: Content Creation
        Writes the article using research intelligence.
        """
        print(f"[BlogCreationFlow] Stage 2: Writing '{self.state.current_topic}'")
          
        result = ContentCreationCrew().crew().kickoff(inputs={
            "niche": self.state.niche,
            "topic": self.state.current_topic,
            "content_plan_context": str(self.state.content_plan),
            "revision_feedback": self._get_revision_feedback(),
        })
          
        self.state.article_draft = result.raw
        self.state.pipeline_status = "editorial_phase"

    @listen(run_creation_stage)
    def run_editorial_stage(self):
        """
        STAGE 3: Editorial QA Gate
        Checks the article against the Target Blog Knowledge Graph.
        """
        print("[BlogCreationFlow] Stage 3: Editorial Review")
          
        result = EditorCrew().crew().kickoff(inputs={
            "article_draft": self.state.article_draft,
            "niche": self.state.niche,
            "current_topic": self.state.current_topic,
        })
          
        self.state.editorial_verdict = result.json_dict or {"raw": result.raw}
        return result.json_dict.get("verdict", "REVISION_REQUIRED") if result.json_dict else "REVISION_REQUIRED"

    @router(run_editorial_stage)
    def editorial_routing(self):
        """Route based on editorial verdict."""
        verdict = self.state.editorial_verdict
        if isinstance(verdict, dict):
            result = verdict.get("verdict", "REVISION_REQUIRED")
        else:
            result = "REVISION_REQUIRED"
          
        if result == "APPROVED":
            return "approved"
        elif result == "REJECTED" or self.state.revision_count >= self.state.max_revisions:
            return "rejected"
        else:
            return "needs_revision"

    @listen("approved")
    def finalize_article(self):
        """Article passed editorial review — mark ready for publication."""
        print(f"[BlogCreationFlow] APPROVED: '{self.state.current_topic}'")
        self.state.pipeline_status = "approved"
          
        # Save the approved article pattern to the KG
        self.remember(
            f"APPROVED article pattern for {self.state.niche}: {self.state.current_topic}. "
            f"Score: {self.state.editorial_verdict.get('composite_score', 'N/A')}",
            scope=f"/target_blog/content_standards"
        )
          
        return {
            "status": "approved",
            "article": self.state.article_draft,
            "verdict": self.state.editorial_verdict,
            "blog_instance_id": self.state.blog_instance_id,
        }

    @listen("needs_revision")
    def handle_revision_request(self):
        """Article needs revision — increment counter and re-run creation."""
        self.state.revision_count += 1
        print(f"[BlogCreationFlow] Revision {self.state.revision_count}/{self.state.max_revisions}")
        self.state.pipeline_status = f"revision_{self.state.revision_count}"
        # The flow will re-run run_creation_stage with revision feedback

    @listen("rejected")
    def handle_rejection(self):
        """Article rejected — escalate to human review."""
        print(f"[BlogCreationFlow] REJECTED: '{self.state.current_topic}'")
        self.state.pipeline_status = "rejected"
        return {
            "status": "rejected",
            "reason": self.state.editorial_verdict,
            "requires_human_review": True,
        }

    def _get_revision_feedback(self) -> str:
        """Extract revision instructions from the last editorial verdict."""
        if not self.state.editorial_verdict:
            return ""
        verdict = self.state.editorial_verdict
        if isinstance(verdict, dict) and "revision_checklist" in verdict:
            return "\n".join(f"- {item}" for item in verdict["revision_checklist"])
        return ""
