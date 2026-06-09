"""Acceptance tests for PR #4 — Article (and Niche/Product) CRUD + dashboard stats.

Covered scenarios (PRs_2_through_7.md §4):

1. Create + list (no filter): list reflects newly created article.
2. List filters: ``?status``, ``?editorial_verdict``, ``?current_stage``,
   ``?niche_id`` each return the expected subset; ``include_archived`` flag
   honors PR #4 soft-delete.
3. Pagination: ``?limit`` + ``?offset`` slice + ``total`` reports the
   un-paginated count.
4. PUT and PATCH both accept partial bodies and persist. PATCH never touches
   fields it didn't carry.
5. DELETE is soft (sets ``status='archived'``); ``?hard=1`` actually drops
   the row.
6. ``GET /articles/<id>/stage-outputs`` returns the four PR #3 JSON columns.
7. ``GET /dashboard/stats`` returns ``by_stage`` / ``by_verdict`` /
   ``awaiting_review`` / ``cost`` panels.
8. PATCH on Niche and Product preserves untouched fields.
"""
from __future__ import annotations

import json
import os
import sys
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

from src.main import create_app  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402


@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _seed(*, count: int = 1, **overrides) -> list[Article]:
    """Create ``count`` articles sharing one niche + product. ``overrides``
    are applied to every article (e.g. ``status='archived'``)."""
    niche = Niche.query.filter_by(name="Cybersecurity SMB").first()
    if niche is None:
        niche = Niche(name="Cybersecurity SMB")
        db.session.add(niche)
        db.session.flush()
    product = Product.query.filter_by(name="Acme VPN Pro").first()
    if product is None:
        product = Product(name="Acme VPN Pro", niche_id=niche.id)
        db.session.add(product)
        db.session.flush()

    out = []
    for i in range(count):
        a = Article(
            title=f"Article {i}",
            content=f"<p>Body {i}</p>",
            meta_description=f"Desc {i}",
            keywords=json.dumps(["vpn", "smb"]),
            product_id=product.id,
            niche_id=niche.id,
            editorial_verdict=overrides.get("editorial_verdict", "PENDING"),
            status=overrides.get("status", "draft"),
            current_stage=overrides.get("current_stage", "stage_0"),
        )
        db.session.add(a)
        out.append(a)
    db.session.commit()
    return out


# ---------------------------------------------------------------------------
# 1. Create + list
# ---------------------------------------------------------------------------


def test_create_and_list(app, client):
    [a] = _seed(count=1)
    r = client.get("/api/blog/articles")
    assert r.status_code == 200
    body = r.get_json()
    assert body["success"] is True
    assert body["total"] == 1
    assert body["articles"][0]["id"] == a.id
    assert body["articles"][0]["title"] == "Article 0"


# ---------------------------------------------------------------------------
# 2. List filters + soft-delete visibility
# ---------------------------------------------------------------------------


def test_list_filters_by_status_and_verdict(app, client):
    _seed(count=2, status="draft", editorial_verdict="PENDING")
    _seed(count=1, status="published", editorial_verdict="PUBLISH")
    _seed(count=1, status="draft", editorial_verdict="REJECT")

    drafts = client.get("/api/blog/articles?status=draft").get_json()
    assert drafts["total"] == 3

    published = client.get("/api/blog/articles?status=published").get_json()
    assert published["total"] == 1
    assert published["articles"][0]["status"] == "published"

    rejected = client.get("/api/blog/articles?editorial_verdict=REJECT").get_json()
    assert rejected["total"] == 1
    assert rejected["articles"][0]["editorial_verdict"] == "REJECT"


def test_list_filters_by_current_stage(app, client):
    _seed(count=2, current_stage="stage_0")
    _seed(count=3, current_stage="awaiting_human_review")

    awaiting = client.get(
        "/api/blog/articles?current_stage=awaiting_human_review"
    ).get_json()
    assert awaiting["total"] == 3


def test_list_excludes_archived_by_default(app, client):
    _seed(count=2, status="draft")
    _seed(count=2, status="archived")

    default_view = client.get("/api/blog/articles").get_json()
    assert default_view["total"] == 2  # archived hidden

    with_archived = client.get("/api/blog/articles?include_archived=1").get_json()
    assert with_archived["total"] == 4


# ---------------------------------------------------------------------------
# 3. Pagination
# ---------------------------------------------------------------------------


def test_list_pagination(app, client):
    _seed(count=5)

    page1 = client.get("/api/blog/articles?limit=2&offset=0").get_json()
    assert page1["total"] == 5
    assert page1["limit"] == 2
    assert len(page1["articles"]) == 2

    page2 = client.get("/api/blog/articles?limit=2&offset=2").get_json()
    assert len(page2["articles"]) == 2

    # No overlap between pages.
    p1_ids = {a["id"] for a in page1["articles"]}
    p2_ids = {a["id"] for a in page2["articles"]}
    assert p1_ids.isdisjoint(p2_ids)


# ---------------------------------------------------------------------------
# 4. PUT and PATCH update
# ---------------------------------------------------------------------------


def test_put_updates_only_supplied_fields(app, client):
    [a] = _seed(count=1)
    r = client.put(
        f"/api/blog/articles/{a.id}",
        json={"title": "New title"},
    )
    assert r.status_code == 200
    refreshed = db.session.get(Article, a.id)
    assert refreshed.title == "New title"
    assert refreshed.content == "<p>Body 0</p>"  # untouched


def test_patch_updates_only_supplied_fields(app, client):
    [a] = _seed(count=1)
    r = client.patch(
        f"/api/blog/articles/{a.id}",
        json={"meta_description": "PR #4 patched"},
    )
    assert r.status_code == 200
    refreshed = db.session.get(Article, a.id)
    assert refreshed.meta_description == "PR #4 patched"
    assert refreshed.title == "Article 0"  # untouched
    assert refreshed.content == "<p>Body 0</p>"  # untouched


def test_patch_keywords_round_trips_as_json(app, client):
    [a] = _seed(count=1)
    r = client.patch(
        f"/api/blog/articles/{a.id}",
        json={"keywords": ["alpha", "beta", "gamma"]},
    )
    assert r.status_code == 200
    refreshed = db.session.get(Article, a.id)
    assert json.loads(refreshed.keywords) == ["alpha", "beta", "gamma"]


# ---------------------------------------------------------------------------
# 5. Soft-delete + hard-delete escape hatch
# ---------------------------------------------------------------------------


def test_delete_is_soft_by_default(app, client):
    [a] = _seed(count=1)
    r = client.delete(f"/api/blog/articles/{a.id}")
    assert r.status_code == 200
    body = r.get_json()
    assert body["archived"] is True
    assert body["deleted"] is False

    refreshed = db.session.get(Article, a.id)
    assert refreshed is not None  # row survives
    assert refreshed.status == "archived"


def test_delete_hard_drops_row(app, client):
    [a] = _seed(count=1)
    r = client.delete(f"/api/blog/articles/{a.id}?hard=1")
    assert r.status_code == 200
    body = r.get_json()
    assert body["deleted"] is True

    assert db.session.get(Article, a.id) is None


# ---------------------------------------------------------------------------
# 6. Stage outputs
# ---------------------------------------------------------------------------


def test_stage_outputs_endpoint(app, client):
    [a] = _seed(count=1)
    a.research_report_json = json.dumps({"trends": ["smb-vpn"]})
    a.strategy_json = json.dumps({"topics": ["best-vpn"]})
    a.draft_sections_json = json.dumps({"draft": "<h2>Intro</h2>..."})
    a.monetization_map_json = json.dumps({"ctas": [{"type": "affiliate"}]})
    a.last_verdict_json = json.dumps({"verdict": "PUBLISH"})
    db.session.commit()

    r = client.get(f"/api/blog/articles/{a.id}/stage-outputs")
    assert r.status_code == 200
    body = r.get_json()
    assert body["success"] is True
    so = body["stage_outputs"]
    assert so["research_report"] == {"trends": ["smb-vpn"]}
    assert so["strategy"] == {"topics": ["best-vpn"]}
    assert so["draft_sections"] == {"draft": "<h2>Intro</h2>..."}
    assert so["monetization_map"] == {"ctas": [{"type": "affiliate"}]}
    assert so["editorial_verdict"] == {"verdict": "PUBLISH"}


# ---------------------------------------------------------------------------
# 7. Dashboard stats — verdict / stage / cost panels
# ---------------------------------------------------------------------------


def test_dashboard_stats_breakdowns(app, client):
    _seed(count=2, current_stage="stage_0", editorial_verdict="PENDING")
    _seed(count=3, current_stage="awaiting_human_review", editorial_verdict="PUBLISH")
    _seed(count=1, current_stage="awaiting_human_review", editorial_verdict="REJECT")

    r = client.get("/api/blog/dashboard/stats")
    assert r.status_code == 200
    stats = r.get_json()["stats"]

    assert stats["by_stage"]["stage_0"] == 2
    assert stats["by_stage"]["awaiting_human_review"] == 4
    assert stats["by_verdict"]["PUBLISH"] == 3
    assert stats["by_verdict"]["REJECT"] == 1
    assert stats["awaiting_review"] == 4

    cost = stats["cost"]
    assert "month" in cost and len(cost["month"]) == 7  # YYYY-MM
    assert cost["cap_usd"] >= 0
    assert cost["spent_usd"] >= 0


# ---------------------------------------------------------------------------
# 8. Niche + Product PATCH
# ---------------------------------------------------------------------------


def test_niche_patch_preserves_untouched_fields(app, client):
    niche = Niche(name="Foo Niche", description="orig desc", competition_level="low")
    db.session.add(niche)
    db.session.commit()

    r = client.patch(
        f"/api/blog/niches/{niche.id}",
        json={"description": "new desc"},
    )
    assert r.status_code == 200
    refreshed = db.session.get(Niche, niche.id)
    assert refreshed.description == "new desc"
    assert refreshed.competition_level == "low"  # untouched


def test_product_patch_preserves_untouched_fields(app, client):
    niche = Niche(name="N1")
    db.session.add(niche)
    db.session.flush()
    product = Product(name="P1", category="cat-a", niche_id=niche.id)
    db.session.add(product)
    db.session.commit()

    r = client.patch(
        f"/api/blog/products/{product.id}",
        json={"category": "cat-b"},
    )
    assert r.status_code == 200
    refreshed = db.session.get(Product, product.id)
    assert refreshed.category == "cat-b"
    assert refreshed.name == "P1"
