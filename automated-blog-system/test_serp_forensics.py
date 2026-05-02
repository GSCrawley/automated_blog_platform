"""Acceptance tests for PR #5a — SERP Forensics + Pattern Library.

Five tests from ``PRs_2_through_7.md`` §5a.6:

1. Profile extraction is deterministic for a given HTML snapshot.
2. Aggregation produces expected confidence tiers for a crafted set of
   profiles with known distributions.
3. Gap identification finds planted gaps in a fixture set.
4. Blueprint persists and rehydrates correctly via Alembic-managed schema.
5. Stage 0.5 integration: the flow correctly loads a fresh Blueprint,
   triggers refresh when stale, and attaches ``blueprint_id`` to the
   Article row.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault(
    "GHOST_ADMIN_KEY",
    "0123456789abcdef01234567:" + "a" * 64,
)

from core.crewai_system.contracts.blueprint import Blueprint  # noqa: E402

from src.main import create_app  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.pattern_library import BlueprintRow, SerpProfile  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402
from src.services.blueprint_repo import (  # noqa: E402
    get_blueprint_for_niche,
    persist_blueprint,
    refresh_blueprint,
)
from src.services.serp_forensics import (  # noqa: E402
    ArticleProfile,
    SerpForensics,
    _profile_from_html,
    is_blueprint_stale,
)
from src.services.stage_persistence import (  # noqa: E402
    select_blueprint_for_article,
)

FIXTURE_HTML = (ROOT / "test_fixtures" / "serp_profile_sample.html").read_text()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _make_profile(
    *,
    url: str = "https://example.com/x",
    word_count: int = 2000,
    h2_count: int = 6,
    has_comparison_table: bool = True,
    has_faq: bool = True,
    h2_keywords: tuple = ("intro", "comparison", "pricing", "faq", "verdict"),
    h3_keywords: tuple = (),
    keyword_density: float = 0.012,
) -> ArticleProfile:
    return ArticleProfile(
        url=url,
        title="x",
        word_count=word_count,
        h1="x",
        h2_headings=list(h2_keywords)[:h2_count],
        h3_headings=list(h3_keywords),
        section_count=h2_count,
        first_h2_position=200,
        has_comparison_table=has_comparison_table,
        has_faq=has_faq,
        has_tldr=False,
        has_schema_markup=False,
        schema_types=[],
        internal_link_count=4,
        external_link_count=3,
        affiliate_link_count=2,
        affiliate_link_positions=[],
        image_count=2,
        first_image_position=300,
        meta_description="x",
        target_keyword="vpn",
        keyword_density=keyword_density,
        last_updated_at=None,
        reading_grade_level=8.0,
        intro_pattern_type=None,
        cta_positions=[],
        source_attribution_count=3,
    )


# ---------------------------------------------------------------------------
# Test 1 — Profile extraction is deterministic
# ---------------------------------------------------------------------------


def test_profile_extraction_is_deterministic():
    """Same HTML → same ArticleProfile across two runs (Firecrawl mocked
    by passing HTML directly)."""
    a = _profile_from_html(
        url="https://apex.example.com/best-vpn-smb",
        html=FIXTURE_HTML,
        query="vpn",
    )
    b = _profile_from_html(
        url="https://apex.example.com/best-vpn-smb",
        html=FIXTURE_HTML,
        query="vpn",
    )
    assert a == b

    # Sanity-check the extracted features.
    assert a.title.startswith("Best VPN for SMBs")
    assert a.h1 == "Best VPN for SMBs in 2026"
    # 6 h2 sections in the fixture
    assert a.section_count == 6
    # FAQ + comparison table both present
    assert a.has_faq is True
    assert a.has_comparison_table is True
    # JSON-LD schema detected
    assert a.has_schema_markup is True
    assert "Article" in a.schema_types
    # 2 affiliate links (sponsored rel) + several non-sponsored ones
    assert a.affiliate_link_count == 2
    # internal vs external split — at least one of each
    assert a.internal_link_count >= 1
    assert a.external_link_count >= 1
    # keyword density is non-zero (the fixture mentions "vpn" repeatedly)
    assert a.keyword_density > 0.0


# ---------------------------------------------------------------------------
# Test 2 — Aggregation produces expected confidence tiers
# ---------------------------------------------------------------------------


def test_aggregation_confidence_tiers():
    """Tight word_count distribution → "high"; spread → "medium" or "low"."""
    sf = SerpForensics(serper_api_key="not-used")

    # Tight distribution: word counts all within 5% of each other → high.
    tight = [
        _make_profile(word_count=2000),
        _make_profile(word_count=2050),
        _make_profile(word_count=1950),
        _make_profile(word_count=2010),
        _make_profile(word_count=1990),
    ]
    bp_tight, conf_tight, _agg = sf.aggregate(
        tight, niche_id=1, target_query_cluster=["best vpn smb"]
    )
    assert conf_tight["word_count"] == "high"
    # Comparison-table boolean: 100% true → high
    assert conf_tight["has_comparison_table"] == "high"

    # Spread distribution: word counts 1000–4000 → low/medium.
    spread = [
        _make_profile(word_count=1000),
        _make_profile(word_count=4000),
        _make_profile(word_count=1500),
        _make_profile(word_count=3500),
        _make_profile(word_count=2500),
    ]
    _bp, conf_spread, _agg = sf.aggregate(
        spread, niche_id=1, target_query_cluster=["best vpn smb"]
    )
    assert conf_spread["word_count"] in ("medium", "low")
    # Mixed booleans (50/50) → low
    mixed = [
        _make_profile(has_comparison_table=True),
        _make_profile(has_comparison_table=True),
        _make_profile(has_comparison_table=False),
        _make_profile(has_comparison_table=False),
    ]
    _bp, conf_mixed, _agg = sf.aggregate(
        mixed, niche_id=1, target_query_cluster=["best vpn smb"]
    )
    assert conf_mixed["has_comparison_table"] in ("medium", "low")


# ---------------------------------------------------------------------------
# Test 3 — Gap identification finds planted gaps
# ---------------------------------------------------------------------------


def test_gap_identification_finds_planted_gaps():
    """A query nobody covers in headings → flagged as a gap."""
    sf = SerpForensics(serper_api_key="not-used")

    # All profiles cover "comparison" and "pricing" but none cover "migration".
    profiles = [
        _make_profile(h2_keywords=("intro", "comparison", "pricing", "verdict"))
        for _ in range(6)
    ]

    gaps = sf.identify_gaps(
        profiles,
        query_cluster=[
            "comparison",
            "pricing",
            "migration from incumbent",  # planted gap
            "support tiers",  # also planted
        ],
    )
    assert "migration from incumbent" in gaps
    assert "support tiers" in gaps
    assert "comparison" not in gaps
    assert "pricing" not in gaps


# ---------------------------------------------------------------------------
# Test 4 — Blueprint persists and rehydrates correctly
# ---------------------------------------------------------------------------


def test_blueprint_persists_and_rehydrates(app):
    """A persisted BlueprintRow round-trips through ``to_blueprint`` losslessly."""
    bp = Blueprint(
        id="bp_smb_cybersec_test_v1",
        niche_id=42,
        target_query_cluster=["best vpn smb", "vpn for small business"],
        word_count_range=(1800, 2800),
        h2_count_range=(5, 9),
        required_sections=["intro", "comparison", "faq", "verdict"],
        target_keyword_density=(0.005, 0.02),
        min_internal_links=3,
        coverage_gaps=["migration from incumbent"],
        source_urls=[
            "https://apex.example.com/best-vpn-smb",
            "https://other.example.com/vpn-business",
        ],
        confidence_tier="medium",
        requires_feature_image=True,
        requires_schema_markup=False,
    )
    row = persist_blueprint(
        bp,
        profile_aggregate={"target_keyword_density": [0.005, 0.02], "word_count_median": 2200},
        confidence_tiers={"word_count": "high", "has_faq": "high"},
        generated_cost_usd=Decimal("0.18"),
    )
    assert row.id == bp.id
    assert row.version == 1
    assert row.parent_blueprint_id is None

    # Reload from DB and project to the contract.
    fresh = db.session.get(BlueprintRow, bp.id)
    rehydrated = fresh.to_blueprint()
    assert rehydrated.id == bp.id
    assert rehydrated.target_query_cluster == bp.target_query_cluster
    assert rehydrated.word_count_range == bp.word_count_range
    assert rehydrated.h2_count_range == bp.h2_count_range
    assert rehydrated.required_sections == bp.required_sections
    assert rehydrated.target_keyword_density == bp.target_keyword_density
    assert rehydrated.coverage_gaps == bp.coverage_gaps
    assert rehydrated.confidence_tier == "medium"

    # Versioning: next persist with parent should be v2.
    bp.id = "bp_smb_cybersec_test_v2"
    row2 = persist_blueprint(bp, parent=fresh)
    assert row2.version == 2
    assert row2.parent_blueprint_id == "bp_smb_cybersec_test_v1"


# ---------------------------------------------------------------------------
# Test 5 — Stage 0.5 integration
# ---------------------------------------------------------------------------


def _seed_article(*, niche_name: str = "Cybersecurity SMB") -> Article:
    niche = Niche.query.filter_by(name=niche_name).first()
    if niche is None:
        niche = Niche(name=niche_name)
        db.session.add(niche)
        db.session.flush()
    product = Product(name="Acme VPN Pro", niche_id=niche.id)
    db.session.add(product)
    db.session.flush()
    article = Article(
        title="Best VPN for SMBs in 2026",
        content="<p>Body</p>",
        meta_description="x",
        keywords=json.dumps(["vpn"]),
        product_id=product.id,
        niche_id=niche.id,
        editorial_verdict="PENDING",
    )
    db.session.add(article)
    db.session.commit()
    return article


def test_stage_0_5_attaches_blueprint_id_using_db_when_fresh(app):
    """Fresh BlueprintRow → Stage 0.5 picks it (no refresh, no network)."""
    article = _seed_article()
    bp = Blueprint(
        id="bp_smb_db_v1",
        niche_id=article.niche_id,
        target_query_cluster=["best vpn smb"],
    )
    persist_blueprint(bp)

    chosen = select_blueprint_for_article(
        article.id,
        target_query_cluster=["best vpn smb"],
        allow_refresh=False,
    )
    assert chosen == "bp_smb_db_v1"

    refreshed = db.session.get(Article, article.id)
    assert refreshed.blueprint_id == "bp_smb_db_v1"
    assert refreshed.current_stage == "stage_0_5_blueprint_selected"


def test_stage_0_5_falls_back_to_stub_when_no_db_row(app):
    """No BlueprintRow + refresh disabled → Stage 0.5 uses the PR #2 stub."""
    article = _seed_article()
    chosen = select_blueprint_for_article(
        article.id,
        target_query_cluster=["best vpn smb"],
        allow_refresh=False,
    )
    # Stub for "Cybersecurity SMB" niche is "bp_smb_cybersec_stub".
    assert chosen == "bp_smb_cybersec_stub"

    refreshed = db.session.get(Article, article.id)
    assert refreshed.blueprint_id == "bp_smb_cybersec_stub"
    assert refreshed.current_stage == "stage_0_5_blueprint_selected"


def test_stage_0_5_triggers_refresh_when_stale(app):
    """Stale row + ``allow_refresh=True`` + injected profiles → new Blueprint
    persisted; the article gets the new id."""
    article = _seed_article()

    stale_bp = Blueprint(
        id="bp_smb_stale_v1",
        niche_id=article.niche_id,
        target_query_cluster=["best vpn smb"],
    )
    stale_row = persist_blueprint(stale_bp)
    # Backdate so it counts as stale (>30 days old).
    stale_row.generated_at = datetime.utcnow() - timedelta(days=60)
    db.session.commit()
    assert is_blueprint_stale(stale_row.generated_at)

    # Inject pre-built profiles so refresh doesn't need network.
    profiles = [
        _make_profile(word_count=2000 + 50 * i, has_comparison_table=True, has_faq=True)
        for i in range(5)
    ]
    new_bp = refresh_blueprint(
        niche_id=article.niche_id,
        target_query_cluster=["best vpn smb"],
        parent=stale_row,
        profiles=profiles,
    )
    assert new_bp.id != stale_bp.id
    new_row = db.session.get(BlueprintRow, new_bp.id)
    assert new_row.parent_blueprint_id == stale_bp.id
    assert new_row.version == stale_row.version + 1

    # And get_blueprint_for_niche returns the fresh one.
    chosen = get_blueprint_for_niche(
        niche_id=article.niche_id,
        niche_name="Cybersecurity SMB",
        target_query_cluster=["best vpn smb"],
        allow_refresh=False,
    )
    assert chosen.id == new_bp.id
