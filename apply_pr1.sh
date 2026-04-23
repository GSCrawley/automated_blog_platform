#!/usr/bin/env bash
# apply_pr1.sh — Apply PR #1 (Ghost Headless CMS Publisher) to automated_blog_platform.
# Idempotent: re-running will not double-patch files or overwrite backups.
#
# Usage:
#   chmod +x apply_pr1.sh
#   ./apply_pr1.sh
#
# Run from the repo root (the directory that contains automated-blog-system/, core/, blog-frontend/).

set -euo pipefail

# ---------- sanity ---------------------------------------------------------
if [[ ! -d "automated-blog-system/src" || ! -d "core/crewai_system" ]]; then
  echo "❌ This doesn't look like the automated_blog_platform repo root."
  echo "   Expected to find ./automated-blog-system/src and ./core/crewai_system."
  exit 1
fi

BACKUP_DIR=".pr1-backup"
mkdir -p "$BACKUP_DIR"

backup() {
  local src="$1"
  if [[ -f "$src" ]]; then
    local dest="$BACKUP_DIR/$src"
    mkdir -p "$(dirname "$dest")"
    if [[ ! -f "$dest" ]]; then
      cp "$src" "$dest"
      echo "  📦 backed up $src -> $dest"
    fi
  fi
}

write_file() {
  # write_file <path>  <<'EOF' ... EOF
  local path="$1"
  mkdir -p "$(dirname "$path")"
  cat > "$path"
  echo "  ✍️  wrote $path"
}

echo "=== PR #1: Ghost Headless CMS Publisher ==="
echo

# ---------- 1. ghost_service.py -------------------------------------------
echo "[1/9] Writing src/services/ghost_service.py"
write_file "automated-blog-system/src/services/ghost_service.py" <<'PYEOF'
"""Ghost Headless CMS publisher service.

Publishes Article records to a Ghost blog via the Admin API v5.
Auth: short-lived JWT signed from the Admin API key pair (id:secret hex).

Required env vars (read lazily so import never fails):
    GHOST_API_URL    e.g. https://apex.yourghostblog.com
    GHOST_ADMIN_KEY  e.g. 6827abc...:deadbeef...   (id:secret, hex)

Returns the live post URL on success so pipeline tasks of the form
'publish and return live URL' resolve deterministically.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Iterable, Optional

import jwt  # PyJWT
import requests

log = logging.getLogger(__name__)


class GhostPublishError(RuntimeError):
    """Raised when a Ghost API call fails."""


@dataclass(frozen=True)
class PublishResult:
    post_id: str
    url: str
    status: str          # "published" | "draft" | "scheduled"
    updated_at: str


class GhostService:
    """Thin synchronous Ghost Admin API client focused on Article publishing."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        admin_key: Optional[str] = None,
        timeout: int = 20,
    ) -> None:
        api_url = api_url or os.environ.get("GHOST_API_URL")
        admin_key = admin_key or os.environ.get("GHOST_ADMIN_KEY")
        if not api_url or not admin_key:
            raise GhostPublishError(
                "GHOST_API_URL and GHOST_ADMIN_KEY must be set "
                "(or passed explicitly to GhostService)."
            )
        if ":" not in admin_key:
            raise GhostPublishError("GHOST_ADMIN_KEY must be in 'id:secret' form.")
        self.api_url = api_url.rstrip("/")
        self.admin_key = admin_key
        self.timeout = timeout

    # ---- auth ---------------------------------------------------------------
    def _token(self) -> str:
        key_id, secret = self.admin_key.split(":", 1)
        iat = int(time.time())
        payload = {"iat": iat, "exp": iat + 5 * 60, "aud": "/admin/"}
        return jwt.encode(
            payload,
            bytes.fromhex(secret),
            algorithm="HS256",
            headers={"kid": key_id},
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Ghost {self._token()}",
            "Content-Type": "application/json",
            "Accept-Version": "v5.0",
        }

    # ---- public API ---------------------------------------------------------
    def publish_article(self, article: dict) -> PublishResult:
        """Create a new published post from a headless-contract Article dict."""
        return self._create(article, status="published")

    def save_draft(self, article: dict) -> PublishResult:
        return self._create(article, status="draft")

    def update_article(self, post_id: str, article: dict) -> PublishResult:
        # Ghost requires the current updated_at for optimistic concurrency.
        current = self._get(f"/ghost/api/admin/posts/{post_id}/")
        updated_at = current["posts"][0]["updated_at"]
        post = self._article_to_post(article, status="published")
        post["updated_at"] = updated_at
        return self._send(
            "PUT",
            f"/ghost/api/admin/posts/{post_id}/",
            {"posts": [post]},
        )

    # ---- internals ----------------------------------------------------------
    def _create(self, article: dict, status: str) -> PublishResult:
        body = {"posts": [self._article_to_post(article, status=status)]}
        return self._send("POST", "/ghost/api/admin/posts/", body)

    @staticmethod
    def _article_to_post(article: dict, status: str) -> dict:
        if "title" not in article:
            raise GhostPublishError("Article is missing required 'title'.")
        html = GhostService._sections_to_html(
            article.get("sections", []),
            summary=article.get("summary"),
            ctas=article.get("calls_to_action", []),
            fallback_content=article.get("content"),
        )
        meta = article.get("meta", {}) or {}
        summary = (article.get("summary") or "").strip()
        post: dict = {
            "title": article["title"],
            "html": html,
            "status": status,
            "tags": [{"name": k} for k in (article.get("keywords") or [])[:10]],
            "meta_title": meta.get("meta_title") or article["title"],
        }
        if summary:
            post["custom_excerpt"] = summary[:300]
            post["meta_description"] = summary[:156]
        if feature_image := meta.get("feature_image"):
            post["feature_image"] = feature_image
        if slug := article.get("slug"):
            post["slug"] = slug
        return post

    @staticmethod
    def _sections_to_html(
        sections: Iterable,
        summary: Optional[str],
        ctas: Iterable,
        fallback_content: Optional[str] = None,
    ) -> str:
        sections = list(sections or [])
        if not sections and fallback_content:
            body = fallback_content.strip()
            return body if body.startswith("<") else f"<p>{body}</p>"

        parts: list = []
        if summary:
            parts.append(f"<p><em>{summary}</em></p>")
        for s in sections:
            heading = (s.get("heading") or "").strip()
            body = (s.get("content") or "").strip()
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            if body:
                parts.append(body if body.startswith("<") else f"<p>{body}</p>")
        for cta in ctas or []:
            if cta.get("type") == "affiliate" and cta.get("target"):
                anchor = cta.get("anchor", "Learn more")
                parts.append(
                    f'<p><a href="{cta["target"]}" '
                    f'rel="sponsored nofollow noopener" '
                    f'target="_blank">{anchor}</a></p>'
                )
        return "\n".join(parts)

    # ---- http plumbing ------------------------------------------------------
    def _get(self, path: str) -> dict:
        r = requests.get(
            f"{self.api_url}{path}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        if not r.ok:
            raise GhostPublishError(f"GET {path} -> {r.status_code}: {r.text[:500]}")
        return r.json()

    def _send(self, method: str, path: str, body: dict) -> PublishResult:
        r = requests.request(
            method,
            f"{self.api_url}{path}",
            headers=self._headers(),
            json=body,
            timeout=self.timeout,
        )
        if not r.ok:
            log.error("Ghost %s %s failed: %s", method, path, r.text)
            raise GhostPublishError(
                f"{method} {path} -> {r.status_code}: {r.text[:500]}"
            )
        post = r.json()["posts"][0]
        return PublishResult(
            post_id=post["id"],
            url=post["url"],
            status=post["status"],
            updated_at=post["updated_at"],
        )


__all__ = ["GhostService", "GhostPublishError", "PublishResult"]
PYEOF

# Replace the deprecated WordPress stub with a re-export shim that points
# to the new Ghost service, so any lingering imports get a clear migration path.
echo "[2/9] Updating src/services/wordpress_service.py -> migration shim"
backup "automated-blog-system/src/services/wordpress_service.py"
write_file "automated-blog-system/src/services/wordpress_service.py" <<'PYEOF'
"""Deprecated WordPress service stub.

WordPress integration was removed; the system now publishes via Ghost
(see services/ghost_service.py). This stub remains only to surface a clear
error for any lingering legacy imports.
"""

class WordPressService:  # pragma: no cover
    def __init__(self, *_, **__):  # type: ignore
        raise RuntimeError(
            "WordPress integration has been removed. "
            "Use src.services.ghost_service.GhostService instead."
        )


__all__ = ["WordPressService"]
PYEOF

# ---------- 3. patch Article model ----------------------------------------
echo "[3/9] Patching src/models/product.py (Article: +ghost columns, +to_headless_contract)"
PRODUCT_PY="automated-blog-system/src/models/product.py"
backup "$PRODUCT_PY"

if grep -q "ghost_post_id" "$PRODUCT_PY"; then
  echo "  ℹ️  Article already has ghost_post_id; skipping model patch."
else
  python3 - <<'PYPATCH'
import re
from pathlib import Path

p = Path("automated-blog-system/src/models/product.py")
src = p.read_text()

# 1. Add columns after wordpress_post_id line.
new_cols = """    wordpress_post_id = db.Column(db.Integer)
    # Ghost Headless CMS publishing fields (PR #1)
    ghost_post_id = db.Column(db.String(64))
    published_url = db.Column(db.String(500))
    editorial_verdict = db.Column(db.String(20), default='PENDING')
    # PUBLISH | REVISE | REJECT | PENDING (set by EditorCrew in PR #2)"""
src = src.replace(
    "    wordpress_post_id = db.Column(db.Integer)",
    new_cols,
    1,
)

# 2. Add the new fields to to_dict() — append right before the closing brace
#    of the Article.to_dict return dict (the one containing 'wordpress_post_id').
def add_to_dict(match):
    block = match.group(0)
    if "ghost_post_id" in block:
        return block
    insert = (
        "            'wordpress_post_id': self.wordpress_post_id,\n"
        "            'ghost_post_id': self.ghost_post_id,\n"
        "            'published_url': self.published_url,\n"
        "            'editorial_verdict': self.editorial_verdict,\n"
    )
    return block.replace(
        "            'wordpress_post_id': self.wordpress_post_id,\n",
        insert,
        1,
    )

src = re.sub(
    r"def to_dict\(self\):\s+\"\"\"Convert article to dictionary\.\"\"\".*?\n        \}\n",
    add_to_dict,
    src,
    count=1,
    flags=re.DOTALL,
)

# 3. Insert to_headless_contract() right before Article.__repr__.
contract = '''
    def to_headless_contract(self):
        """Return the article in the Headless Article Contract shape
        consumed by GhostService.publish_article()."""
        keywords = json.loads(self.keywords) if self.keywords else []
        return {
            "id": self.id,
            "title": self.title,
            # GhostService uses 'sections' if present, else falls back to 'content'.
            "content": self.content,
            "sections": [],
            "summary": (self.meta_description or "")[:300],
            "keywords": keywords,
            "calls_to_action": [],
            "meta": {
                "meta_title": self.title,
                "meta_description": self.meta_description,
            },
        }

'''
# Only insert in the Article class (the second __repr__ in the file).
parts = src.split("    def __repr__(self):")
if len(parts) >= 3:
    parts[-1] = "    def __repr__(self):" + parts[-1]
    parts[-2] = parts[-2] + contract + "    def __repr__(self):"
    parts.pop(-2)  # rejoin
    src = "    def __repr__(self):".join(parts[:-1]) + parts[-1]
else:
    # Fallback: append at end of file (shouldn't happen with current file shape).
    src += contract

p.write_text(src)
print("  ✅ patched product.py")
PYPATCH
fi

# ---------- 4. publisher route --------------------------------------------
echo "[4/9] Writing src/routes/publisher.py"
write_file "automated-blog-system/src/routes/publisher.py" <<'PYEOF'
"""Ghost publisher routes.

Endpoints (all under /api/publisher):
    GET  /health                 -> verify config + auth without publishing
    POST /publish/<article_id>   -> publish or update on Ghost
    POST /draft/<article_id>     -> create as draft on Ghost
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify

from src.models.product import Article
from src.models.user import db
from src.services.ghost_service import GhostPublishError, GhostService

logger = logging.getLogger(__name__)
publisher_bp = Blueprint("publisher", __name__)


def _refuse_unless_publishable(article):
    """Enforce APE-71 lesson: Publisher only publishes passing articles."""
    verdict = (article.editorial_verdict or "PENDING").upper()
    if verdict != "PUBLISH":
        return (
            jsonify(
                {
                    "success": False,
                    "error": (
                        f"Article {article.id} editorial_verdict is "
                        f"{article.editorial_verdict!r}; refusing to publish. "
                        "Only articles with verdict 'PUBLISH' may be sent to Ghost."
                    ),
                }
            ),
            409,
        )
    return None


@publisher_bp.route("/health", methods=["GET"])
def health():
    try:
        svc = GhostService()
        svc._get("/ghost/api/admin/posts/?limit=1")
        return jsonify({"success": True, "ghost": "reachable"})
    except GhostPublishError as e:
        return jsonify({"success": False, "error": str(e)}), 502


@publisher_bp.route("/publish/<int:article_id>", methods=["POST"])
def publish(article_id):
    article = Article.query.get_or_404(article_id)
    refusal = _refuse_unless_publishable(article)
    if refusal is not None:
        return refusal

    payload = article.to_headless_contract()
    try:
        svc = GhostService()
        if article.ghost_post_id:
            result = svc.update_article(article.ghost_post_id, payload)
        else:
            result = svc.publish_article(payload)
    except GhostPublishError as e:
        logger.exception("Ghost publish failed for article %s", article_id)
        return jsonify({"success": False, "error": str(e)}), 502

    article.ghost_post_id = result.post_id
    article.published_url = result.url
    article.status = "published"
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "article_id": article.id,
            "post_id": result.post_id,
            "url": result.url,
            "ghost_status": result.status,
        }
    )


@publisher_bp.route("/draft/<int:article_id>", methods=["POST"])
def draft(article_id):
    article = Article.query.get_or_404(article_id)
    payload = article.to_headless_contract()
    try:
        result = GhostService().save_draft(payload)
    except GhostPublishError as e:
        logger.exception("Ghost draft failed for article %s", article_id)
        return jsonify({"success": False, "error": str(e)}), 502

    article.ghost_post_id = result.post_id
    article.published_url = result.url
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "article_id": article.id,
            "post_id": result.post_id,
            "url": result.url,
            "ghost_status": result.status,
        }
    )
PYEOF

# ---------- 5. patch main.py ----------------------------------------------
echo "[5/9] Patching src/main.py to register publisher_bp"
MAIN_PY="automated-blog-system/src/main.py"
backup "$MAIN_PY"
if grep -q "publisher_bp" "$MAIN_PY"; then
  echo "  ℹ️  publisher_bp already registered; skipping main.py patch."
else
  python3 - <<'PYPATCH'
from pathlib import Path
p = Path("automated-blog-system/src/main.py")
src = p.read_text()

block = '''    try:
        from src.routes.publisher import publisher_bp
        app.register_blueprint(publisher_bp, url_prefix='/api/publisher')
        print("✅ Publisher blueprint registered successfully")
    except Exception as e:
        print(f"❌ Error registering publisher blueprint: {e}")

'''

# Insert immediately AFTER the automation blueprint registration block.
needle = 'print("✅ Automation blueprint registered successfully")'
if needle in src:
    # Find the end of the surrounding except block.
    idx = src.index(needle)
    end = src.index("\n", src.index("except", idx))
    end = src.index("\n", end + 1)  # consume the print(...) inside except
    src = src[: end + 1] + "\n" + block + src[end + 1 :]
else:
    # Fallback: append before the React serve route.
    src = src.replace(
        "    # Serve React Frontend",
        block + "    # Serve React Frontend",
        1,
    )

p.write_text(src)
print("  ✅ patched main.py")
PYPATCH
fi

# ---------- 6. requirements.txt -------------------------------------------
echo "[6/9] Updating requirements.txt"
REQ="automated-blog-system/requirements.txt"
backup "$REQ"
write_file "$REQ" <<'TXTEOF'
flask==3.1.0
flask-cors==6.0.1
flask-sqlalchemy==3.1.1
crewai>=0.100.0
crewai-tools>=0.40.0
tavily-python>=0.5.0
lancedb>=0.18.0
google-cloud-storage>=2.0.0
PyJWT>=2.8.0
requests>=2.31.0
responses>=0.25.0
pytest>=8.0.0
TXTEOF

# ---------- 7. migration script -------------------------------------------
echo "[7/9] Writing scripts/migrate_add_ghost_columns.py"
write_file "automated-blog-system/scripts/__init__.py" <<'PYEOF'
PYEOF
write_file "automated-blog-system/scripts/migrate_add_ghost_columns.py" <<'PYEOF'
"""One-shot migration: add Ghost publishing columns to `articles`.

Idempotent — safe to run more than once. PR #3 will introduce Alembic and
this script will become obsolete.

Usage (from automated-blog-system/):
    python -m scripts.migrate_add_ghost_columns
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text  # noqa: E402

from src.main import create_app  # noqa: E402
from src.models.user import db  # noqa: E402

NEW_COLUMNS = {
    "ghost_post_id": "VARCHAR(64)",
    "published_url": "VARCHAR(500)",
    "editorial_verdict": "VARCHAR(20) DEFAULT 'PENDING'",
}


def run() -> None:
    app = create_app()
    with app.app_context():
        insp = inspect(db.engine)
        existing = {c["name"] for c in insp.get_columns("articles")}
        added = []
        with db.engine.begin() as conn:
            for col, ddl in NEW_COLUMNS.items():
                if col in existing:
                    continue
                conn.execute(text(f"ALTER TABLE articles ADD COLUMN {col} {ddl}"))
                added.append(col)
        if added:
            print(f"✅ Added columns to articles: {', '.join(added)}")
        else:
            print("ℹ️  All Ghost columns already present; nothing to do.")


if __name__ == "__main__":
    run()
PYEOF

# ---------- 8. tests ------------------------------------------------------
echo "[8/9] Writing test_ghost_publisher.py"
write_file "automated-blog-system/test_ghost_publisher.py" <<'PYEOF'
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

os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault(
    "GHOST_ADMIN_KEY",
    "0123456789abcdef01234567:" + "a" * 64,
)

from src.main import create_app  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402
from src.services.ghost_service import GhostService  # noqa: E402


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
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
PYEOF

# ---------- 9. README + todo + GOALS + RUN --------------------------------
echo "[9/9] Writing GOALS.md, RUN.md, README.md, todo.md (root)"

backup "README.md"
backup "todo.md"