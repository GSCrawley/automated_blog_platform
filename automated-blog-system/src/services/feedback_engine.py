"""Performance Feedback Engine (PR #7).

This module closes the content improvement loop. It has two responsibilities:

1. **Statistical proposals** — compare per-Blueprint-field conformance
   against article performance (ROI).  Requires ``min_n`` articles per
   comparison bucket; default is **3** (revised down from the original
   plan's 10 — a single strong baseline article plus two follow-ups is
   sufficient for early signal; raise ``min_n`` per-niche once data grows).

2. **Conformance-gap proposals** — compare a specific article against the
   *currently active* Blueprint and surface every high-confidence field
   where the article is non-conformant.  These do **not** require historical
   performance data and fire from the very first published article.

Design:

- No auto-apply.  Every proposal is a row in ``blueprint_proposals`` or
  ``article_improvement_proposals`` with ``status='pending'``.  A human
  reviews + accepts/rejects via the UI.

- On accept of a ``BlueprintProposal``, a new Blueprint version is created
  (PR #5a machinery) and ``generate_improvement_proposals`` is fanned out
  across all published articles in the same niche (rate-limited background).

- No LLM calls in this module.  All analysis is statistical / rule-based.
"""
from __future__ import annotations

import json
import logging
import random
import statistics
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc

from src.models.analytics import (
    ArticleBlueprintSnapshot,
    ArticleImprovementProposal,
    ArticlePerformance,
    BlueprintProposal,
)
from src.models.pattern_library import BlueprintRow
from src.models.product import Article
from src.models.user import db

logger = logging.getLogger(__name__)

# Default minimum articles per comparison bucket before we surface a
# statistical proposal. Lower than the original plan's 10 because a
# high-quality baseline article provides a strong conformance signal even
# with few data points.
DEFAULT_MIN_N = 3

# Bootstrap resamples for confidence-interval estimation.
_BOOTSTRAP_N = 1000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _median(values: List[float]) -> float:
    if not values:
        return 0.0
    return statistics.median(values)


def _bootstrap_ci(
    values: List[float], confidence: float = 0.95, n_resamples: int = _BOOTSTRAP_N
) -> Tuple[float, float]:
    """Return a ``(lower, upper)`` bootstrap confidence interval."""
    if len(values) < 2:
        v = values[0] if values else 0.0
        return (v, v)
    medians = []
    for _ in range(n_resamples):
        sample = random.choices(values, k=len(values))
        medians.append(statistics.median(sample))
    medians.sort()
    alpha = 1 - confidence
    lo_idx = int(n_resamples * alpha / 2)
    hi_idx = int(n_resamples * (1 - alpha / 2)) - 1
    return (medians[max(0, lo_idx)], medians[min(len(medians) - 1, hi_idx)])


def _is_conformant(field: str, value: Any, blueprint: BlueprintRow) -> bool:
    """Return True if ``value`` satisfies the blueprint constraint for ``field``."""
    if field == "word_count_range":
        if isinstance(value, (int, float)):
            return (blueprint.word_count_lo or 0) <= value <= (blueprint.word_count_hi or 999999)
        return True
    if field == "h2_count_range":
        if isinstance(value, (int, float)):
            return (blueprint.h2_count_lo or 0) <= value <= (blueprint.h2_count_hi or 999999)
        return True
    if field == "has_comparison_table":
        return bool(value) == bool(blueprint.profile_aggregate_has("has_comparison_table"))
    if field == "has_faq":
        return bool(value) == bool(blueprint.profile_aggregate_has("has_faq"))
    if field == "requires_feature_image":
        return (not blueprint.requires_feature_image) or bool(value)
    if field == "requires_schema_markup":
        return (not blueprint.requires_schema_markup) or bool(value)
    if field == "min_internal_links":
        if isinstance(value, (int, float)):
            return value >= (blueprint.min_internal_links or 0)
        return True
    return True


def _article_field_value(field: str, article: Article) -> Any:
    """Extract the article's current value for a blueprint field."""
    if field == "word_count_range":
        return article.word_count or 0
    if field == "h2_count_range":
        content = article.content or ""
        import re
        return len(re.findall(r"<h2[\s>]", content, re.IGNORECASE))
    if field == "requires_feature_image":
        contract = article.to_headless_contract()
        return bool((contract.get("meta") or {}).get("feature_image"))
    if field == "min_internal_links":
        content = article.content or ""
        import re
        return len(re.findall(r'href=["\']/', content, re.IGNORECASE))
    if field in ("has_comparison_table", "has_faq"):
        content = article.content or ""
        if field == "has_comparison_table":
            return bool("<table" in content.lower())
        return bool("faq" in content.lower() or "<details" in content.lower())
    return None


def _blueprint_field_recommendation(field: str, blueprint: BlueprintRow) -> Any:
    """Return the Blueprint's target value for a field."""
    if field == "word_count_range":
        return [blueprint.word_count_lo, blueprint.word_count_hi]
    if field == "h2_count_range":
        return [blueprint.h2_count_lo, blueprint.h2_count_hi]
    if field == "has_comparison_table":
        return blueprint.profile_aggregate_has("has_comparison_table")
    if field == "has_faq":
        return blueprint.profile_aggregate_has("has_faq")
    if field == "requires_feature_image":
        return blueprint.requires_feature_image
    if field == "requires_schema_markup":
        return blueprint.requires_schema_markup
    if field == "min_internal_links":
        return blueprint.min_internal_links
    return None


# ---------------------------------------------------------------------------
# Patch BlueprintRow with a helper not in the original model
# ---------------------------------------------------------------------------


def _profile_aggregate_has(self, key: str) -> bool:
    """Return the modal bool for a structural field from the aggregate JSON."""
    try:
        agg = json.loads(self.profile_aggregate or "{}")
        val = agg.get(key)
        if val is None:
            return False
        if isinstance(val, dict):
            return bool(val.get("modal") or val.get("value") or val.get("mean", 0) >= 0.5)
        return bool(val)
    except (TypeError, ValueError):
        return False


BlueprintRow.profile_aggregate_has = _profile_aggregate_has


# ---------------------------------------------------------------------------
# HIGH-CONFIDENCE fields we check for conformance gaps
# ---------------------------------------------------------------------------

_CONFORMANCE_FIELDS = [
    "word_count_range",
    "h2_count_range",
    "has_comparison_table",
    "has_faq",
    "requires_feature_image",
    "requires_schema_markup",
    "min_internal_links",
]

_FIELD_RATIONALE: Dict[str, str] = {
    "word_count_range": (
        "Article word count is outside the Blueprint's target range. "
        "Articles in this range have historically performed better in this niche."
    ),
    "h2_count_range": (
        "The number of H2 headings is outside the Blueprint's recommended range. "
        "Top-ranking articles in this niche use this structure."
    ),
    "has_comparison_table": (
        "The Blueprint requires a comparison table — a high-confidence pattern in "
        "top-10 SERP results for this niche. Adding one may improve rankings."
    ),
    "has_faq": (
        "An FAQ section is a high-confidence pattern in this niche's top-10 SERP "
        "results. Adding one targets featured-snippet opportunities."
    ),
    "requires_feature_image": (
        "The Blueprint requires a feature image. Ghost uses it for social sharing "
        "previews; missing it reduces click-through from social distribution."
    ),
    "requires_schema_markup": (
        "The Blueprint requires schema markup. Top-ranking articles in this niche "
        "use structured data for rich-result eligibility."
    ),
    "min_internal_links": (
        "The article has fewer internal links than the Blueprint recommends. "
        "Internal linking improves crawl coverage and distributes page authority."
    ),
}


# ---------------------------------------------------------------------------
# Conformance-gap proposals (no performance data needed)
# ---------------------------------------------------------------------------


def generate_improvement_proposals(
    article_id: int,
    *,
    blueprint_proposal_id: Optional[int] = None,
    blueprint: Optional[BlueprintRow] = None,
) -> List[ArticleImprovementProposal]:
    """Scan one article for Blueprint conformance gaps and insert proposals.

    Runs from article 1 — no historical performance data required.

    Parameters
    ----------
    article_id:
        The article to scan.
    blueprint_proposal_id:
        Optional FK to the ``BlueprintProposal`` that triggered this call.
    blueprint:
        Pre-loaded BlueprintRow (skip DB lookup). Useful in tests.

    Returns
    -------
    list[ArticleImprovementProposal]
        Newly-inserted (pending) proposals. Already-open proposals for the
        same ``(article_id, blueprint_field)`` are skipped to avoid
        duplicates.
    """
    article = Article.query.get(article_id)
    if article is None:
        logger.warning("generate_improvement_proposals: article %d not found", article_id)
        return []

    if blueprint is None:
        from src.services.blueprint_repo import get_active_blueprint_row
        blueprint = get_active_blueprint_row(article.niche_id)
    if blueprint is None:
        logger.info("No blueprint for niche %s — skipping improvement proposals", article.niche_id)
        return []

    # Load confidence tiers so we only flag high-confidence gaps.
    try:
        confidence_tiers: Dict[str, str] = json.loads(blueprint.confidence_tiers or "{}")
    except (TypeError, ValueError):
        confidence_tiers = {}

    created: List[ArticleImprovementProposal] = []

    for field in _CONFORMANCE_FIELDS:
        # Skip fields with low confidence (not an empirically strong signal).
        tier = confidence_tiers.get(field, "medium")
        if tier == "low":
            continue

        current_val = _article_field_value(field, article)
        if current_val is None:
            continue

        if _is_conformant(field, current_val, blueprint):
            continue

        # Check for an already-open proposal on this field.
        existing = ArticleImprovementProposal.query.filter_by(
            article_id=article_id,
            blueprint_field=field,
            status="pending",
        ).first()
        if existing:
            continue

        recommendation = _blueprint_field_recommendation(field, blueprint)
        proposal = ArticleImprovementProposal(
            article_id=article_id,
            blueprint_proposal_id=blueprint_proposal_id,
            blueprint_field=field,
            current_value_json=json.dumps(current_val),
            recommended_value_json=json.dumps(recommendation),
            rationale=_FIELD_RATIONALE.get(field, ""),
            evidence_json=json.dumps(
                {
                    "blueprint_id": blueprint.id,
                    "confidence_tier": tier,
                    "niche_id": article.niche_id,
                }
            ),
        )
        db.session.add(proposal)
        created.append(proposal)

    if created:
        db.session.commit()
        logger.info(
            "Generated %d improvement proposals for article %d", len(created), article_id
        )
    return created


# ---------------------------------------------------------------------------
# Statistical Blueprint-effectiveness analysis
# ---------------------------------------------------------------------------


def compute_blueprint_effectiveness(
    niche_id: int, *, min_n: int = DEFAULT_MIN_N
) -> Dict[str, Any]:
    """Analyse per-field conformance vs. performance within a niche.

    For each Blueprint field, buckets published articles by conformance
    (yes/no or in-range/out-of-range), computes median ROI per bucket,
    and reports effect size + 95% bootstrap CI.

    Returns a dict of per-field analyses. Fields with fewer than ``min_n``
    articles in *either* bucket are reported but marked ``insufficient_data``
    so the feedback loop does not auto-propose from noisy estimates.

    Parameters
    ----------
    niche_id:
        Scope the analysis to this niche.
    min_n:
        Minimum articles per bucket required before reporting an effect.
        Default is 3; raise once you have more data.
    """
    # Load all published articles in this niche that have performance data.
    performances = (
        db.session.query(ArticlePerformance, Article)
        .join(Article, ArticlePerformance.article_id == Article.id)
        .filter(
            Article.niche_id == niche_id,
            Article.status == "published",
        )
        .all()
    )

    if not performances:
        return {"niche_id": niche_id, "fields": {}, "message": "No published articles."}

    # Get active blueprint for the niche.
    from src.services.blueprint_repo import get_active_blueprint_row
    blueprint = get_active_blueprint_row(niche_id)
    if blueprint is None:
        return {"niche_id": niche_id, "fields": {}, "message": "No blueprint found for niche."}

    overall_rois = [
        float(p.roi)
        for p, _ in performances
        if p.roi is not None
    ]
    overall_median = _median(overall_rois)

    field_results: Dict[str, Any] = {}

    for field in _CONFORMANCE_FIELDS:
        conformant_rois: List[float] = []
        nonconformant_rois: List[float] = []

        for perf, article in performances:
            if perf.roi is None:
                continue
            val = _article_field_value(field, article)
            if val is None:
                continue
            if _is_conformant(field, val, blueprint):
                conformant_rois.append(float(perf.roi))
            else:
                nonconformant_rois.append(float(perf.roi))

        n_conf = len(conformant_rois)
        n_non = len(nonconformant_rois)

        if n_conf < min_n or n_non < min_n:
            field_results[field] = {
                "status": "insufficient_data",
                "n_conformant": n_conf,
                "n_nonconformant": n_non,
                "min_n_required": min_n,
            }
            continue

        med_conf = _median(conformant_rois)
        med_non = _median(nonconformant_rois)
        effect_size = (
            (med_conf - med_non) / overall_median if overall_median != 0 else 0.0
        )
        ci_conf = _bootstrap_ci(conformant_rois)
        ci_non = _bootstrap_ci(nonconformant_rois)

        field_results[field] = {
            "status": "ok",
            "n_conformant": n_conf,
            "n_nonconformant": n_non,
            "median_roi_conformant": med_conf,
            "median_roi_nonconformant": med_non,
            "effect_size": effect_size,
            "ci_conformant_95": ci_conf,
            "ci_nonconformant_95": ci_non,
        }

    return {"niche_id": niche_id, "blueprint_id": blueprint.id, "fields": field_results}


# ---------------------------------------------------------------------------
# Propose Blueprint updates from effectiveness findings
# ---------------------------------------------------------------------------


def propose_blueprint_updates(
    niche_id: int, *, min_n: int = DEFAULT_MIN_N, min_effect: float = 0.10
) -> List[BlueprintProposal]:
    """Convert effectiveness findings into ``BlueprintProposal`` rows.

    Only creates proposals for fields where:
    - The analysis has sufficient data (``status == 'ok'``).
    - The effect size ≥ ``min_effect`` (default 10 % of overall median ROI).
    - The nonconformant bucket outperforms the conformant bucket, OR where
      the conformant bucket is the lower performer — either direction
      warrants a proposal.
    - No ``pending`` proposal already exists for the same field + blueprint.

    Never mutates an existing Blueprint. The human must accept a proposal
    via ``POST /api/proposals/<id>/accept`` to create a new Blueprint version.
    """
    from src.services.blueprint_repo import get_active_blueprint_row
    blueprint = get_active_blueprint_row(niche_id)
    if blueprint is None:
        logger.info("propose_blueprint_updates: no blueprint for niche %d", niche_id)
        return []

    analysis = compute_blueprint_effectiveness(niche_id, min_n=min_n)
    created: List[BlueprintProposal] = []

    for field, result in analysis.get("fields", {}).items():
        if result.get("status") != "ok":
            continue
        effect = abs(result.get("effect_size", 0.0))
        if effect < min_effect:
            continue

        # Check for existing pending proposal.
        existing = BlueprintProposal.query.filter_by(
            blueprint_id=blueprint.id,
            blueprint_field=field,
            status="pending",
        ).first()
        if existing:
            continue

        current_val = _blueprint_field_recommendation(field, blueprint)

        # Propose the value from the *better-performing* bucket as the target.
        if result["median_roi_conformant"] >= result["median_roi_nonconformant"]:
            # Conformant > nonconformant → conformance is good; proposal may
            # be to tighten the range (e.g. raise min word count).
            proposed_val = current_val  # placeholder — fine-tuning requires more data
        else:
            # Nonconformant > conformant → current blueprint target is
            # counter-productive; propose relaxing or inverting it.
            proposed_val = None  # signal to human: review and revise

        proposal = BlueprintProposal(
            niche_id=niche_id,
            blueprint_id=blueprint.id,
            blueprint_field=field,
            current_value_json=json.dumps(current_val),
            proposed_value_json=json.dumps(proposed_val),
            evidence_json=json.dumps(
                {
                    "n_conformant": result["n_conformant"],
                    "n_nonconformant": result["n_nonconformant"],
                    "median_roi_conformant": result["median_roi_conformant"],
                    "median_roi_nonconformant": result["median_roi_nonconformant"],
                    "effect_size": result["effect_size"],
                    "ci_conformant_95": result["ci_conformant_95"],
                    "ci_nonconformant_95": result["ci_nonconformant_95"],
                }
            ),
        )
        db.session.add(proposal)
        created.append(proposal)

    if created:
        db.session.commit()
        logger.info(
            "Created %d blueprint proposals for niche %d", len(created), niche_id
        )
    return created


# ---------------------------------------------------------------------------
# Fan-out: generate article improvement proposals when blueprint is accepted
# ---------------------------------------------------------------------------


def fanout_improvement_proposals(
    blueprint_proposal_id: int,
    niche_id: Optional[int],
) -> int:
    """Scan all published articles in the niche and generate per-article
    improvement proposals for the field affected by the accepted
    ``BlueprintProposal``.

    Called in a background thread after ``POST /api/proposals/<id>/accept``
    so it does not block the accept response. Thread-safe: each article
    gets its own DB write cycle.

    Returns the total number of ``ArticleImprovementProposal`` rows created.
    """
    q = Article.query.filter(Article.status == "published")
    if niche_id is not None:
        q = q.filter(Article.niche_id == niche_id)
    articles = q.all()

    total = 0
    for article in articles:
        proposals = generate_improvement_proposals(
            article.id, blueprint_proposal_id=blueprint_proposal_id
        )
        total += len(proposals)

    logger.info(
        "fanout_improvement_proposals: generated %d proposals across %d articles in niche %s",
        total,
        len(articles),
        niche_id,
    )
    return total


__all__ = [
    "DEFAULT_MIN_N",
    "generate_improvement_proposals",
    "compute_blueprint_effectiveness",
    "propose_blueprint_updates",
    "fanout_improvement_proposals",
]
