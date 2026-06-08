"""Analytics services package (PR #7).

Provides two data providers and a daily ingest orchestrator:

- :mod:`.gsc_provider`       — Google Search Console pull
- :mod:`.affiliate_provider` — Affiliate network adapters (Amazon Associates + base)
- :mod:`.ingest`             — Orchestrator: pull both, upsert, refresh performance
"""
from .gsc_provider import GSCProvider
from .affiliate_provider import AffiliateProvider, AmazonAssociatesProvider
from .ingest import run_daily_ingest, refresh_performance

__all__ = [
    "GSCProvider",
    "AffiliateProvider",
    "AmazonAssociatesProvider",
    "run_daily_ingest",
    "refresh_performance",
]
