"""Smoke tests for the Ghost publisher (PR #1).

Mocked unit tests run by default. To run the live test against a real
Ghost instance, set GHOST_LIVE_TEST=1 (and GHOST_API_URL / GHOST_ADMIN_KEY)
and run pytest with -k live.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import responses

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Mocked tests need a deterministic URL so `responses` can match. PR #6.4
# added .env auto-loading via conftest.py, which means GHOST_API_URL is now
# pre-populated from the real .env at import time — `setdefault` would be a
# no-op and the mock URL would not match the real one. Force the test URL
# unless we're running the live test (where the real env values are needed).
if os.environ.get("GHOST_LIVE_TEST") != "1":
    os.environ["GHOST_API_URL"] = "https://ghost.test.local"
    os.environ["GHOST_ADMIN_KEY"] = "0123456789abcdef01234567:" + "a" * 64

from src.main import create_app  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402
from src.services.ghost_service import GhostService  # noqa: E402


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


def _make_article(verdict="PUBLISH"):
    niche = Niche(name="Cybersecurity SMB")
    db.session.add(niche)
    db.session.flush()
    product = Product(name="Acme VPN Pro", niche_id=niche.id)
    db.session.add(product)
    db.session.flush()
    article = Article(
        title="Best VPN for SMBs in 2026",
        content="<p>Body copy here.</p>",
        meta_description="A quick guide for small business owners.",
        keywords=json.dumps(["vpn", "smb", "privacy"]),
        product_id=product.id,
        niche_id=niche.id,
        editorial_verdict=verdict,
    )
    db.session.add(article)
    db.session.commit()
    return article


def test_article_to_post_serialization():
    article = {
        "title": "Hello",
        "summary": "A short summary.",
        "sections": [{"heading": "Intro", "content": "Body."}],
        "keywords": ["alpha", "beta"],
        "calls_to_action": [
            {"type": "affiliate", "target": "https://x.test/", "anchor": "Buy"},
        ],
    }
    post = GhostService._article_to_post(article, status="published")
    assert post["title"] == "Hello"
    assert post["status"] == "published"
    assert "<h2>Intro</h2>" in post["html"]
    assert 'rel="sponsored nofollow noopener"' in post["html"]
    assert post["meta_description"].startswith("A short summary")
    assert {t["name"] for t in post["tags"]} == {"alpha", "beta"}


@responses.activate
def test_publish_route_persists_ghost_fields(app, client):
    article = _make_article(verdict="PUBLISH")
    responses.add(
        responses.POST,
        "https://ghost.test.local/ghost/api/admin/posts/",
        json={
            "posts": [
                {
                    "id": "abc123",
                    "url": "https://ghost.test.local/best-vpn/",
                    "status": "published",
                    "updated_at": "2026-04-22T12:00:00.000Z",
                }
            ]
        },
        status=201,
    )

    r = client.post(f"/api/publisher/publish/{article.id}")
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["success"] is True
    assert body["url"] == "https://ghost.test.local/best-vpn/"

    refreshed = db.session.get(Article, article.id)
    assert refreshed.ghost_post_id == "abc123"
    assert refreshed.published_url == "https://ghost.test.local/best-vpn/"
    assert refreshed.status == "published"


def test_publish_route_refuses_non_publish_verdict(app, client):
    article = _make_article(verdict="REVISE")
    r = client.post(f"/api/publisher/publish/{article.id}")
    assert r.status_code == 409
    body = r.get_json()
    assert body["success"] is False
    assert "PUBLISH" in body["error"]


@pytest.mark.skipif(
    os.environ.get("GHOST_LIVE_TEST") != "1",
    reason="Set GHOST_LIVE_TEST=1 (plus real GHOST_API_URL/KEY) to enable.",
)
def test_live_draft_against_real_ghost():
    """Creates a real DRAFT (not published) on the configured Ghost blog."""
    svc = GhostService()
    result = svc.save_draft(
        {
            "title": "[smoke-test] PR #1 publisher draft",
            "summary": "Created by automated_blog_platform smoke test.",
            "sections": [{"heading": "Test", "content": "Delete me."}],
            "keywords": ["smoke-test"],
        }
    )
    assert result.post_id
    assert result.status == "draft"
