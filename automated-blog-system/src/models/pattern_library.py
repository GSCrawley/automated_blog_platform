"""DB models for the PR #5a Pattern Library — blueprints + serp_profiles.

The in-memory ``Blueprint`` *contract* lives at
:mod:`core.crewai_system.contracts.blueprint`; this module is the on-disk
representation. The two are kept separate on purpose:

- The contract is what crews and the Editor consume — a small, stable
  dataclass with no Flask / SQLAlchemy footprint.
- :class:`BlueprintRow` holds everything the Pattern Library needs to do
  versioning, freshness, attribution, and per-field confidence tiering. It
  knows how to round-trip itself to/from the contract.

PR #7's feedback engine joins published Articles against snapshots of
:class:`BlueprintRow`; PR #5a writes the rows but doesn't snapshot yet —
that's PR #7's ``article_blueprint_snapshot`` table.
"""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)

from core.crewai_system.contracts.blueprint import Blueprint
from src.models.user import db


class BlueprintRow(db.Model):
    """One row per published Blueprint version.

    The ``id`` is a stable string (e.g. ``bp_smb_cybersec_v3``) the rest of
    the system can pin to. A new SERP-forensics regeneration produces a
    new row with an incremented ``version`` and ``parent_blueprint_id``
    pointing at the prior version.
    """

    __tablename__ = "blueprints"

    id = Column(String(64), primary_key=True)
    niche_id = Column(Integer, ForeignKey("niches.id"), nullable=True)

    # JSON-encoded list/dict columns — kept as Text for SQLite portability;
    # accessors below handle the encode/decode.
    target_query_cluster = Column(Text)
    profile_aggregate = Column(Text)
    coverage_gaps = Column(Text)
    source_urls = Column(Text)
    confidence_tiers = Column(Text)
    required_sections = Column(Text)

    # Numerical aggregates broken out so the dashboard / Editor don't have
    # to parse JSON to read them.
    word_count_lo = Column(Integer)
    word_count_hi = Column(Integer)
    h2_count_lo = Column(Integer)
    h2_count_hi = Column(Integer)

    min_internal_links = Column(Integer, default=0, nullable=False)
    requires_feature_image = Column(Boolean, default=False, nullable=False)
    requires_schema_markup = Column(Boolean, default=False, nullable=False)

    confidence_tier = Column(String(16), default="medium", nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_cost_usd = Column(Numeric(10, 4), default=Decimal("0"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    parent_blueprint_id = Column(String(64), nullable=True)

    # ---- (de)serialization ------------------------------------------------

    @staticmethod
    def _dump(value: Any) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value)

    @staticmethod
    def _load(raw: Optional[str], default: Any) -> Any:
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return default

    def profile_aggregate_has(self, key: str) -> bool:
        """Return the modal bool for a structural field from ``profile_aggregate``."""
        agg = self._load(self.profile_aggregate, {}) or {}
        val = agg.get(key)
        if val is None:
            return False
        if isinstance(val, dict):
            return bool(val.get("modal") or val.get("value") or val.get("mean", 0) >= 0.5)
        return bool(val)

    def to_blueprint(self) -> Blueprint:
        """Project this row to the in-memory Blueprint contract.

        ``target_keyword_density`` isn't stored as a top-level column on the
        row — we keep it inside ``profile_aggregate`` and re-extract here so
        the contract round-trips faithfully.
        """
        agg: Dict[str, Any] = self._load(self.profile_aggregate, {}) or {}
        kd = agg.get("target_keyword_density") or [0.003, 0.025]
        return Blueprint(
            id=self.id,
            niche_id=self.niche_id,
            target_query_cluster=self._load(self.target_query_cluster, []) or [],
            word_count_range=(
                self.word_count_lo or 1500,
                self.word_count_hi or 3500,
            ),
            h2_count_range=(self.h2_count_lo or 4, self.h2_count_hi or 12),
            required_sections=self._load(self.required_sections, []) or [],
            target_keyword_density=tuple(kd) if isinstance(kd, list) else (0.003, 0.025),  # type: ignore[arg-type]
            min_internal_links=int(self.min_internal_links or 0),
            coverage_gaps=self._load(self.coverage_gaps, []) or [],
            source_urls=self._load(self.source_urls, []) or [],
            confidence_tier=self.confidence_tier or "medium",  # type: ignore[arg-type]
            requires_feature_image=bool(self.requires_feature_image),
            requires_schema_markup=bool(self.requires_schema_markup),
        )

    @classmethod
    def from_blueprint(
        cls,
        blueprint: Blueprint,
        *,
        profile_aggregate: Optional[Dict[str, Any]] = None,
        confidence_tiers: Optional[Dict[str, str]] = None,
        generated_cost_usd: Decimal = Decimal("0"),
        version: int = 1,
        parent_blueprint_id: Optional[str] = None,
    ) -> "BlueprintRow":
        """Build a row from an in-memory Blueprint plus the per-field
        confidence map and the raw aggregate (which carries fields that
        don't have dedicated columns, like ``target_keyword_density``)."""
        agg = dict(profile_aggregate or {})
        agg.setdefault(
            "target_keyword_density", list(blueprint.target_keyword_density)
        )
        return cls(
            id=blueprint.id,
            niche_id=blueprint.niche_id,
            target_query_cluster=cls._dump(blueprint.target_query_cluster),
            profile_aggregate=cls._dump(agg),
            coverage_gaps=cls._dump(blueprint.coverage_gaps),
            source_urls=cls._dump(blueprint.source_urls),
            confidence_tiers=cls._dump(confidence_tiers or {}),
            required_sections=cls._dump(blueprint.required_sections),
            word_count_lo=blueprint.word_count_range[0],
            word_count_hi=blueprint.word_count_range[1],
            h2_count_lo=blueprint.h2_count_range[0],
            h2_count_hi=blueprint.h2_count_range[1],
            min_internal_links=blueprint.min_internal_links,
            requires_feature_image=blueprint.requires_feature_image,
            requires_schema_markup=blueprint.requires_schema_markup,
            confidence_tier=blueprint.confidence_tier,
            generated_cost_usd=generated_cost_usd,
            version=version,
            parent_blueprint_id=parent_blueprint_id,
        )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<BlueprintRow {self.id} v{self.version} niche={self.niche_id}>"


class SerpProfile(db.Model):
    """Cached :class:`ArticleProfile` for a single (url, query).

    The (url, query) pair is unique — re-fetching upserts. ``fetched_at``
    drives freshness windows on the SERP-forensics side.
    """

    __tablename__ = "serp_profiles"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    query = Column(String(500), nullable=False)
    profile_json = Column(Text, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_profile_dict(self) -> Dict[str, Any]:
        try:
            return json.loads(self.profile_json or "{}")
        except (TypeError, ValueError):
            return {}

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SerpProfile {self.url[:40]} q={self.query[:30]}>"


__all__ = ["BlueprintRow", "SerpProfile"]
