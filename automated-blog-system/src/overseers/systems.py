"""Systems Overseer — embodies the *Custom Bot Development* function.

Mandate: keep the machine itself healthy. Detect crashed or stuck pipeline
runs, silent startup failures, missing configuration, unmetered spend,
broken integrations, and dead code. Code-level problems are never hot-
patched by the running app — they become ``engineering`` findings that a
coding agent (Grok Bot routine, Copilot, or a human) turns into a PR.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from flask import current_app

from src.models.observability import CostEvent
from src.models.product import Article
from src.models.user import db
from src.overseers.base import ActionSpec, BaseOverseer, Finding

TERMINAL_STAGES = {"awaiting_human_review", "published", "archived"}
STUCK_AFTER_HOURS = 6
RETRY_BUDGET = 2  # GOALS.md: per-article retry budget is 2 cycles
CREWAI_GENERATION_STAGE = "crewai_generation"

# Repo-root paths that are superseded by later PRs. Detected, never deleted
# by the app — deletion goes through an approved engineering ticket / PR.
REDUNDANT_CANDIDATES = {
    ".pr1-backup": "Pre-PR#1 snapshot; superseded by git history",
    ".pr2-backup": "Pre-PR#2 snapshot; superseded by git history",
    ".pr3-backup": "Pre-PR#3 snapshot; superseded by git history",
    ".pr4-backup": "Pre-PR#4 snapshot; superseded by git history",
    ".pr5a-backup": "Pre-PR#5a snapshot; superseded by git history",
    ".pr5b-backup": "Pre-PR#5b snapshot; superseded by git history",
    ".pr6-backup": "Pre-PR#6 snapshot; superseded by git history",
    "KGsTemp": "Scratch knowledge-graph files",
    "dump.rdb": "Committed Redis dump; *.rdb is already in .gitignore",
    ".DS_Store": "macOS metadata file",
    "apply_pr1.sh": "One-shot PR#1 patch script",
    "apply_pr1_docs.sh": "One-shot PR#1 docs script",
    "automated-blog-system/test_wordpress_integration.py": "Tests the removed WordPress path",
    "automated-blog-system/src/services/wordpress_service.py": "Deprecated stub that only raises",
    "memory-bank": "Describes the abandoned WordPress -> JAMstack plan; contradicts GOALS.md/README.md",
}

REQUIRED_CONFIG = {
    "GHOST_API_URL": ("high", "Publisher cannot reach Ghost"),
    "GHOST_ADMIN_KEY": ("high", "Publisher cannot authenticate to Ghost"),
    "TAVILY_API_KEY": ("medium", "Research crew loses real-time web search"),
    "SERPER_API_KEY": ("medium", "Research crew and SERP forensics lose Google SERP data"),
    "GSC_PROPERTY_URL": ("medium", "No organic-search signal for the feedback loop"),
    "GSC_CREDENTIALS_FILE": ("medium", "GSC provider cannot authenticate"),
}


def _repo_root() -> Path:
    # automated-blog-system/src/overseers/systems.py -> repo root
    return Path(__file__).resolve().parents[3]


class SystemsOverseer(BaseOverseer):
    name = "systems"
    function = "Custom Bot Development"
    mandate = (
        "Keep the pipeline, integrations, and codebase healthy: find faults, "
        "file fixes, retire redundancies."
    )

    def sense(self) -> List[Finding]:
        out: List[Finding] = []
        out += self._blueprint_registration()
        out += self._stuck_and_errored_articles()
        out += self._config()
        out += self._unmetered_spend()
        out += self._affiliate_integration()
        out += self._redundancies()
        return out

    # ------------------------------------------------------------------
    def _blueprint_registration(self) -> List[Finding]:
        errors = current_app.extensions.get("blueprint_errors", {}) if current_app else {}
        return [
            Finding(
                code="route_group_failed_to_load",
                title=f"API route group '{name}' failed to register at startup",
                severity="critical",
                category="engineering",
                detail=(
                    "create_app() swallows blueprint import errors, so the API "
                    "boots with this whole route group missing (every call 404s). "
                    "Usually a missing dependency."
                ),
                evidence={"error": err},
                subject_type="system",
                subject_id=f"blueprint:{name}",
                actions=[ActionSpec("engineering_ticket", {"area": "startup", "blueprint": name, "error": err})],
            )
            for name, err in errors.items()
        ]

    def _stuck_and_errored_articles(self) -> List[Finding]:
        out: List[Finding] = []
        cutoff = self.ago(hours=STUCK_AFTER_HOURS)
        candidates = Article.query.filter(Article.status != "archived").all()
        for a in candidates:
            stage = a.current_stage or "stage_0"
            if stage in TERMINAL_STAGES:
                continue
            ts = a.last_transition_at or a.updated_at or a.created_at
            if a.stage_status in ("pending", "running") and ts and ts < cutoff:
                out.append(
                    Finding(
                        code="stuck_article",
                        title=f"Article {a.id} stuck in {stage} for >{STUCK_AFTER_HOURS}h",
                        severity="high",
                        detail="No stage transition recorded; the flow likely died mid-run.",
                        evidence={"stage": stage, "stage_status": a.stage_status, "since": ts.isoformat()},
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[ActionSpec("mark_article_error", {"article_id": a.id}, risk="auto")],
                    )
                )
            elif a.stage_status in ("error", "halted_budget"):
                actions = [ActionSpec("retry_article", {"article_id": a.id, "budget": RETRY_BUDGET})]
                actions.append(ActionSpec("archive_article", {"article_id": a.id, "reason": "retry budget exhausted"}))
                out.append(
                    Finding(
                        code="article_failed",
                        title=f"Article {a.id} failed in {stage} ({a.stage_status})",
                        severity="high",
                        detail=(a.last_error or "")[:500],
                        evidence={"stage": stage, "stage_status": a.stage_status},
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=actions,
                    )
                )
        return out

    def _config(self) -> List[Finding]:
        out: List[Finding] = []
        for key, (sev, why) in REQUIRED_CONFIG.items():
            if not (os.getenv(key) or current_app.config.get(key)):
                out.append(
                    Finding(
                        code="missing_config",
                        title=f"{key} is not set",
                        severity=sev,
                        detail=why,
                        subject_type="config",
                        subject_id=key,
                        actions=[ActionSpec("notify_human", {"env": key}, risk="auto")],
                    )
                )
        from src.overseers.author_model_gate import current_author_provider

        provider = (os.getenv("CONTENT_LLM_PROVIDER") or "openai").lower()
        author = "meta" if provider == "meta" else current_author_provider()
        # The default model always backs the monetization and research agents;
        # Meta is needed only when the author agent (or the whole crew) runs on it.
        needed = {"OPENAI_API_KEY": f"CONTENT_LLM_PROVIDER={provider}"}
        if provider == "meta":
            needed = {"META_MODEL_API_KEY": "CONTENT_LLM_PROVIDER=meta"}
        elif author == "meta":
            needed["META_MODEL_API_KEY"] = "author agent switched to Muse Spark"
        for llm_key, why in needed.items():
            if not (os.getenv(llm_key) or current_app.config.get(llm_key)):
                out.append(
                    Finding(
                        code="missing_config",
                        title=f"{llm_key} is not set ({why})",
                        severity="critical",
                        detail="The content pipeline has no LLM to call.",
                        subject_type="config",
                        subject_id=llm_key,
                        actions=[ActionSpec("notify_human", {"env": llm_key}, risk="auto")],
                    )
                )
        return out

    def _unmetered_spend(self) -> List[Finding]:
        """Articles past Stage 2 with zero cost events = LLM spend is invisible.

        The BlogCreationFlow docstring notes token attribution from CrewAI's
        LLM hooks is still TODO. Until it lands, the $100/month cap in
        GOALS.md is enforced against an undercount.
        """
        drafted = (
            Article.query.filter(Article.draft_sections_json.isnot(None))
            .filter(Article.status != "archived")
            .all()
        )
        if not drafted:
            return []
        ids = [a.id for a in drafted]
        metered = {
            r[0]
            for r in db.session.query(CostEvent.article_id)
            .filter(CostEvent.article_id.in_(ids))
            .filter(CostEvent.stage == CREWAI_GENERATION_STAGE)
            .distinct()
            .all()
        }
        unmetered = [i for i in ids if i not in metered]
        if not unmetered:
            return []
        return [
            Finding(
                code="llm_spend_unmetered",
                title=f"{len(unmetered)} drafted article(s) have no recorded LLM cost",
                severity="high",
                category="engineering",
                detail=(
                    "CrewAI LLM calls are not wired into CostMeter.record with "
                    f"stage={CREWAI_GENERATION_STAGE!r}, so the monthly budget "
                    "circuit breaker is blind to real spend. Wire a CrewAI/LiteLLM "
                    "success callback that records this stage."
                ),
                evidence={"article_ids": unmetered[:50]},
                subject_type="system",
                subject_id="cost_meter",
                actions=[ActionSpec("engineering_ticket", {"area": "cost_meter", "article_ids": unmetered[:50]})],
            )
        ]

    def _affiliate_integration(self) -> List[Finding]:
        from src.services.analytics.affiliate_provider import AmazonAssociatesProvider

        endpoint = getattr(AmazonAssociatesProvider, "_REPORT_ENDPOINT_TEMPLATE", "")
        if "associates-report.amazon" not in endpoint:
            return []
        return [
            Finding(
                code="affiliate_ingest_endpoint_invalid",
                title="Amazon earnings ingest targets an endpoint Amazon does not document",
                severity="high",
                category="engineering",
                detail=(
                    "AmazonAssociatesProvider calls associates-report.amazon.<tld> with "
                    "basic auth. Amazon's programmatic access is the Creators API "
                    "(OAuth 2.0; requires 10 qualifying sales in 30 days). Until then, "
                    "import Associates Central CSV reports via "
                    "POST /api/overseer/revenue/associates-csv."
                ),
                evidence={"endpoint": endpoint},
                subject_type="system",
                subject_id="affiliate_provider",
                actions=[ActionSpec("engineering_ticket", {"area": "affiliate_ingest"})],
            )
        ]

    def _redundancies(self) -> List[Finding]:
        root = _repo_root()
        present = {p: why for p, why in REDUNDANT_CANDIDATES.items() if (root / p).exists()}
        if not present:
            return []
        return [
            Finding(
                code="redundant_paths",
                title=f"{len(present)} superseded file(s)/folder(s) still in the repo",
                severity="low",
                category="redundancy",
                detail="Safe to remove in a cleanup PR; git history preserves them.",
                evidence={"paths": present},
                subject_type="system",
                subject_id="repo",
                actions=[ActionSpec("engineering_ticket", {"area": "cleanup", "paths": sorted(present)})],
            )
        ]


__all__ = ["SystemsOverseer", "REDUNDANT_CANDIDATES", "RETRY_BUDGET"]
