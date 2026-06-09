"""Acceptance tests for PR #2 — EditorialVerdict + Conformance axis.

The five tests in `PRs_2_through_7.md` §2.6:

1. Verdict schema round-trip.
2. Conformance axis is deterministic.
3. PUBLISH gate persists ``editorial_verdict == 'PUBLISH'``.
4. REJECT gate persists ``editorial_verdict == 'REJECT'`` and populated blocking_axes.
5. Terminal state — ``Article.current_stage == 'awaiting_human_review'`` regardless.

No network calls (LLM axes default to a pass-stub when no caller is injected).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Make sibling Flask app importable, plus project root for `core/` imports.
ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

# Set Ghost env so create_app() doesn't blow up if other imports touch it.
os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault(
    "GHOST_ADMIN_KEY",
    "0123456789abcdef01234567:" + "a" * 64,
)

from core.crewai_system.contracts.blueprint import Blueprint  # noqa: E402
from core.crewai_system.contracts.editorial_verdict import (  # noqa: E402
    AxisReport,
    EditorialVerdict,
)
from core.crewai_system.crews.editor_crew.axes import conformance_axis  # noqa: E402
from core.crewai_system.crews.editor_crew.editor_crew import EditorCrew  # noqa: E402

from src.main import create_app  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402
from src.services.editorial_review import run_editorial_review  # noqa: E402


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


def _stub_blueprint() -> Blueprint:
    """A loose Blueprint a competently-written test article can satisfy."""
    return Blueprint(
        id="bp_test_stub_v1",
        niche_id=None,
        target_query_cluster=["best vpn smb"],
        word_count_range=(40, 5000),
        h2_count_range=(2, 12),
        required_sections=["intro", "comparison", "faq", "verdict"],
        target_keyword_density=(0.0, 0.5),
        min_internal_links=0,
        coverage_gaps=["pricing per seat"],
        confidence_tier="medium",
    )


def _passing_article() -> dict:
    """Article shaped to satisfy every Conformance + Monetization check."""
    return {
        "id": None,
        "title": "Best VPN for SMBs in 2026",
        "content": "",
        "sections": [
            {
                "heading": "Intro",
                "content": (
                    "<p>Small businesses need a VPN to keep client work confidential. "
                    "<a href='https://aff.example/vpn-pro' rel='sponsored nofollow noopener'>Try Acme VPN</a> "
                    "is one option. Pricing per seat starts at $4/mo.</p>"
                ),
            },
            {
                "heading": "Comparison",
                "content": "<p>We compared four contenders across SMB use cases.</p>",
            },
            {
                "heading": "FAQ",
                "content": "<p>Q: Is a VPN enough? A: It's a starting point.</p>",
            },
            {
                "heading": "Verdict",
                "content": (
                    "<p>Acme VPN wins for SMBs.</p>"
                    "<p><em>Affiliate disclosure: we may earn a commission "
                    "from links in this post.</em></p>"
                ),
            },
        ],
        "summary": "A quick guide for small business owners.",
        "keywords": ["vpn", "smb"],
        "calls_to_action": [
            {
                "type": "affiliate",
                "target": "https://aff.example/vpn-pro",
                "anchor": "Try Acme VPN",
            }
        ],
        "meta": {
            "meta_title": "Best VPN for SMBs in 2026",
            "meta_description": "Quick guide for small business owners.",
            "feature_image": None,
        },
    }


def _make_db_article(verdict: str = "PENDING", *, drop_section: str | None = None) -> Article:
    """Persist a passing-shaped Article to the in-memory DB.

    If ``drop_section`` is set, that section is removed from the article body
    so Conformance fails on a missing required section.
    """
    niche = Niche.query.filter_by(name="Cybersecurity SMB").first()
    if niche is None:
        niche = Niche(name="Cybersecurity SMB")
        db.session.add(niche)
        db.session.flush()
    product = Product(name="Acme VPN Pro", niche_id=niche.id)
    db.session.add(product)
    db.session.flush()

    art = _passing_article()
    if drop_section:
        art["sections"] = [
            s for s in art["sections"] if drop_section.lower() not in (s.get("heading") or "").lower()
        ]

    sections_html = []
    for s in art["sections"]:
        if s.get("heading"):
            sections_html.append(f"<h2>{s['heading']}</h2>")
        if s.get("content"):
            sections_html.append(s["content"])
    rendered = "\n".join(sections_html)

    article = Article(
        title=art["title"],
        content=rendered,
        meta_description=art["meta"]["meta_description"],
        keywords=json.dumps(art["keywords"]),
        product_id=product.id,
        niche_id=niche.id,
        editorial_verdict=verdict,
    )
    db.session.add(article)
    db.session.commit()
    return article


# ---------------------------------------------------------------------------
# Tests — exactly the five required by PRs_2_through_7.md §2.6
# ---------------------------------------------------------------------------


def test_verdict_schema_round_trip():
    """1. EditorialVerdict.to_json() ↔ from_json() is lossless."""
    verdict = EditorialVerdict(
        verdict="REJECT",
        axis_reports=[
            AxisReport(
                axis="conformance",
                score=4.5,
                passed=False,
                checklist=[{"item": "word_count_in_range", "passed": False,
                             "expected": [1500, 3000], "actual": 200, "note": ""}],
                evidence={"word_count": 200},
            ),
            AxisReport(
                axis="content_quality",
                score=10.0,
                passed=True,
                checklist=[],
                evidence={"llm_skipped": True},
            ),
        ],
        blocking_axes=["conformance"],
        article_id=42,
        blueprint_id="bp_test_stub_v1",
    )
    raw = verdict.to_json()
    restored = EditorialVerdict.from_json(raw)
    assert restored.to_json() == raw
    assert restored.verdict == "REJECT"
    assert restored.blocking_axes == ["conformance"]
    assert len(restored.axis_reports) == 2
    assert restored.axis_reports[0].evidence == {"word_count": 200}


def test_conformance_axis_is_deterministic():
    """2. Conformance returns identical AxisReport on two successive runs.

    No LLM is involved in structural checks, so the dict equality assertion
    is the right signal.
    """
    article = _passing_article()
    blueprint = _stub_blueprint()
    r1 = conformance_axis(article, blueprint).to_json()
    r2 = conformance_axis(article, blueprint).to_json()
    assert r1 == r2


def test_publish_gate_persists(app):
    """3. An article that passes all axes gets editorial_verdict == 'PUBLISH'."""
    article = _make_db_article()
    verdict = run_editorial_review(article.id, blueprint=_stub_blueprint())

    refreshed = db.session.get(Article, article.id)
    assert verdict.verdict == "PUBLISH", verdict.to_json()
    assert refreshed.editorial_verdict == "PUBLISH"
    stored_report = json.loads(refreshed.last_verdict_json)
    assert stored_report["verdict"] == "PUBLISH"
    assert stored_report["blueprint_id"] == "bp_test_stub_v1"


def test_reject_gate_populates_blocking_axes(app):
    """4. Article missing a required section gets REJECT + populated blocking_axes."""
    article = _make_db_article(drop_section="comparison")
    verdict = run_editorial_review(article.id, blueprint=_stub_blueprint())

    refreshed = db.session.get(Article, article.id)
    assert verdict.verdict == "REJECT"
    assert "conformance" in verdict.blocking_axes
    assert refreshed.editorial_verdict == "REJECT"
    stored_report = json.loads(refreshed.last_verdict_json)
    assert "conformance" in stored_report["blocking_axes"]

    # The conformance checklist should explicitly flag the missing section.
    conformance_report = next(
        r for r in stored_report["axis_reports"] if r["axis"] == "conformance"
    )
    assert any(
        c["item"] == "section_present:comparison" and not c["passed"]
        for c in conformance_report["checklist"]
    ), conformance_report["checklist"]


def test_terminal_state_is_awaiting_human_review_for_either_verdict(app):
    """5. After EditorCrew, current_stage == 'awaiting_human_review' regardless."""
    pub = _make_db_article()
    rej = _make_db_article(drop_section="comparison")

    run_editorial_review(pub.id, blueprint=_stub_blueprint())
    run_editorial_review(rej.id, blueprint=_stub_blueprint())

    pub_row = db.session.get(Article, pub.id)
    rej_row = db.session.get(Article, rej.id)
    assert pub_row.current_stage == "awaiting_human_review"
    assert rej_row.current_stage == "awaiting_human_review"
    assert pub_row.editorial_verdict == "PUBLISH"
    assert rej_row.editorial_verdict == "REJECT"


# ---------------------------------------------------------------------------
# Sanity — EditorCrew direct call without DB
# ---------------------------------------------------------------------------

def test_editor_crew_direct_call_publish():
    verdict = EditorCrew().review(_passing_article(), _stub_blueprint())
    assert verdict.verdict == "PUBLISH", [
        (r.axis, r.passed, [c for c in r.checklist if not c["passed"]])
        for r in verdict.axis_reports
    ]
    assert verdict.blocking_axes == []
    assert verdict.blueprint_id == "bp_test_stub_v1"
