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
