"""Daily analytics ingest orchestrator (PR #7).

Orchestrates the two providers (GSC + affiliate) and the performance
roll-up. Called by the APScheduler job wired in ``main.py`` at 6 AM.

Key design decisions:

- **Upsert, never duplicate.** Both providers return dicts with the
  ``(article_id, date, source)`` triple key. The ingest function deletes
  the matching row (if any) and inserts the fresh one — SQLite-safe upsert.

- **Conformance-gap proposals can be generated on-demand** (per-article) or
  triggered as a fan-out when a Blueprint proposal is accepted. A single
  well-crafted baseline article is enough to flag non-conformant fields.
  (The daily ingest job currently only upserts analytics + refreshes performance.)
- **Statistical proposals** (effect-size based) require ``min_n`` articles
  per bucket. The default is ``3``; raise it per-niche once data grows.

- **No network calls in unit tests.** Providers are injected; tests pass
  pre-built row lists directly.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from src.models.analytics import ArticleAnalyticsDaily, ArticlePerformance
from src.models.product import Article
from src.models.user import db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Upsert helper
# ---------------------------------------------------------------------------


def _upsert_analytics_rows(rows: List[Dict]) -> int:
    """Insert-or-replace rows into ``article_analytics_daily``.

    Deletes any existing row with the same ``(article_id, date, source)``
    before inserting so re-running a day is idempotent.

    Returns the number of rows written.
    """
    written = 0
    for r in rows:
        existing = ArticleAnalyticsDaily.query.filter_by(
            article_id=r["article_id"],
            date=r["date"],
            source=r["source"],
        ).first()
        if existing:
            db.session.delete(existing)
            db.session.flush()

        row = ArticleAnalyticsDaily(
            article_id=r["article_id"],
            date=r["date"],
            source=r["source"],
            impressions=r.get("impressions", 0),
            clicks=r.get("clicks", 0),
            ctr=r.get("ctr", Decimal("0")),
            avg_position=r.get("avg_position"),
            conversions=r.get("conversions", 0),
            revenue_usd=r.get("revenue_usd", Decimal("0")),
        )
        db.session.add(row)
        written += 1

    db.session.commit()
    return written


# ---------------------------------------------------------------------------
# Performance roll-up
# ---------------------------------------------------------------------------


def refresh_performance(niche_id: Optional[int] = None) -> int:
    """Recompute the ``article_performance`` roll-up for published articles.

    Scans the trailing 28 days of ``article_analytics_daily``, aggregates
    per article, then assigns ``performance_tier`` relative to the niche.

    Parameters
    ----------
    niche_id:
        Restrict roll-up to one niche (useful for targeted refreshes after
        a single-niche ingest). Pass ``None`` to refresh all niches.

    Returns
    -------
    int
        Number of ``article_performance`` rows written / updated.
    """
    cutoff = date.today() - timedelta(days=28)

    q = Article.query.filter(Article.status == "published")
    if niche_id is not None:
        q = q.filter(Article.niche_id == niche_id)
    articles = q.all()

    if not articles:
        return 0

    niche_rois: Dict[Optional[int], List[Decimal]] = {}
    perf_data: List[Dict] = []

    for article in articles:
        rows = ArticleAnalyticsDaily.query.filter(
            ArticleAnalyticsDaily.article_id == article.id,
            ArticleAnalyticsDaily.date >= cutoff,
        ).all()

        total_impressions = sum(r.impressions or 0 for r in rows)
        total_clicks = sum(r.clicks or 0 for r in rows)
        total_revenue = sum(Decimal(str(r.revenue_usd or 0)) for r in rows)
        total_conversions = sum(r.conversions or 0 for r in rows)
        positions = [Decimal(str(r.avg_position)) for r in rows if r.avg_position]

        avg_ctr = (
            Decimal(str(total_clicks)) / Decimal(str(total_impressions))
            if total_impressions > 0
            else Decimal("0")
        )
        avg_pos = (
            sum(positions) / Decimal(str(len(positions))) if positions else None
        )
        epc = (
            total_revenue / Decimal(str(total_clicks))
            if total_clicks > 0
            else Decimal("0")
        )
        cost = Decimal(str(article.cost_usd or 0))
        roi = total_revenue / cost if (cost > Decimal("0") and rows) else None

        # Use existing ArticlePerformance data as fallback when no analytics
        # rows exist (e.g., newly seeded articles without daily data yet).
        existing_perf = ArticlePerformance.query.get(article.id)
        if roi is None and existing_perf is not None and existing_perf.roi is not None:
            roi = Decimal(str(existing_perf.roi))

        # Determine first_published_at, preferring any existing perf row's
        # recorded value so that refresh doesn't reset the age of an article.
        first_published_at = None
        if existing_perf and existing_perf.first_published_at:
            first_published_at = existing_perf.first_published_at
        elif article.published_url or article.status == "published":
            # Use created_at as proxy for first_published_at when no
            # dedicated column exists (PR #6 sets status='published').
            first_published_at = article.created_at

        days_live = 0
        if first_published_at:
            days_live = max(0, (datetime.utcnow() - first_published_at).days)

        niche_key = article.niche_id
        if roi is not None:
            niche_rois.setdefault(niche_key, []).append(roi)

        perf_data.append(
            {
                "article_id": article.id,
                "niche_id": niche_key,
                "first_published_at": first_published_at,
                "days_live": days_live,
                "total_impressions_28d": total_impressions,
                "total_clicks_28d": total_clicks,
                "avg_ctr_28d": avg_ctr,
                "avg_position_28d": avg_pos,
                "total_epc_28d": epc,
                "total_revenue_28d": total_revenue,
                "cost_usd": cost,
                "roi": roi,
                "performance_tier": "tbd",  # assigned below
            }
        )

    # Assign performance tiers within each niche.
    for d in perf_data:
        if d["days_live"] < 14:
            d["performance_tier"] = "tbd"
            continue
        if d["roi"] is None:
            d["performance_tier"] = "tbd"
            continue
        niche_key = d["niche_id"]
        rois = sorted(niche_rois.get(niche_key, []))
        n = len(rois)
        if n == 0:
            d["performance_tier"] = "tbd"
            continue
        percentile_20 = rois[max(0, int(n * 0.20) - 1)]
        percentile_80 = rois[min(n - 1, int(n * 0.80))]
        roi_val = d["roi"]
        if roi_val >= percentile_80:
            d["performance_tier"] = "winner"
        elif roi_val <= percentile_20:
            d["performance_tier"] = "loser"
        else:
            d["performance_tier"] = "mid"

    written = 0
    for d in perf_data:
        existing = ArticlePerformance.query.get(d["article_id"])
        if existing is None:
            existing = ArticlePerformance(article_id=d["article_id"])
            db.session.add(existing)

        existing.first_published_at = d["first_published_at"]
        existing.days_live = d["days_live"]
        existing.total_impressions_28d = d["total_impressions_28d"]
        existing.total_clicks_28d = d["total_clicks_28d"]
        existing.avg_ctr_28d = d["avg_ctr_28d"]
        existing.avg_position_28d = d["avg_position_28d"]
        existing.total_epc_28d = d["total_epc_28d"]
        existing.total_revenue_28d = d["total_revenue_28d"]
        existing.cost_usd = d["cost_usd"]
        existing.roi = d["roi"]
        existing.performance_tier = d["performance_tier"]
        existing.refreshed_at = datetime.utcnow()
        written += 1

    db.session.commit()
    return written


# ---------------------------------------------------------------------------
# Daily ingest orchestrator
# ---------------------------------------------------------------------------


def run_daily_ingest(
    *,
    gsc_provider=None,
    affiliate_providers=None,
    target_date: Optional[date] = None,
    article_url_map: Optional[Dict[str, int]] = None,
    tracking_id_map: Optional[Dict[str, int]] = None,
) -> Dict:
    """Pull both providers, upsert, then refresh performance.

    Parameters
    ----------
    gsc_provider:
        A :class:`~src.services.analytics.gsc_provider.GSCProvider` instance.
        If ``None`` and ``GSC_PROPERTY_URL`` is set, a real one is created.
        Pass an explicit ``None`` (with no env var) to skip GSC.
    affiliate_providers:
        List of :class:`~src.services.analytics.affiliate_provider.AffiliateProvider`
        instances. Auto-creates :class:`AmazonAssociatesProvider` if
        ``AMAZON_ASSOCIATES_ACCESS_KEY`` is set.
    target_date:
        The day to pull (defaults to today − 3 days, matching GSC's lag).
    article_url_map:
        ``{published_url: article_id}`` override. Computed from the DB if
        not provided (normal production path).
    tracking_id_map:
        ``{tracking_id: article_id}`` override. Computed from the DB if not
        provided.

    Returns
    -------
    dict
        ``{gsc_rows, affiliate_rows, performance_rows}`` counts.
    """
    from src.services.analytics.gsc_provider import GSCProvider
    from src.services.analytics.affiliate_provider import AmazonAssociatesProvider

    target = target_date or (date.today() - timedelta(days=3))

    # Build URL → article_id map from DB unless caller provides one.
    if article_url_map is None:
        published = Article.query.filter(
            Article.status == "published",
            Article.published_url.isnot(None),
        ).all()
        article_url_map = {a.published_url: a.id for a in published}

    # Build tracking_id → article_id map from DB unless caller provides one.
    if tracking_id_map is None:
        from src.models.product import Product
        tracking_id_map = {}
        for a in Article.query.filter(Article.status == "published").all():
            if a.product and a.product.tracking_id:
                tracking_id_map[a.product.tracking_id] = a.id

    # GSC pull
    gsc_rows_written = 0
    if gsc_provider is None and os.getenv("GSC_PROPERTY_URL"):
        gsc_provider = GSCProvider()
    if gsc_provider is not None:
        try:
            gsc_rows = gsc_provider.pull(article_url_map=article_url_map)
            gsc_rows_written = _upsert_analytics_rows(gsc_rows)
        except Exception:
            logger.exception("GSC ingest failed")

    # Affiliate pull
    affiliate_rows_written = 0
    if affiliate_providers is None:
        affiliate_providers = []
        if os.getenv("AMAZON_ASSOCIATES_ACCESS_KEY"):
            affiliate_providers.append(AmazonAssociatesProvider())

    for provider in affiliate_providers:
        try:
            rows = provider.pull_earnings(for_date=target, tracking_id_map=tracking_id_map)
            affiliate_rows_written += _upsert_analytics_rows(rows)
        except Exception:
            logger.exception("Affiliate ingest failed for %s", type(provider).__name__)

    # Performance roll-up
    perf_written = refresh_performance()

    logger.info(
        "Daily ingest complete: gsc=%d affiliate=%d perf=%d",
        gsc_rows_written,
        affiliate_rows_written,
        perf_written,
    )
    return {
        "gsc_rows": gsc_rows_written,
        "affiliate_rows": affiliate_rows_written,
        "performance_rows": perf_written,
    }


__all__ = ["run_daily_ingest", "refresh_performance", "_upsert_analytics_rows"]
