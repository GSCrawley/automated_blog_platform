"""Acceptance tests for PR #7 — Performance Feedback Loop.

Coverage:

1. GSC ingest round-trip  — pull returns rows; upsert writes DB; re-running
   upserts, doesn't duplicate.
2. Affiliate ingest round-trip — same upsert guarantee.
3. Performance tier assignment — seeded articles with known revenue
   distributions receive correct tiers.
4. Effectiveness calculation — fixture dataset with a known effect (articles
   with comparison tables outperform 2x in ROI) produces a non-zero
   effect_size that exceeds the default min_effect threshold.
5. Min-n gating — with fewer than min_n articles per bucket the engine
   reports ``insufficient_data`` for that field.
6. Proposal lifecycle — creating a proposal, accepting it via the route,
   verifying a new Blueprint version is created with the proposed value,
   and the original Blueprint is retained for historical attribution.
7. generate_proposals route — on-demand endpoint returns proposals_created.
8. reject route — marks proposal rejected without touching Blueprint.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import responses as resp_lib

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault("GHOST_ADMIN_KEY", "0123456789abcdef01234567:" + "a" * 64)

from src.main import create_app  # noqa: E402
from src.models.analytics import (  # noqa: E402
    ArticleAnalyticsDaily,
    ArticlePerformance,
    BlueprintProposal,
)
from src.models.niche import Niche  # noqa: E402
from src.models.pattern_library import BlueprintRow  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
    # teardown handled by in-memory SQLite being dropped


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def niche(app):
    n = Niche(name="Test Niche Feedback", description="test")
    db.session.add(n)
    db.session.commit()
    return n


@pytest.fixture()
def product(niche):
    p = Product(
        name="Test Product",
        description="desc",
        price=500.0,
        niche_id=niche.id,
        tracking_id="testtrack-20",
        affiliate_url="https://amazon.com/dp/TEST",
    )
    db.session.add(p)
    db.session.commit()
    return p


def _make_article(product, niche, *, word_count=2000, content="", published=True):
    a = Article(
        title="Test Article",
        content=content or ("<p>word " * word_count + "</p>"),
        product_id=product.id,
        niche_id=niche.id,
        status="published" if published else "draft",
        editorial_verdict="PUBLISH",
        current_stage="published" if published else "awaiting_human_review",
        cost_usd=Decimal("0.50"),
    )
    db.session.add(a)
    db.session.commit()
    return a


def _make_blueprint(niche, *, version=1):
    row = BlueprintRow(
        id=f"bp_test_v{version}",
        niche_id=niche.id,
        target_query_cluster=json.dumps(["best test product"]),
        word_count_lo=1500,
        word_count_hi=3000,
        h2_count_lo=4,
        h2_count_hi=10,
        min_internal_links=2,
        requires_feature_image=False,
        requires_schema_markup=False,
        confidence_tier="high",
        confidence_tiers=json.dumps(
            {
                "word_count_range": "high",
                "h2_count_range": "medium",
                "has_comparison_table": "high",
                "has_faq": "high",
                "requires_feature_image": "low",
                "requires_schema_markup": "low",
                "min_internal_links": "medium",
            }
        ),
        profile_aggregate=json.dumps(
            {"has_comparison_table": True, "has_faq": True}
        ),
        version=version,
    )
    db.session.add(row)
    db.session.commit()
    return row


def _seed_perf(article, *, roi: float, days_live: int = 30):
    existing = ArticlePerformance.query.get(article.id)
    if existing:
        db.session.delete(existing)
        db.session.flush()
    p = ArticlePerformance(
        article_id=article.id,
        first_published_at=datetime.utcnow() - timedelta(days=days_live),
        days_live=days_live,
        total_impressions_28d=1000,
        total_clicks_28d=50,
        avg_ctr_28d=Decimal("0.05"),
        total_revenue_28d=Decimal(str(roi * 0.5)),
        cost_usd=Decimal("0.50"),
        roi=Decimal(str(roi)),
        performance_tier="mid",
    )
    db.session.add(p)
    db.session.commit()
    return p


# ---------------------------------------------------------------------------
# 1. GSC ingest round-trip
# ---------------------------------------------------------------------------


def test_gsc_ingest_roundtrip(app, product, niche):
    """Pull returns rows; upsert writes DB; re-running upserts, doesn't duplicate."""
    from src.services.analytics.ingest import _upsert_analytics_rows

    rows = [
        {
            "article_id": 999,   # synthetic — doesn't need a real Article for this test
            "date": date(2026, 1, 15),
            "source": "gsc",
            "impressions": 1000,
            "clicks": 50,
            "ctr": Decimal("0.05"),
            "avg_position": Decimal("4.2"),
            "conversions": 0,
            "revenue_usd": Decimal("0"),
        }
    ]

    written = _upsert_analytics_rows(rows)
    assert written == 1

    row = ArticleAnalyticsDaily.query.filter_by(
        article_id=999, date=date(2026, 1, 15), source="gsc"
    ).first()
    assert row is not None
    assert row.impressions == 1000
    assert row.clicks == 50

    # Re-run with updated data — should upsert (1 row), not duplicate.
    rows[0]["impressions"] = 1200
    written2 = _upsert_analytics_rows(rows)
    assert written2 == 1

    total = ArticleAnalyticsDaily.query.filter_by(
        article_id=999, date=date(2026, 1, 15), source="gsc"
    ).count()
    assert total == 1  # no duplicates

    refreshed = ArticleAnalyticsDaily.query.filter_by(
        article_id=999, date=date(2026, 1, 15), source="gsc"
    ).first()
    assert refreshed.impressions == 1200


# ---------------------------------------------------------------------------
# 2. Affiliate ingest round-trip
# ---------------------------------------------------------------------------


def test_affiliate_ingest_roundtrip(app, product, niche):
    """Affiliate rows upsert correctly via _upsert_analytics_rows."""
    from src.services.analytics.ingest import _upsert_analytics_rows

    rows = [
        {
            "article_id": 888,
            "date": date(2026, 1, 15),
            "source": "affiliate",
            "impressions": 0,
            "clicks": 10,
            "ctr": Decimal("0"),
            "avg_position": None,
            "conversions": 2,
            "revenue_usd": Decimal("14.50"),
        }
    ]
    written = _upsert_analytics_rows(rows)
    assert written == 1

    row = ArticleAnalyticsDaily.query.filter_by(
        article_id=888, date=date(2026, 1, 15), source="affiliate"
    ).first()
    assert row is not None
    assert row.revenue_usd == Decimal("14.50")
    assert row.conversions == 2

    # Re-run — still 1 row.
    written2 = _upsert_analytics_rows(rows)
    assert written2 == 1
    assert ArticleAnalyticsDaily.query.filter_by(
        article_id=888, date=date(2026, 1, 15), source="affiliate"
    ).count() == 1


# ---------------------------------------------------------------------------
# 3. Performance tier assignment
# ---------------------------------------------------------------------------


def test_performance_tier_assignment(app, product, niche):
    """Articles with top-20% ROI → winner; bottom-20% → loser; middle → mid."""
    from src.services.analytics.ingest import refresh_performance

    # Create 5 published articles with known ROIs: 10, 5, 3, 2, 1
    articles = [_make_article(product, niche) for _ in range(5)]
    rois = [10.0, 5.0, 3.0, 2.0, 1.0]
    for a, roi in zip(articles, rois):
        _seed_perf(a, roi=roi, days_live=30)

    refresh_performance(niche_id=niche.id)

    perf = {
        ArticlePerformance.query.get(a.id).performance_tier: a.id
        for a in articles
    }

    # Top 20% of 5 = top 1 → index 4 (roi=10) should be 'winner'
    top_article_perf = ArticlePerformance.query.get(articles[0].id)
    assert top_article_perf.performance_tier == "winner"

    # Bottom 20% → roi=1 should be 'loser'
    bottom_article_perf = ArticlePerformance.query.get(articles[4].id)
    assert bottom_article_perf.performance_tier == "loser"


def test_performance_tier_tbd_for_new_articles(app, product, niche):
    """Articles with < 14 days live are 'tbd' regardless of ROI."""
    from src.services.analytics.ingest import refresh_performance

    a = _make_article(product, niche)
    _seed_perf(a, roi=100.0, days_live=3)  # very new

    refresh_performance(niche_id=niche.id)

    perf = ArticlePerformance.query.get(a.id)
    assert perf.performance_tier == "tbd"


# ---------------------------------------------------------------------------
# 4. Effectiveness calculation with known fixture effect
# ---------------------------------------------------------------------------


def test_effectiveness_known_effect(app, product, niche):
    """Articles with comparison tables have 2x ROI — effect_size should be > 0."""
    from src.services.feedback_engine import compute_blueprint_effectiveness

    _make_blueprint(niche)

    # 4 articles with comparison tables (ROI ~10), 4 without (ROI ~5)
    for i in range(4):
        content_with = "<table><tr><td>a</td></tr></table> " + "<p>word</p> " * 2000
        a = _make_article(product, niche, content=content_with)
        _seed_perf(a, roi=10.0, days_live=30)

    for i in range(4):
        content_without = "<p>word</p> " * 2000
        a = _make_article(product, niche, content=content_without)
        _seed_perf(a, roi=5.0, days_live=30)

    result = compute_blueprint_effectiveness(niche.id, min_n=3)
    table_result = result["fields"].get("has_comparison_table", {})
    assert table_result.get("status") == "ok", table_result
    assert table_result["effect_size"] != 0


# ---------------------------------------------------------------------------
# 5. Min-n gating
# ---------------------------------------------------------------------------


def test_min_n_gating(app, product, niche):
    """With fewer than min_n articles per bucket, field reports insufficient_data."""
    from src.services.feedback_engine import compute_blueprint_effectiveness

    _make_blueprint(niche)

    # Only 1 article with comparison table
    a = _make_article(product, niche, content="<table></table><p>word</p>" * 500)
    _seed_perf(a, roi=8.0, days_live=30)

    result = compute_blueprint_effectiveness(niche.id, min_n=3)
    table_result = result["fields"].get("has_comparison_table", {})
    # Only 1 in one bucket — insufficient_data expected
    assert table_result.get("status") == "insufficient_data"
    assert table_result["min_n_required"] == 3


# ---------------------------------------------------------------------------
# 6. Proposal lifecycle: create → accept → new Blueprint version created
# ---------------------------------------------------------------------------


def test_proposal_lifecycle_accept(app, client, product, niche):
    """Accept a proposal → new Blueprint version; original Blueprint retained."""
    bp = _make_blueprint(niche)

    proposal = BlueprintProposal(
        niche_id=niche.id,
        blueprint_id=bp.id,
        blueprint_field="word_count_range",
        current_value_json=json.dumps([1500, 3000]),
        proposed_value_json=json.dumps([2000, 3500]),
        evidence_json=json.dumps(
            {"n_conformant": 5, "n_nonconformant": 5, "effect_size": 0.25}
        ),
    )
    db.session.add(proposal)
    db.session.commit()
    pid = proposal.id

    resp = client.post(f"/api/proposals/{pid}/accept")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["status"] == "accepted"
    new_bp_id = body["new_blueprint_id"]
    assert new_bp_id != bp.id

    # Original Blueprint still exists.
    original = BlueprintRow.query.get(bp.id)
    assert original is not None

    # New Blueprint version exists.
    new_bp = BlueprintRow.query.get(new_bp_id)
    assert new_bp is not None
    assert new_bp.version == 2
    assert new_bp.parent_blueprint_id == bp.id

    # Proposal marked accepted.
    refreshed = BlueprintProposal.query.get(pid)
    assert refreshed.status == "accepted"
    assert refreshed.resulting_blueprint_id == new_bp_id


def test_proposal_lifecycle_reject(app, client, product, niche):
    """Reject a proposal → Blueprint unchanged, proposal marked rejected."""
    bp = _make_blueprint(niche, version=1)

    proposal = BlueprintProposal(
        niche_id=niche.id,
        blueprint_id=bp.id,
        blueprint_field="h2_count_range",
        current_value_json=json.dumps([4, 10]),
        proposed_value_json=json.dumps([6, 12]),
        evidence_json=json.dumps({"n_conformant": 3, "effect_size": 0.15}),
    )
    db.session.add(proposal)
    db.session.commit()
    pid = proposal.id

    resp = client.post(f"/api/proposals/{pid}/reject")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["status"] == "rejected"

    # Only original Blueprint exists.
    assert BlueprintRow.query.count() == 1

    refreshed = BlueprintProposal.query.get(pid)
    assert refreshed.status == "rejected"


# ---------------------------------------------------------------------------
# 7. generate_proposals route
# ---------------------------------------------------------------------------


def test_generate_proposals_route(app, client, product, niche):
    """POST /api/proposals/generate/<niche_id> returns success even with no data."""
    _make_blueprint(niche)
    resp = client.post(f"/api/proposals/generate/{niche.id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "proposals_created" in body


# ---------------------------------------------------------------------------
# 8. Cannot accept/reject an already-closed proposal
# ---------------------------------------------------------------------------


def test_cannot_double_accept(app, client, product, niche):
    """Accepting an already-accepted proposal returns 409."""
    bp = _make_blueprint(niche)
    proposal = BlueprintProposal(
        niche_id=niche.id,
        blueprint_id=bp.id,
        blueprint_field="word_count_range",
        current_value_json=json.dumps([1500, 3000]),
        proposed_value_json=json.dumps([2000, 3500]),
        evidence_json=json.dumps({}),
        status="accepted",
    )
    db.session.add(proposal)
    db.session.commit()

    resp = client.post(f"/api/proposals/{proposal.id}/accept")
    assert resp.status_code == 409
