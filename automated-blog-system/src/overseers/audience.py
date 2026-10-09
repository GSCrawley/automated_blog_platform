"""Audience Overseer — embodies the *24/7 Lead Generation* function.

Mandate: get every published article in front of people (search indexing,
owned social distribution) and turn readers into owned audience
(newsletter members), which is the KPI GOALS.md tracks.
"""
from __future__ import annotations

import os
from typing import List

from sqlalchemy import func

from src.models.analytics import ArticleAnalyticsDaily
from src.models.overseer import OverseerAction
from src.models.product import Article
from src.models.user import db
from src.overseers.base import ActionSpec, BaseOverseer, Finding

INDEXING_GRACE_DAYS = 7  # GOALS.md DoD: GSC impressions recorded after 7 days


def _already_distributed(article_id: int) -> bool:
    for a in OverseerAction.query.filter(OverseerAction.kind == "distribute_to_facebook_page").all():
        if a.params.get("article_id") == article_id and a.status in ("proposed", "approved", "applied", "verified"):
            return True
    return False


class AudienceOverseer(BaseOverseer):
    name = "audience"
    function = "24/7 Lead Generation"
    mandate = (
        "Get every live article indexed and distributed, and convert readers "
        "into newsletter members."
    )

    def sense(self) -> List[Finding]:
        out: List[Finding] = []
        published = Article.query.filter(Article.status == "published").all()
        page_ready = bool(os.getenv("META_PAGE_ID") and os.getenv("META_PAGE_ACCESS_TOKEN"))

        for a in published:
            gsc_rows = (
                db.session.query(func.coalesce(func.sum(ArticleAnalyticsDaily.impressions), 0))
                .filter(ArticleAnalyticsDaily.article_id == a.id)
                .filter(ArticleAnalyticsDaily.source == "gsc")
                .scalar()
            )
            if a.created_at and a.created_at < self.ago(days=INDEXING_GRACE_DAYS) and not gsc_rows:
                out.append(
                    Finding(
                        code="no_search_impressions",
                        title=f"Article {a.id} has zero Search Console impressions after {INDEXING_GRACE_DAYS}+ days",
                        severity="high",
                        detail="Either not indexed, GSC ingest is not configured, or the page is blocked.",
                        evidence={"published_url": a.published_url},
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[ActionSpec("notify_human", {"article_id": a.id, "check": "URL Inspection in GSC"}, risk="auto")],
                    )
                )
            if page_ready and a.published_url and not _already_distributed(a.id):
                out.append(
                    Finding(
                        code="not_distributed",
                        title=f"Article {a.id} has not been shared to the Facebook Page",
                        severity="low",
                        detail="GOALS.md: the distribution routine must fire at least once per post.",
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[
                            ActionSpec(
                                "distribute_to_facebook_page",
                                {"article_id": a.id, "link": a.published_url, "message": a.title},
                            )
                        ],
                    )
                )

        if published and not page_ready:
            out.append(
                Finding(
                    code="distribution_unconfigured",
                    title="No distribution channel configured",
                    severity="medium",
                    detail="Set META_PAGE_ID and META_PAGE_ACCESS_TOKEN to enable Facebook Page distribution.",
                    subject_type="config",
                    subject_id="META_PAGE_ID",
                    actions=[ActionSpec("notify_human", {"env": "META_PAGE_ID"}, risk="auto")],
                )
            )
        return out


__all__ = ["AudienceOverseer"]
