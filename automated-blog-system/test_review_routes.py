"""Acceptance tests for PR #6 — human-in-the-loop review + publish UI.

Seven tests from ``PRs_2_through_7.md`` §6.7:

1. Verdict gate on publish — non-PUBLISH returns 409.
2. PATCH round-trip — edits land, GET reflects them, headless contract
   carries the updated values.
3. Publish path — Ghost mocked; the body sent to Ghost reflects the
   PATCH'd content; Article gains ``ghost_post_id`` / ``published_url`` /
   ``last_ghost_sync_hash``.
4. Pull-from-Ghost — overwrites local title/html/meta; records a
   ``pre_pull_from_ghost`` revision row of the prior state.
5. Drift — Ghost returns divergent HTML → ``drift_detected: true`` with a
   non-empty ``diverging_fields`` list.
6. Push-to-Ghost — local edits push via update_article;
   ``last_ghost_sync_hash`` updates; a ``pre_push_to_ghost`` revision row
   captures the prior state.
7. No autonomous publish — grep guard: ``GhostService.publish_article`` /
   ``update_article`` and ``/api/publisher/publish/`` are only called from
   ``routes/review.py`` and ``routes/publisher.py``.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest
import responses

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
from src.models.observability import ArticleRevision  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402
from src.services.ghost_service import clear_post_cache  # noqa: E402


GHOST_URL = "https://ghost.test.local"
GHOST_POSTS_URL = f"{GHOST_URL}/ghost/api/admin/posts/"


@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        clear_post_cache()
        yield app
        db.session.remove()
        db.drop_all()
        clear_post_cache()


@pytest.fixture()
def client(app):
    return app.test_client()


def _make_article(*, verdict: str = "PUBLISH", with_ghost_post: bool = False) -> Article:
    niche = Niche.query.filter_by(name="Cybersecurity SMB").first()
    if niche is None:
        niche = Niche(name="Cybersecurity SMB")
        db.session.add(niche)
        db.session.flush()
    product = Product(name="Acme VPN Pro", niche_id=niche.id)
    db.session.add(product)
    db.session.flush()
    article = Article(
        title="Best VPN for SMBs in 2026",
        content="<h2>Intro</h2><p>Body.</p>",
        meta_description="A buyer guide.",
        keywords=json.dumps(["vpn", "smb"]),
        product_id=product.id,
        niche_id=niche.id,
        editorial_verdict=verdict,
        current_stage="awaiting_human_review",
        word_count=500,
    )
    if with_ghost_post:
        article.ghost_post_id = "ghost123"
        article.published_url = "https://ghost.test.local/best-vpn/"
        article.status = "published"
    db.session.add(article)
    db.session.commit()
    return article


def _ghost_post_response(
    *,
    post_id: str = "ghost123",
    title: str = "Best VPN for SMBs in 2026",
    html: str = "<p>Original Ghost body.</p>",
    meta_description: str = "Original meta.",
    tags: list | None = None,
    status: str = "published",
    updated_at: str = "2026-04-26T12:00:00.000Z",
):
    """Shape of a Ghost Admin API post response."""
    return {
        "posts": [
            {
                "id": post_id,
                "title": title,
                "html": html,
                "meta_description": meta_description,
                "tags": tags or [{"name": "vpn"}, {"name": "smb"}],
                "status": status,
                "updated_at": updated_at,
                "url": f"https://ghost.test.local/{post_id}/",
            }
        ]
    }


# ---------------------------------------------------------------------------
# 1. Verdict gate on publish
# ---------------------------------------------------------------------------


def test_publish_verdict_gate_returns_409(app, client):
    article = _make_article(verdict="REJECT")
    r = client.post(f"/api/review/{article.id}/publish")
    assert r.status_code == 409
    body = r.get_json()
    assert body["success"] is False
    assert "PUBLISH" in body["error"]


# ---------------------------------------------------------------------------
# 2. PATCH round-trip
# ---------------------------------------------------------------------------


def test_patch_round_trip_persists_and_reflects(app, client):
    article = _make_article()
    r = client.patch(
        f"/api/review/{article.id}",
        json={
            "title": "Updated VPN guide",
            "meta_description": "Updated meta.",
            "keywords": ["vpn", "smb", "2026"],
        },
    )
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["article"]["title"] == "Updated VPN guide"
    assert body["article"]["meta_description"] == "Updated meta."
    # Article.to_dict() already json.loads keywords for the API consumer.
    assert body["article"]["keywords"] == ["vpn", "smb", "2026"]

    # Subsequent GET reflects the PATCH.
    r2 = client.get(f"/api/review/{article.id}")
    assert r2.status_code == 200
    fresh = r2.get_json()
    assert fresh["article"]["title"] == "Updated VPN guide"
    # The headless contract carries the updated values too.
    assert fresh["headless_contract"]["title"] == "Updated VPN guide"
    assert fresh["headless_contract"]["meta"]["meta_description"] == "Updated meta."


def test_patch_validates_meta_description_length(app, client):
    article = _make_article()
    r = client.patch(
        f"/api/review/{article.id}",
        json={"meta_description": "x" * 200},
    )
    assert r.status_code == 400
    assert "max" in r.get_json()["error"]


def test_patch_validates_cta_target_url(app, client):
    article = _make_article()
    r = client.patch(
        f"/api/review/{article.id}",
        json={"calls_to_action": [{"type": "affiliate", "target": "not-a-url"}]},
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# 3. Publish path with mocked Ghost
# ---------------------------------------------------------------------------


@responses.activate
def test_publish_sends_patched_content_to_ghost(app, client):
    article = _make_article()

    captured_request_body: dict = {}

    def _post_callback(request):
        nonlocal captured_request_body
        captured_request_body = json.loads(request.body)
        return (
            201,
            {},
            json.dumps(_ghost_post_response(post_id="abc123")),
        )

    responses.add_callback(
        responses.POST,
        GHOST_POSTS_URL,
        callback=_post_callback,
    )

    # Patch the content first, then publish.
    r = client.patch(
        f"/api/review/{article.id}",
        json={"title": "PATCHED title", "meta_description": "PATCHED meta."},
    )
    assert r.status_code == 200, r.get_json()

    r = client.post(f"/api/review/{article.id}/publish")
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["success"] is True
    assert body["url"].startswith("https://ghost.test.local/")
    assert body["last_sync_hash"].startswith("sha256:")

    # Ghost received the patched content.
    sent = captured_request_body["posts"][0]
    assert sent["title"] == "PATCHED title"
    assert sent["meta_description"].startswith("PATCHED meta.")

    # Article row reflects the publish.
    refreshed = db.session.get(Article, article.id)
    assert refreshed.ghost_post_id == "abc123"
    assert refreshed.published_url == "https://ghost.test.local/abc123/"
    assert refreshed.status == "published"
    assert refreshed.last_ghost_sync_hash.startswith("sha256:")
    assert refreshed.has_unpushed_changes is False


# ---------------------------------------------------------------------------
# 4. Pull-from-Ghost
# ---------------------------------------------------------------------------


@responses.activate
def test_pull_from_ghost_overwrites_local_and_records_revision(app, client):
    article = _make_article(with_ghost_post=True)

    responses.add(
        responses.GET,
        f"{GHOST_POSTS_URL}ghost123/",
        json=_ghost_post_response(
            title="Ghost-side title",
            html="<p>Ghost-side body.</p>",
            meta_description="Ghost-side meta.",
        ),
    )

    r = client.post(f"/api/review/{article.id}/pull-from-ghost")
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["success"] is True
    assert body["revision_id"] is not None
    assert "title" in body["pulled_fields"]

    # Local row now matches Ghost.
    refreshed = db.session.get(Article, article.id)
    assert refreshed.title == "Ghost-side title"
    assert refreshed.content == "<p>Ghost-side body.</p>"
    assert refreshed.meta_description == "Ghost-side meta."
    assert refreshed.has_unpushed_changes is False

    # Revision captured the prior state.
    rev = db.session.get(ArticleRevision, body["revision_id"])
    assert rev.source == "pre_pull_from_ghost"
    snap = json.loads(rev.snapshot_json)
    assert snap["title"] == "Best VPN for SMBs in 2026"  # the pre-pull value


# ---------------------------------------------------------------------------
# 5. Drift detection
# ---------------------------------------------------------------------------


@responses.activate
def test_get_ghost_detects_drift_when_ghost_diverges(app, client):
    article = _make_article(with_ghost_post=True)

    responses.add(
        responses.GET,
        f"{GHOST_POSTS_URL}ghost123/",
        json=_ghost_post_response(
            title="DIVERGED title from Ghost",
            html="<p>Ghost edited this directly in Admin.</p>",
        ),
    )

    r = client.get(f"/api/review/{article.id}/ghost")
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["drift_detected"] is True
    assert "title" in body["diverging_fields"]
    assert "html" in body["diverging_fields"]
    assert body["local_hash"] != body["ghost_hash"]


# ---------------------------------------------------------------------------
# 6. Push-to-Ghost
# ---------------------------------------------------------------------------


@responses.activate
def test_push_to_ghost_sends_local_edits_and_records_revision(app, client):
    article = _make_article(with_ghost_post=True)

    # GhostService.update_article does a GET first (for updated_at), then PUT.
    responses.add(
        responses.GET,
        f"{GHOST_POSTS_URL}ghost123/",
        json=_ghost_post_response(updated_at="2026-04-26T11:00:00.000Z"),
    )
    captured: dict = {}

    def _put_callback(request):
        nonlocal captured
        captured = json.loads(request.body)
        return (
            200,
            {},
            json.dumps(
                _ghost_post_response(
                    post_id="ghost123",
                    title="Best VPN for SMBs in 2026",
                    html="<p>Local edits sent.</p>",
                    updated_at="2026-04-26T13:00:00.000Z",
                )
            ),
        )

    responses.add_callback(
        responses.PUT,
        f"{GHOST_POSTS_URL}ghost123/",
        callback=_put_callback,
    )

    # Patch first so there's a local edit to push.
    client.patch(
        f"/api/review/{article.id}",
        json={"title": "Pushed title"},
    )

    r = client.post(f"/api/review/{article.id}/push-to-ghost")
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["success"] is True
    assert body["revision_id"] is not None

    sent = captured["posts"][0]
    assert sent["title"] == "Pushed title"

    refreshed = db.session.get(Article, article.id)
    assert refreshed.last_ghost_sync_hash.startswith("sha256:")
    # The pre_push_to_ghost revision exists and captures the local state
    # right before the push (which includes the PATCHed title).
    rev = db.session.get(ArticleRevision, body["revision_id"])
    assert rev.source == "pre_push_to_ghost"


def test_push_to_ghost_refuses_without_ghost_post_id(app, client):
    article = _make_article()
    r = client.post(f"/api/review/{article.id}/push-to-ghost")
    assert r.status_code == 409


def test_push_to_ghost_refuses_non_publish_verdict(app, client):
    article = _make_article(verdict="REJECT", with_ghost_post=True)
    r = client.post(f"/api/review/{article.id}/push-to-ghost")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# 7. No-autonomous-publish grep guard
# ---------------------------------------------------------------------------


def test_no_autonomous_publish_call_sites_outside_routes_review_or_publisher():
    """Forbid new ``GhostService.publish_article`` / ``update_article`` /
    ``/api/publisher/publish/`` call sites outside ``routes/review.py``,
    ``routes/publisher.py``, the test files, and the Ghost service itself
    (where the methods are defined)."""
    repo_root = ROOT.parent
    # Match actual call sites — the trailing argument character disqualifies
    # bare docstring references like "GhostService.publish_article()".
    forbidden = re.compile(
        r"(GhostService\(\)\.publish_article\(\s*[A-Za-z_{[]|"
        r"GhostService\(\)\.update_article\(\s*[A-Za-z_{[]|"
        r"\.publish_article\(\s*[A-Za-z_{[]|"
        r"\.update_article\(\s*[A-Za-z_{[]|"
        r"/api/publisher/publish/)"
    )
    allowed_paths = {
        # Where the methods are defined.
        "automated-blog-system/src/services/ghost_service.py",
        # Where the routes live.
        "automated-blog-system/src/routes/review.py",
        "automated-blog-system/src/routes/publisher.py",
        # api.js wraps the publisher endpoint for the frontend.
        "blog-frontend/src/services/api.js",
    }

    violators = []
    for path in repo_root.rglob("*.py"):
        rel = path.relative_to(repo_root).as_posix()
        if rel.startswith(".pr") or rel.startswith(".kilo") or "/__pycache__/" in rel:
            continue
        if rel.startswith("test_") or rel.startswith("automated-blog-system/test_"):
            continue
        if rel in allowed_paths:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if forbidden.search(text):
            violators.append(rel)

    for path in repo_root.rglob("*.js"):
        rel = path.relative_to(repo_root).as_posix()
        if rel.startswith(".pr") or "node_modules" in rel:
            continue
        if rel in allowed_paths:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if forbidden.search(text):
            violators.append(rel)

    assert not violators, (
        "PR #6 forbids new autonomous-publish call sites. Found in:\n"
        + "\n".join(f"  - {v}" for v in violators)
    )
