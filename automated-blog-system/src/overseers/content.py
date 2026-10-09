"""Content Overseer — embodies the *Programmatic Content Agency* function.

Mandate: keep a steady flow of publishable, fresh, blueprint-conformant
articles. Watches the human review queue, editorial rejection patterns by
axis, thin content, and freshness decay on live posts.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import List

from src.models.observability import EditorialReport
from src.models.product import Article
from src.overseers.base import ActionSpec, BaseOverseer, Finding

REVIEW_BACKLOG_MAX = 10
REVIEW_STALE_HOURS = 72
AXIS_REJECT_WINDOW = 20
AXIS_REJECT_MIN_N = 5
AXIS_REJECT_RATE = 0.5
FRESHNESS_DAYS = 180
THIN_WORDS = 800


class ContentOverseer(BaseOverseer):
    name = "content"
    function = "Programmatic Content Agency"
    mandate = (
        "Keep publishable, fresh, blueprint-conformant articles flowing through "
        "review without blanket rewrites."
    )

    def sense(self) -> List[Finding]:
        return self._review_queue() + self._axis_rejects() + self._live_quality()

    def _review_queue(self) -> List[Finding]:
        q = (
            Article.query.filter(Article.current_stage == "awaiting_human_review")
            .filter(Article.status != "archived")
            .order_by(Article.last_transition_at.asc())
            .all()
        )
        if not q:
            return []
        oldest = q[0].last_transition_at or q[0].created_at
        stale = oldest is not None and oldest < self.ago(hours=REVIEW_STALE_HOURS)
        if len(q) <= REVIEW_BACKLOG_MAX and not stale:
            return []
        return [
            Finding(
                code="review_backlog",
                title=f"{len(q)} article(s) waiting for human review",
                severity="medium" if len(q) <= 2 * REVIEW_BACKLOG_MAX else "high",
                detail="Publishing is gated on human review; the queue is the bottleneck.",
                evidence={
                    "count": len(q),
                    "oldest_since": oldest.isoformat() if oldest else None,
                    "publish_ready": [a.id for a in q if (a.editorial_verdict or "").upper() == "PUBLISH"][:20],
                },
                subject_type="system",
                subject_id="review_queue",
                actions=[ActionSpec("notify_human", {"queue": "/api/review"}, risk="auto")],
            )
        ]

    def _axis_rejects(self) -> List[Finding]:
        reports = EditorialReport.query.order_by(EditorialReport.created_at.desc()).limit(AXIS_REJECT_WINDOW).all()
        if len(reports) < AXIS_REJECT_MIN_N:
            return []
        counts: Counter = Counter()
        for r in reports:
            try:
                for axis in json.loads(r.blocking_axes or "[]"):
                    counts[axis] += 1
            except (TypeError, ValueError):
                continue
        out: List[Finding] = []
        for axis, n in counts.items():
            rate = n / len(reports)
            if rate >= AXIS_REJECT_RATE:
                out.append(
                    Finding(
                        code="axis_reject_rate",
                        title=f"'{axis}' axis blocks {rate:.0%} of recent articles",
                        severity="high",
                        category="engineering",
                        detail=(
                            "Systemic, not per-article: tune the crew responsible for this "
                            "axis (GOALS.md: rejection on one axis re-invokes only that crew)."
                        ),
                        evidence={"axis": axis, "blocked": n, "window": len(reports)},
                        subject_type="axis",
                        subject_id=axis,
                        actions=[ActionSpec("engineering_ticket", {"area": "crew_tuning", "axis": axis})],
                    )
                )
        return out

    def _live_quality(self) -> List[Finding]:
        out: List[Finding] = []
        for a in Article.query.filter(Article.status == "published").all():
            touched = a.ghost_updated_at or a.updated_at or a.created_at
            if touched and touched < self.ago(days=FRESHNESS_DAYS):
                out.append(
                    Finding(
                        code="stale_article",
                        title=f"Published article {a.id} not updated in {FRESHNESS_DAYS}+ days",
                        severity="medium",
                        detail="Prices, models and availability drift; buyer-intent pages decay fastest.",
                        evidence={"last_updated": touched.isoformat()},
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[ActionSpec("generate_improvement_proposals", {"article_id": a.id}, risk="auto")],
                    )
                )
            wc = a.word_count or len((a.content or "").split())
            if wc and wc < THIN_WORDS:
                out.append(
                    Finding(
                        code="thin_article",
                        title=f"Published article {a.id} is thin ({wc} words)",
                        severity="medium",
                        evidence={"word_count": wc},
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[ActionSpec("generate_improvement_proposals", {"article_id": a.id}, risk="auto")],
                    )
                )
        return out


__all__ = ["ContentOverseer"]
