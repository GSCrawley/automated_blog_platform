"""Revenue Overseer — embodies the *Affiliate Funnel Management* function.

Mandate: make sure every live article can earn, that earnings are actually
observed (no blind feedback loop), and that traffic converts. Amplifying
winners with Meta campaign drafts arrives in PR #22.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import List

from sqlalchemy import func

from src.models.analytics import ArticleAnalyticsDaily, ArticlePerformance
from src.models.product import Article
from src.models.user import db
from src.overseers.base import ActionSpec, BaseOverseer, Finding

CLICKS_NO_SALE_MIN = 50
REVENUE_SIGNAL_GRACE_DAYS = 3
ROLLUP_STALE_HOURS = 36


def _has_affiliate_link(a: Article) -> bool:
    if (a.affiliate_links_count or 0) > 0:
        return True
    html = (a.content or "").lower()
    url = (a.product.affiliate_url or "").lower() if a.product else ""
    return bool(url and url in html) or "amazon." in html or "amzn.to" in html


class RevenueOverseer(BaseOverseer):
    name = "revenue"
    function = "Affiliate Funnel Management"
    mandate = (
        "Every live article monetized, every dollar observed, every click "
        "given a chance to convert."
    )

    def sense(self) -> List[Finding]:
        published = Article.query.filter(Article.status == "published").all()
        out: List[Finding] = []
        if not published:
            out.append(
                Finding(
                    code="no_live_articles",
                    title="No published articles: the blog has no revenue surface yet",
                    severity="critical",
                    detail="GOALS.md first-blog Definition of Done is not met.",
                    subject_type="system",
                    subject_id="blog",
                    actions=[ActionSpec("notify_human", {"queue": "/api/review"}, risk="auto")],
                )
            )
            return out

        for a in published:
            if not _has_affiliate_link(a):
                out.append(
                    Finding(
                        code="unmonetized_article",
                        title=f"Published article {a.id} contains no affiliate link",
                        severity="high",
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[ActionSpec("notify_human", {"article_id": a.id}, risk="auto")],
                    )
                )

        out += self._tracking_collisions(published)
        out += self._revenue_signal(published)
        out += self._funnel(published)
        return out

    def _tracking_collisions(self, published: List[Article]) -> List[Finding]:
        by_tag = defaultdict(list)
        for a in published:
            if a.product and a.product.tracking_id:
                by_tag[a.product.tracking_id].append(a.id)
        return [
            Finding(
                code="tracking_id_collision",
                title=f"{len(ids)} live articles share tracking ID '{tag}'",
                severity="high",
                category="engineering",
                detail=(
                    "run_daily_ingest maps tracking_id -> one article_id, so all "
                    "earnings for this tag land on a single article and ROI for the "
                    "others reads as zero. Create one Associates tracking ID per "
                    "article (or per cluster) and store it on the Product."
                ),
                evidence={"tracking_id": tag, "article_ids": ids},
                subject_type="tracking_id",
                subject_id=tag,
                actions=[ActionSpec("engineering_ticket", {"area": "attribution", "tracking_id": tag, "article_ids": ids})],
            )
            for tag, ids in by_tag.items()
            if len(ids) > 1
        ]

    def _revenue_signal(self, published: List[Article]) -> List[Finding]:
        oldest = min((a.created_at for a in published if a.created_at), default=None)
        if oldest is None or oldest > self.ago(days=REVENUE_SIGNAL_GRACE_DAYS):
            return []
        recent = (
            db.session.query(func.count(ArticleAnalyticsDaily.id))
            .filter(ArticleAnalyticsDaily.source == "affiliate")
            .filter(ArticleAnalyticsDaily.date >= self.ago(days=7).date())
            .scalar()
        )
        out: List[Finding] = []
        if not recent:
            out.append(
                Finding(
                    code="revenue_signal_missing",
                    title="No affiliate earnings data ingested in the last 7 days",
                    severity="high",
                    detail=(
                        "The feedback loop is optimizing blind. Import an Associates "
                        "Central CSV (POST /api/overseer/revenue/associates-csv) until "
                        "Creators API access is available."
                    ),
                    subject_type="system",
                    subject_id="affiliate_ingest",
                    actions=[ActionSpec("notify_human", {"endpoint": "/api/overseer/revenue/associates-csv"}, risk="auto")],
                )
            )
        last_roll = db.session.query(func.max(ArticlePerformance.refreshed_at)).scalar()
        has_rows = db.session.query(func.count(ArticleAnalyticsDaily.id)).scalar()
        if has_rows and (last_roll is None or last_roll < self.ago(hours=ROLLUP_STALE_HOURS)):
            out.append(
                Finding(
                    code="performance_rollup_stale",
                    title="28-day performance roll-up is stale",
                    severity="medium",
                    subject_type="system",
                    subject_id="article_performance",
                    actions=[ActionSpec("refresh_performance", {}, risk="auto")],
                )
            )
        return out

    def _funnel(self, published: List[Article]) -> List[Finding]:
        out: List[Finding] = []
        ids = [a.id for a in published]
        perfs = ArticlePerformance.query.filter(ArticlePerformance.article_id.in_(ids)).all()
        for p in perfs:
            rev = Decimal(p.total_revenue_28d or 0)
            if (p.total_clicks_28d or 0) >= CLICKS_NO_SALE_MIN and rev == 0:
                out.append(
                    Finding(
                        code="clicks_without_sales",
                        title=f"Article {p.article_id}: {p.total_clicks_28d} clicks, $0 earned (28d)",
                        severity="medium",
                        detail="Traffic is arriving but not converting: offer, CTA placement, or intent mismatch.",
                        evidence={"clicks_28d": p.total_clicks_28d},
                        subject_type="article",
                        subject_id=str(p.article_id),
                        actions=[ActionSpec("generate_improvement_proposals", {"article_id": p.article_id}, risk="auto")],
                    )
                )
        return out


__all__ = ["RevenueOverseer"]
