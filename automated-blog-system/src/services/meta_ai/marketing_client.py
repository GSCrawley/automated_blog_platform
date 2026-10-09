"""Meta Graph / Marketing API client — PR #21.

Three capabilities, each deliberately narrow:

1. ``create_campaign_draft`` — creates an ad campaign with ``status=PAUSED``.
   There is no code path that creates an ACTIVE campaign; a human turns it
   on in Ads Manager after adding the ad set, creative and budget. The
   destination must be the blog, never Amazon (see compliance overseer).
2. ``send_conversion_event`` — Conversions API server event (e.g. ``Lead``
   when a reader joins the Ghost newsletter). Required for conversion-
   optimised lead campaigns.
3. ``post_link_to_page`` — organic distribution of a published article to
   the Facebook Page feed.

Env:
    META_GRAPH_API_VERSION   default v26.0 (current as of Oct 2026)
    META_AD_ACCOUNT_ID       numeric id, without the ``act_`` prefix
    META_SYSTEM_USER_TOKEN   token with ads_management
    META_PIXEL_ID            dataset / pixel id for Conversions API
    META_PAGE_ID, META_PAGE_ACCESS_TOKEN   for Page posting
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional

import requests

GRAPH = "https://graph.facebook.com"
DEFAULT_VERSION = "v26.0"
ALLOWED_OBJECTIVES = {"OUTCOME_TRAFFIC", "OUTCOME_LEADS", "OUTCOME_ENGAGEMENT", "OUTCOME_AWARENESS"}


class MetaGraphError(RuntimeError):
    pass


def _sha256(v: str) -> str:
    return hashlib.sha256(v.strip().lower().encode()).hexdigest()


class MetaMarketingClient:
    def __init__(self, http: Optional[requests.Session] = None, version: Optional[str] = None) -> None:
        self.http = http or requests.Session()
        self.version = version or os.getenv("META_GRAPH_API_VERSION") or DEFAULT_VERSION
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID", "").removeprefix("act_")
        self.token = os.getenv("META_SYSTEM_USER_TOKEN", "")
        self.pixel_id = os.getenv("META_PIXEL_ID", "")
        self.page_id = os.getenv("META_PAGE_ID", "")
        self.page_token = os.getenv("META_PAGE_ACCESS_TOKEN", "")

    def _url(self, path: str) -> str:
        return f"{GRAPH}/{self.version}/{path.lstrip('/')}"

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.http.post(self._url(path), data=data, timeout=60)
        try:
            body = resp.json()
        except ValueError:
            body = {"raw": resp.text[:500]}
        if resp.status_code >= 400 or "error" in body:
            raise MetaGraphError(f"Graph {path} {resp.status_code}: {json.dumps(body)[:400]}")
        return body

    # 1 ---------------------------------------------------------------
    def create_campaign_draft(
        self,
        name: str,
        *,
        objective: str = "OUTCOME_TRAFFIC",
        special_ad_categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not (self.ad_account_id and self.token):
            raise MetaGraphError("META_AD_ACCOUNT_ID / META_SYSTEM_USER_TOKEN not set")
        if objective not in ALLOWED_OBJECTIVES:
            raise MetaGraphError(f"objective {objective!r} not allowed")
        return self._post(
            f"act_{self.ad_account_id}/campaigns",
            {
                "name": name[:250],
                "objective": objective,
                "status": "PAUSED",  # never ACTIVE from code
                "special_ad_categories": json.dumps(special_ad_categories or []),
                "access_token": self.token,
            },
        )

    def set_campaign_status(self, campaign_id: str, status: str) -> Dict[str, Any]:
        """Only PAUSED / ARCHIVED are reachable from code (used for undo)."""
        if status not in ("PAUSED", "ARCHIVED"):
            raise MetaGraphError("Code may only pause or archive campaigns")
        return self._post(campaign_id, {"status": status, "access_token": self.token})

    # 2 ---------------------------------------------------------------
    def send_conversion_event(
        self,
        event_name: str,
        *,
        event_source_url: str,
        email: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        event_id: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None,
        test_event_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not (self.pixel_id and self.token):
            raise MetaGraphError("META_PIXEL_ID / META_SYSTEM_USER_TOKEN not set")
        user_data: Dict[str, Any] = {}
        if email:
            user_data["em"] = [_sha256(email)]
        if client_ip:
            user_data["client_ip_address"] = client_ip
        if user_agent:
            user_data["client_user_agent"] = user_agent
        event = {
            "event_name": event_name,
            "event_time": int(time.time()),
            "action_source": "website",
            "event_source_url": event_source_url,
            "user_data": user_data,
        }
        if event_id:
            event["event_id"] = event_id  # dedupe with browser Pixel
        if custom_data:
            event["custom_data"] = custom_data
        data = {"data": json.dumps([event]), "access_token": self.token}
        if test_event_code:
            data["test_event_code"] = test_event_code
        return self._post(f"{self.pixel_id}/events", data)

    # 3 ---------------------------------------------------------------
    def post_link_to_page(self, message: str, link: str) -> Dict[str, Any]:
        if not (self.page_id and self.page_token):
            raise MetaGraphError("META_PAGE_ID / META_PAGE_ACCESS_TOKEN not set")
        return self._post(f"{self.page_id}/feed", {"message": message, "link": link, "access_token": self.page_token})


__all__ = ["MetaMarketingClient", "MetaGraphError", "ALLOWED_OBJECTIVES"]
