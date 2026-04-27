"""Blueprint persistence + lookup (PR #5a).

Two responsibilities:

1. **Persist** a freshly-generated Blueprint as a :class:`BlueprintRow`,
   wiring up versioning (``parent_blueprint_id``, ``version``) and the
   per-field ``confidence_tiers`` map.
2. **Look up** the active Blueprint for a niche, refreshing via
   :class:`SerpForensics` when stale or missing — but only when the
   caller permits it (tests pass ``allow_refresh=False``).

This is the layer that replaces PR #2's hand-written
``load_stub_blueprint`` for the production path. The stub still exists as
the ultimate fallback when no DB row exists *and* refresh is disabled —
useful for local dev without API keys and for the unit tests.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import desc

from core.crewai_system.contracts.blueprint import Blueprint, load_stub_blueprint
from src.models.pattern_library import BlueprintRow, SerpProfile
from src.models.user import db
from src.services.serp_forensics import (
    ArticleProfile,
    DEFAULT_BLUEPRINT_TTL_DAYS,
    SerpForensics,
    is_blueprint_stale,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def get_active_blueprint_row(niche_id: Optional[int]) -> Optional[BlueprintRow]:
    """Return the freshest BlueprintRow for ``niche_id`` (or any niche if
    ``None``), or ``None`` when no row exists."""
    q = BlueprintRow.query
    if niche_id is not None:
        q = q.filter(BlueprintRow.niche_id == niche_id)
    return q.order_by(desc(BlueprintRow.generated_at)).first()


def get_blueprint_for_niche(
    *,
    niche_id: Optional[int],
    niche_name: Optional[str] = None,
    target_query_cluster: Optional[List[str]] = None,
    allow_refresh: bool = True,
    ttl_days: int = DEFAULT_BLUEPRINT_TTL_DAYS,
    forensics: Optional[SerpForensics] = None,
) -> Blueprint:
    """Return the active Blueprint for ``niche_id``.

    Order of operations:

    1. Fresh BlueprintRow exists → return it.
    2. Stale / missing AND ``allow_refresh`` AND a usable forensics
       instance → run :func:`refresh_blueprint`, persist, return it.
    3. Otherwise → :func:`load_stub_blueprint(niche_name)` (PR #2
       fallback).

    ``allow_refresh=False`` is the test-path: no network calls, only DB
    or stub. Production callers pass ``allow_refresh=True`` and rely on
    refresh failures (e.g. missing SERPER_API_KEY) to fall through to
    the stub gracefully.
    """
    row = get_active_blueprint_row(niche_id)
    if row is not None and not is_blueprint_stale(row.generated_at, ttl_days):
        return row.to_blueprint()

    if allow_refresh and target_query_cluster:
        try:
            new_bp = refresh_blueprint(
                niche_id=niche_id,
                target_query_cluster=target_query_cluster,
                parent=row,
                forensics=forensics,
            )
            return new_bp
        except Exception:  # pragma: no cover — refresh is best-effort
            logger.exception(
                "Blueprint refresh failed for niche %s; falling back",
                niche_id,
            )

    if row is not None:
        # Stale but the only thing we have — return rather than nothing.
        logger.info("Returning stale Blueprint %s (refresh unavailable)", row.id)
        return row.to_blueprint()

    return load_stub_blueprint(niche_name)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def persist_blueprint(
    blueprint: Blueprint,
    *,
    profile_aggregate: Optional[dict] = None,
    confidence_tiers: Optional[dict] = None,
    generated_cost_usd: Decimal = Decimal("0"),
    parent: Optional[BlueprintRow] = None,
) -> BlueprintRow:
    """Write the Blueprint as a new :class:`BlueprintRow`.

    If ``parent`` is given, the new row's ``version`` is ``parent.version + 1``
    and ``parent_blueprint_id = parent.id``. The new row's ``id`` is whatever
    the Blueprint dataclass carried (callers should ensure uniqueness; the
    aggregator's :func:`_suggest_blueprint_id` is timestamped to avoid
    collisions in practice)."""
    row = BlueprintRow.from_blueprint(
        blueprint,
        profile_aggregate=profile_aggregate,
        confidence_tiers=confidence_tiers,
        generated_cost_usd=generated_cost_usd,
        version=(parent.version + 1) if parent else 1,
        parent_blueprint_id=parent.id if parent else None,
    )
    row.generated_at = datetime.utcnow()
    db.session.add(row)
    db.session.commit()
    logger.info(
        "Persisted Blueprint %s v%d (niche=%s parent=%s)",
        row.id,
        row.version,
        row.niche_id,
        row.parent_blueprint_id,
    )
    return row


# ---------------------------------------------------------------------------
# Refresh — pull SERP, profile, aggregate, persist
# ---------------------------------------------------------------------------


def refresh_blueprint(
    *,
    niche_id: Optional[int],
    target_query_cluster: List[str],
    parent: Optional[BlueprintRow] = None,
    forensics: Optional[SerpForensics] = None,
    profiles: Optional[List[ArticleProfile]] = None,
) -> Blueprint:
    """Generate a new Blueprint version from current SERP data.

    ``profiles`` lets the caller pre-supply profiles (the unit tests do
    this so no network is needed). Otherwise we use :class:`SerpForensics`
    to pull the SERP for the *first* query in ``target_query_cluster``
    and profile each result.

    Caches the per-URL :class:`SerpProfile` rows so PR #5b's retrieval has
    a normalized table to read from.
    """
    if not target_query_cluster:
        raise ValueError("refresh_blueprint requires a non-empty target_query_cluster")

    sf = forensics or SerpForensics()
    pulled_profiles: List[ArticleProfile]

    if profiles is not None:
        pulled_profiles = profiles
    else:
        primary_query = target_query_cluster[0]
        results = sf.pull_serp(primary_query, k=10)
        pulled_profiles = []
        for r in results:
            try:
                profile = sf.profile_url(r.url, query=primary_query)
            except Exception:
                logger.exception("Failed to profile %s; skipping", r.url)
                continue
            pulled_profiles.append(profile)
            _upsert_serp_profile(r.url, primary_query, profile)
        if not pulled_profiles:
            raise RuntimeError("No URLs profiled — refresh aborted")

    blueprint, confidence, agg = sf.aggregate(
        pulled_profiles,
        niche_id=niche_id,
        target_query_cluster=target_query_cluster,
    )
    # Coverage gaps based on the original query cluster.
    blueprint.coverage_gaps = sf.identify_gaps(pulled_profiles, target_query_cluster)
    persist_blueprint(
        blueprint,
        profile_aggregate=agg,
        confidence_tiers=confidence,
        parent=parent,
    )
    return blueprint


def _upsert_serp_profile(url: str, query: str, profile: ArticleProfile) -> None:
    """Insert-or-update the cached SERP profile row for ``(url, query)``."""
    import json as _json  # local import — avoid module-level json shadowing

    row = SerpProfile.query.filter_by(url=url, query=query).first()
    if row is None:
        row = SerpProfile(url=url, query=query, profile_json=_json.dumps(profile.to_dict()))
        db.session.add(row)
    else:
        row.profile_json = _json.dumps(profile.to_dict())
        row.fetched_at = datetime.utcnow()
    db.session.commit()


__all__ = [
    "get_active_blueprint_row",
    "get_blueprint_for_niche",
    "persist_blueprint",
    "refresh_blueprint",
]
