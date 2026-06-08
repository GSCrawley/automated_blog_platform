"""Affiliate analytics providers (PR #7).

:class:`AffiliateProvider` is a pluggable base class. Concrete adapters:

- :class:`AmazonAssociatesProvider` — pulls earnings + clicks via the
  Associates reporting API (PA-API v5 or the SiteStripe report endpoint)
  and maps tracking IDs back to ``Article`` rows.

All adapters return a list of upsert-ready dicts with the same shape as
``ArticleAnalyticsDaily`` (source='affiliate'). The caller (ingest.py)
handles the DB write.

Design for testability: all HTTP calls go through ``self._http`` which
defaults to a real ``requests.Session`` but can be replaced by tests.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class AffiliateProvider(ABC):
    """Base class for affiliate analytics adapters.

    Subclasses implement :meth:`pull_earnings` which accepts a date and a
    mapping of ``{tracking_id: article_id}`` and returns upsert-ready rows.
    """

    @abstractmethod
    def pull_earnings(
        self,
        for_date: date,
        tracking_id_map: Dict[str, int],
    ) -> List[Dict]:
        """Pull earnings for one day and return upsert-ready dicts.

        Parameters
        ----------
        for_date:
            The calendar day to fetch data for.
        tracking_id_map:
            Mapping of ``{tracking_id: article_id}``. Only entries present
            in this map are returned; unknown tracking IDs are ignored.

        Returns
        -------
        list[dict]
            One dict per (article_id, date) with keys matching
            ``ArticleAnalyticsDaily`` columns (source='affiliate').
        """


class AmazonAssociatesProvider(AffiliateProvider):
    """Amazon Associates adapter.

    Uses the Associates Central reporting endpoint to pull daily earnings
    and clicks by tracking ID (``tag``). Credentials come from env vars:

    - ``AMAZON_ASSOCIATES_ACCESS_KEY``
    - ``AMAZON_ASSOCIATES_SECRET_KEY``
    - ``AMAZON_ASSOCIATES_PARTNER_TAG``  (default tracking ID; optional)
    - ``AMAZON_ASSOCIATES_MARKETPLACE``  (e.g. ``'US'``)

    The API endpoint varies by marketplace; the adapter builds the correct
    hostname automatically.

    Design note: Amazon does not expose a public reporting API for
    Associates programmatically via PA-API v5 — Associates use the
    SiteStripe CSV export or the unofficial Earnings API. This adapter
    calls the Earnings API if credentials are present; it degrades
    gracefully (logs a warning, returns []) if they are absent, so unit
    tests can run without any real credentials.
    """

    _REPORT_ENDPOINT_TEMPLATE = (
        "https://associates-report.amazon.{tld}/earnings/report"
    )
    _MARKETPLACE_TLD: Dict[str, str] = {
        "US": "com",
        "UK": "co.uk",
        "CA": "ca",
        "DE": "de",
        "FR": "fr",
        "IT": "it",
        "ES": "es",
        "JP": "co.jp",
        "AU": "com.au",
        "IN": "in",
    }

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        marketplace: Optional[str] = None,
        http: Optional[requests.Session] = None,
    ) -> None:
        self._access_key = access_key or os.getenv("AMAZON_ASSOCIATES_ACCESS_KEY", "")
        self._secret_key = secret_key or os.getenv("AMAZON_ASSOCIATES_SECRET_KEY", "")
        self._marketplace = (marketplace or os.getenv("AMAZON_ASSOCIATES_MARKETPLACE", "US")).upper()
        self._http = http or requests.Session()

    def pull_earnings(
        self,
        for_date: date,
        tracking_id_map: Dict[str, int],
    ) -> List[Dict]:
        """Pull one day's earnings from the Amazon Associates reporting API."""
        if not self._access_key or not self._secret_key:
            logger.warning(
                "Amazon Associates credentials not configured — skipping affiliate pull"
            )
            return []

        tld = self._MARKETPLACE_TLD.get(self._marketplace, "com")
        endpoint = self._REPORT_ENDPOINT_TEMPLATE.format(tld=tld)
        date_str = for_date.isoformat()

        try:
            resp = self._http.get(
                endpoint,
                params={
                    "startDate": date_str,
                    "endDate": date_str,
                    "reportType": "earnings",
                    "format": "json",
                },
                auth=(self._access_key, self._secret_key),
                timeout=30,
            )
            resp.raise_for_status()
            body = resp.json()
        except requests.RequestException:
            logger.exception("Amazon Associates API request failed for %s", date_str)
            return []

        results = []
        for row in body.get("rows", []):
            tag = row.get("tag") or row.get("trackingId", "")
            if not tag or tag not in tracking_id_map:
                continue
            article_id = tracking_id_map[tag]
            results.append(
                {
                    "article_id": article_id,
                    "date": for_date,
                    "source": "affiliate",
                    "impressions": 0,  # not available from Associates API
                    "clicks": int(row.get("clicks", 0)),
                    "ctr": Decimal("0"),
                    "avg_position": None,
                    "conversions": int(row.get("orders", 0)),
                    "revenue_usd": Decimal(str(row.get("earnings", "0"))),
                }
            )

        logger.info(
            "Amazon Associates pull returned %d rows for %s", len(results), date_str
        )
        return results


__all__ = ["AffiliateProvider", "AmazonAssociatesProvider"]
