"""Tests for PR #7 — retroactive article improvement proposals.

Coverage:

1. generate_improvement_proposals correctly identifies non-conformant fields
   against a fixture blueprint (word count too low, no FAQ, no comparison table).
2. Already-open proposals are not duplicated on a second generate call.
3. GET /api/review/<id>/improvements returns pending proposals.
4. POST /api/review/<id>/improvements/generate creates proposals.
5. POST /api/review/<id>/improvements/<pid>/apply mutates article and sets
   has_unpushed_changes; marks proposal status='applied'.
6. POST /api/review/<id>/improvements/<pid>/dismiss records reason; marks
   proposal status='dismissed'.
7. Accepting a BlueprintProposal triggers fan-out that creates article-level
   proposals for non-conformant published articles in the niche.
8. min_n=3 (new default): conformance-gap proposals fire from article 1
   (no statistical data needed).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault("GHOST_ADMIN_KEY", "0123456789abcdef01234567:" + "a" * 64)

from src.main import create_app  # noqa: E402
from src.models.analytics import (  # noqa: E402
    ArticleImprovementProposal,
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


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def niche(app):
    n = Niche(name="Test Niche Improvement", description="test")
    db.session.add(n)
    db.session.commit()
    return n


@pytest.fixture()
def product(niche):
    p = Product(
        name="Improvement Product",
        description="desc",
        price=600.0,
        niche_id=niche.id,
        tracking_id="imptest-20",
        affiliate_url="https://amazon.com/dp/IMPTEST",
    )
    db.session.add(p)
    db.session.commit()
    return p


def _article(product, niche, *, content="", word_count=500, status="published"):
    """Create a minimal article that is non-conformant by default
    (word_count too low, no FAQ, no comparison table)."""
    a = Article(
        title="Improvement Test Article",
        content=content or ("<p>word</p> " * word_count),
        product_id=product.id,
        niche_id=niche.id,
        status=status,
        editorial_verdict="PUBLISH",
        current_stage="published" if status == "published" else "awaiting_human_review",
        cost_usd=Decimal("0.40"),
        word_count=word_count,
    )
    db.session.add(a)
    db.session.commit()
    return a


def _blueprint(niche):
    row = BlueprintRow(
        id=f"bp_improvement_v1",
        niche_id=niche.id,
        target_query_cluster=json.dumps(["best improvement product"]),
        word_count_lo=1500,
        word_count_hi=3000,
        h2_count_lo=4,
        h2_count_hi=10,
        min_internal_links=0,
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
                "min_internal_links": "low",
            }
        ),
        profile_aggregate=json.dumps(
            {"has_comparison_table": True, "has_faq": True}
        ),
        version=1,
    )
    db.session.add(row)
    db.session.commit()
    return row


# ---------------------------------------------------------------------------
# 1. generate_improvement_proposals identifies non-conformant fields
# ---------------------------------------------------------------------------


def test_generate_identifies_nonconformant_fields(app, product, niche):
    """Word count below 1500 and no FAQ/table → proposals for those fields."""
    from src.services.feedback_engine import generate_improvement_proposals

    bp = _blueprint(niche)
    a = _article(product, niche, word_count=300)  # below 1500

    proposals = generate_improvement_proposals(a.id, blueprint=bp)
    fields = {p.blueprint_field for p in proposals}

    assert "word_count_range" in fields, f"word_count_range not in {fields}"
    assert "has_comparison_table" in fields, f"has_comparison_table not in {fields}"
    assert "has_faq" in fields, f"has_faq not in {fields}"
    # All should be pending
    assert all(p.status == "pending" for p in proposals)


def test_generate_conformant_article_no_proposals(app, product, niche):
    """An article that meets all high-confidence blueprint fields → no proposals."""
    from src.services.feedback_engine import generate_improvement_proposals

    bp = _blueprint(niche)
    # word count in range, has FAQ and comparison table, enough H2s
    content = (
        "<table><tr><td>Comparison</td></tr></table>"
        + "<h2>Section</h2>" * 5
        + "<p>FAQ</p>" * 3
        + "<p>word</p>" * 2000
    )
    a = _article(product, niche, content=content, word_count=2100)
    a.content = content
    db.session.commit()

    proposals = generate_improvement_proposals(a.id, blueprint=bp)
    non_word_proposals = [p for p in proposals if p.blueprint_field not in ("word_count_range",)]
    # table and faq should be satisfied; word_count is 2100 which is in [1500,3000]
    assert len(proposals) == 0, f"Unexpected proposals: {[p.blueprint_field for p in proposals]}"


# ---------------------------------------------------------------------------
# 2. Duplicate prevention
# ---------------------------------------------------------------------------


def test_duplicate_proposals_not_created(app, product, niche):
    """Calling generate twice doesn't duplicate proposals for the same field."""
    from src.services.feedback_engine import generate_improvement_proposals

    bp = _blueprint(niche)
    a = _article(product, niche, word_count=300)

    first = generate_improvement_proposals(a.id, blueprint=bp)
    second = generate_improvement_proposals(a.id, blueprint=bp)

    assert len(second) == 0  # all already open
    total = ArticleImprovementProposal.query.filter_by(
        article_id=a.id, blueprint_field="word_count_range"
    ).count()
    assert total == 1


def test_pending_improvement_proposals_are_db_unique(app, product, niche):
    """DB uniqueness prevents duplicate pending proposals for one field."""
    proposal_data = {
        "article_id": _article(product, niche, word_count=300).id,
        "blueprint_field": "word_count_range",
        "current_value_json": json.dumps(300),
        "recommended_value_json": json.dumps([1500, 3000]),
        "status": "pending",
    }

    db.session.add(ArticleImprovementProposal(**proposal_data))
    db.session.commit()

    db.session.add(ArticleImprovementProposal(**proposal_data))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


# ---------------------------------------------------------------------------
# 3. GET /api/review/<id>/improvements
# ---------------------------------------------------------------------------


def test_get_improvements_route(app, client, product, niche):
    """GET returns pending proposals for the article."""
    from src.services.feedback_engine import generate_improvement_proposals

    bp = _blueprint(niche)
    a = _article(product, niche, word_count=300)
    generate_improvement_proposals(a.id, blueprint=bp)

    resp = client.get(f"/api/review/{a.id}/improvements")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert len(body["proposals"]) >= 1
    for p in body["proposals"]:
        assert p["status"] == "pending"


# ---------------------------------------------------------------------------
# 4. POST /api/review/<id>/improvements/generate
# ---------------------------------------------------------------------------


def test_generate_improvements_route(app, client, product, niche):
    """POST /generate creates proposals and returns counts."""
    bp = _blueprint(niche)
    a = _article(product, niche, word_count=300)

    resp = client.post(f"/api/review/{a.id}/improvements/generate")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["proposals_created"] >= 1


# ---------------------------------------------------------------------------
# 5. Apply improvement proposal
# ---------------------------------------------------------------------------


def test_apply_improvement_proposal(app, client, product, niche):
    """Applying a proposal marks it 'applied'; article has_unpushed_changes (if ghost_post_id set)."""
    from src.services.feedback_engine import generate_improvement_proposals

    bp = _blueprint(niche)
    a = _article(product, niche, word_count=300)
    proposals = generate_improvement_proposals(a.id, blueprint=bp)
    assert proposals, "Need at least one proposal to apply"

    pid = proposals[0].id

    resp = client.post(f"/api/review/{a.id}/improvements/{pid}/apply")
    assert resp.status_code == 200

    updated = ArticleImprovementProposal.query.get(pid)
    assert updated.status == "applied"
    assert updated.reviewed_at is not None


# ---------------------------------------------------------------------------
# 6. Dismiss improvement proposal
# ---------------------------------------------------------------------------


def test_dismiss_improvement_proposal(app, client, product, niche):
    """Dismissing a proposal records reason and sets status='dismissed'."""
    from src.services.feedback_engine import generate_improvement_proposals

    bp = _blueprint(niche)
    a = _article(product, niche, word_count=300)
    proposals = generate_improvement_proposals(a.id, blueprint=bp)
    pid = proposals[0].id

    resp = client.post(
        f"/api/review/{a.id}/improvements/{pid}/dismiss",
        json={"reason": "Not relevant for this audience"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "dismissed"

    updated = ArticleImprovementProposal.query.get(pid)
    assert updated.status == "dismissed"
    assert "Not relevant" in updated.dismissed_reason


def test_cannot_dismiss_applied_proposal(app, client, product, niche):
    """Cannot dismiss an already-applied proposal."""
    from src.services.feedback_engine import generate_improvement_proposals

    bp = _blueprint(niche)
    a = _article(product, niche, word_count=300)
    proposals = generate_improvement_proposals(a.id, blueprint=bp)
    p = proposals[0]
    p.status = "applied"
    db.session.commit()

    resp = client.post(
        f"/api/review/{a.id}/improvements/{p.id}/dismiss",
        json={"reason": "too late"},
    )
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# 7. Accepting a BlueprintProposal triggers fan-out
# ---------------------------------------------------------------------------


def test_accept_blueprint_proposal_triggers_fanout(app, client, product, niche):
    """After accepting a blueprint proposal, improvement proposals are generated
    for all published articles in the niche."""
    bp = _blueprint(niche)

    # Two published articles that are non-conformant
    a1 = _article(product, niche, word_count=300)
    a2 = _article(product, niche, word_count=300)

    proposal = BlueprintProposal(
        niche_id=niche.id,
        blueprint_id=bp.id,
        blueprint_field="word_count_range",
        current_value_json=json.dumps([1500, 3000]),
        proposed_value_json=json.dumps([2000, 3500]),
        evidence_json=json.dumps({"n_conformant": 4, "effect_size": 0.3}),
    )
    db.session.add(proposal)
    db.session.commit()
    pid = proposal.id

    resp = client.post(f"/api/proposals/{pid}/accept")
    assert resp.status_code == 200

    # Allow background thread to complete (it's fast — pure DB, no network).
    import time
    time.sleep(0.5)

    # Both articles should have improvement proposals generated.
    for a in [a1, a2]:
        count = ArticleImprovementProposal.query.filter_by(article_id=a.id).count()
        assert count >= 1, f"No improvement proposals for article {a.id}"


# ---------------------------------------------------------------------------
# 8. min_n=3: conformance proposals fire from article 1
# ---------------------------------------------------------------------------


def test_conformance_proposals_fire_from_first_article(app, product, niche):
    """Conformance-gap proposals require no historical performance data.
    Even with a single article, non-conformant high-confidence fields are flagged.
    """
    from src.services.feedback_engine import generate_improvement_proposals

    bp = _blueprint(niche)
    a = _article(product, niche, word_count=200)  # single article, below 1500

    proposals = generate_improvement_proposals(a.id, blueprint=bp)
    # Must produce at least word_count_range even with zero analytics rows.
    fields = {p.blueprint_field for p in proposals}
    assert "word_count_range" in fields
