"""Audience Overseer — embodies the *24/7 Lead Generation* function.

Mandate: get every published article in front of people. This PR covers
search indexing; owned social distribution (Facebook Page) and newsletter
lead events arrive with the Meta AI integration in PR #22.
"""
from __future__ import annotations

from typing import List

from sqlalchemy import func

from src.models.analytics import ArticleAnalyticsDaily
from src.models.product import Article
from src.models.user import db
from src.overseers.base import ActionSpec, BaseOverseer, Finding

INDEXING_GRACE_DAYS = 7  # GOALS.md DoD: GSC impressions recorded after 7 days


class AudienceOverseer(BaseOverseer):
    name = "audience"
    function = "24/7 Lead Generation"
    mandate = (
        "Get every live article indexed and found in search; owned-channel "
        "distribution plugs in with PR #22 (Meta)."
    )

    def sense(self) -> List[Finding]:
        out: List[Finding] = []
        published = Article.query.filter(Article.status == "published").all()

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
        return out


__all__ = ["AudienceOverseer"]
