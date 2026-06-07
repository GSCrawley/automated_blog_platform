"""Google Search Console analytics provider (PR #7).

Pulls per-URL daily impressions, clicks, CTR, and average position for
the trailing 28 days and upserts rows into ``article_analytics_daily``.

Authentication uses OAuth 2.0 credentials stored as a JSON file (path
given by env var ``GSC_CREDENTIALS_FILE``) or a service-account key. The
OAuth flow for connecting a new GSC property is user-initiated; this module
only performs data pulls once credentials exist.

Quota: GSC allows 1 200 queries / min / user. This provider sends at most
one batch request per daily ingest run, well within quota.

Design for testability:
  - All HTTP calls go through ``self._http`` which defaults to a real
    ``requests.Session`` but can be replaced by the caller (tests inject a
    ``responses``-mocked session).
  - :meth:`pull` accepts an optional ``property_url`` override so tests do
    not need env vars.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Iterator, List, Optional

import requests

try:
    import jwt as pyjwt
except ImportError:
    pyjwt = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_GSC_DISCOVERY_URL = "https://searchconsole.googleapis.com/webmasters/v3"
_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GSCProvider:
    """Pull GSC metrics and upsert them into ``article_analytics_daily``.

    Parameters
    ----------
    property_url:
        The GSC property to query, e.g. ``"https://yourdomain.com/"``.
        Falls back to the ``GSC_PROPERTY_URL`` env var.
    credentials_file:
        Path to the OAuth2 / service-account JSON credentials file.
        Falls back to the ``GSC_CREDENTIALS_FILE`` env var.
    http:
        Injectable :class:`requests.Session`. Defaults to a new session.
    """

    def __init__(
        self,
        property_url: Optional[str] = None,
        credentials_file: Optional[str] = None,
        http: Optional[requests.Session] = None,
    ) -> None:
        self._property_url = property_url or os.getenv("GSC_PROPERTY_URL", "")
        self._credentials_file = credentials_file or os.getenv("GSC_CREDENTIALS_FILE", "")
        self._http = http or requests.Session()
        self._access_token: Optional[str] = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def pull(
        self,
        *,
        article_url_map: Dict[str, int],
        trailing_days: int = 28,
        property_url: Optional[str] = None,
    ) -> List[Dict]:
        """Pull metrics for the given URLs and return upsert-ready dicts.

        Parameters
        ----------
        article_url_map:
            Mapping of ``{published_url: article_id}`` for all published
            articles. Only URLs present in this map are returned.
        trailing_days:
            How many trailing days to pull (default 28, max 500 per GSC).
        property_url:
            Override the property URL for this call (useful in tests).

        Returns
        -------
        list[dict]
            One dict per (article_id, date) pair with keys matching
            ``ArticleAnalyticsDaily`` columns.
        """
        prop = property_url or self._property_url
        if not prop:
            logger.warning("GSC_PROPERTY_URL not set — skipping GSC pull")
            return []

        if not self._access_token:
            self._access_token = self._authenticate()
            if not self._access_token:
                logger.warning("GSC authentication failed — skipping GSC pull")
                return []

        end_date = date.today() - timedelta(days=3)  # GSC data lags ~3 days
        start_date = end_date - timedelta(days=trailing_days - 1)

        raw_rows = self._fetch_rows(prop, start_date, end_date)
        results = []
        for row in raw_rows:
            url = row.get("keys", [None])[0]
            if not url or url not in article_url_map:
                continue
            row_date_str = row.get("keys", [None, None])[1] if len(row.get("keys", [])) > 1 else None
            if not row_date_str:
                continue
            try:
                row_date = date.fromisoformat(row_date_str)
            except ValueError:
                continue
            results.append(
                {
                    "article_id": article_url_map[url],
                    "date": row_date,
                    "source": "gsc",
                    "impressions": int(row.get("impressions", 0)),
                    "clicks": int(row.get("clicks", 0)),
                    "ctr": Decimal(str(row.get("ctr", 0))),
                    "avg_position": Decimal(str(row.get("position", 0))),
                    "conversions": 0,
                    "revenue_usd": Decimal("0"),
                }
            )
        logger.info("GSC pull returned %d rows for property %s", len(results), prop)
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _authenticate(self) -> Optional[str]:
        """Return a short-lived access token from the credentials file.

        Supports service-account key JSON only (most common for server
        deployments). Returns ``None`` if the file is missing or malformed.
        """
        if not self._credentials_file or not os.path.isfile(self._credentials_file):
            logger.debug("GSC credentials file not found at %r", self._credentials_file)
            return None
        try:
            with open(self._credentials_file) as fh:
                creds = json.load(fh)

            # Build a JWT assertion for service-account auth.
            if pyjwt is None:
                logger.warning("PyJWT not installed; GSC auth unavailable. pip install PyJWT")
                return None

            now = int(time.time())
            payload = {
                "iss": creds["client_email"],
                "sub": creds["client_email"],
                "scope": "https://www.googleapis.com/auth/webmasters.readonly",
                "aud": _TOKEN_URL,
                "iat": now,
                "exp": now + 3600,
            }
            private_key = creds["private_key"]
            assertion = pyjwt.encode(payload, private_key, algorithm="RS256")
            resp = self._http.post(
                _TOKEN_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json().get("access_token")
        except Exception:
            logger.exception("GSC token exchange failed")
            return None

    def _fetch_rows(
        self,
        property_url: str,
        start_date: date,
        end_date: date,
    ) -> Iterator[Dict]:
        """Yield raw GSC SearchAnalytics rows (page through all results)."""
        endpoint = (
            f"{_GSC_DISCOVERY_URL}/sites/{requests.utils.quote(property_url, safe='')}"
            "/searchAnalytics/query"
        )
        headers = {"Authorization": "Bearer " + (self._access_token or "")}
        start_row = 0
        row_limit = 25000

        while True:
            payload = {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "dimensions": ["page", "date"],
                "rowLimit": row_limit,
                "startRow": start_row,
            }
            try:
                resp = self._http.post(endpoint, json=payload, headers=headers, timeout=30)
                resp.raise_for_status()
            except requests.RequestException:
                logger.exception("GSC API request failed")
                return

            body = resp.json()
            rows = body.get("rows", [])
            yield from rows
            if len(rows) < row_limit:
                break
            start_row += row_limit


__all__ = ["GSCProvider"]
