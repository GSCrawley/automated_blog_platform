"""SERP Forensics + Pattern Library generator (PR #5a).

This is the service that makes the editor genuinely smart:

    pull_serp     → top-10 organic URLs for a target query (Serper API)
    profile_url   → scrape + extract structural features → ArticleProfile
    aggregate    → fold profiles into a Blueprint (medians, modal, IQR)
                    with per-field confidence tiers
    identify_gaps → questions/sub-topics under-addressed in the top 10

Design notes:

- HTML parsing is regex-based on purpose: deterministic, dependency-free,
  and the structural features we care about (h-tag counts, link rel
  attrs, FAQ/comparison markers) don't need a full DOM.
- All network calls go through ``requests`` so unit tests can mock them
  with the ``responses`` library. ``profile_url`` accepts an explicit
  ``html`` kwarg so tests can skip the network entirely.
- LLM-based fuzzy classification (intro pattern, section semantics) is
  injectable and skipped by default — same pattern as PR #2's content
  quality / compliance axes ("no network calls in unit tests").
"""
from __future__ import annotations

import json
import logging
import os
import re
import statistics
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import requests

from core.crewai_system.contracts.blueprint import Blueprint

logger = logging.getLogger(__name__)


# Type alias for an injectable LLM caller. Receives ``(prompt, context)``
# and returns a dict the caller interprets. None = skip.
LLMCaller = Callable[[str, Dict[str, Any]], Dict[str, Any]]


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class SerpResult:
    """One organic SERP entry."""

    url: str
    title: str
    snippet: str = ""
    position: int = 0


@dataclass
class ArticleProfile:
    """Structural fingerprint of one URL.

    Pure data, no judgment — judgments live in the Editor (PR #2's axes)
    and the Blueprint aggregator below. The doc lists ~25 fields; PR #5a
    populates the deterministic-from-HTML subset and leaves the LLM-only
    fields (``intro_pattern_type``) as None when no LLM is wired.
    """

    url: str
    title: str = ""
    word_count: int = 0
    h1: str = ""
    h2_headings: List[str] = field(default_factory=list)
    h3_headings: List[str] = field(default_factory=list)
    section_count: int = 0
    first_h2_position: int = -1
    has_comparison_table: bool = False
    has_faq: bool = False
    has_tldr: bool = False
    has_schema_markup: bool = False
    schema_types: List[str] = field(default_factory=list)
    internal_link_count: int = 0
    external_link_count: int = 0
    affiliate_link_count: int = 0
    affiliate_link_positions: List[int] = field(default_factory=list)
    image_count: int = 0
    first_image_position: int = -1
    meta_description: str = ""
    target_keyword: str = ""
    keyword_density: float = 0.0
    last_updated_at: Optional[str] = None
    reading_grade_level: Optional[float] = None
    intro_pattern_type: Optional[str] = None  # filled by injected LLM only
    cta_positions: List[int] = field(default_factory=list)
    source_attribution_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Regex toolkit (kept module-level so it compiles once)
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]+>")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_META_DESC_RE = re.compile(
    r'<meta\s+[^>]*name\s*=\s*"description"[^>]*content\s*=\s*"([^"]*)"',
    re.IGNORECASE,
)
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
_H2_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
_H3_RE = re.compile(r"<h3[^>]*>(.*?)</h3>", re.IGNORECASE | re.DOTALL)
_TABLE_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.IGNORECASE | re.DOTALL)
_AHREF_RE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_REL_RE = re.compile(r'rel\s*=\s*"([^"]*)"', re.IGNORECASE)
_HREF_RE = re.compile(r'href\s*=\s*"([^"]*)"', re.IGNORECASE)
_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_LDJSON_RE = re.compile(
    r'<script[^>]*type\s*=\s*"application/ld\+json"[^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_TIME_RE = re.compile(
    r'<time[^>]*datetime\s*=\s*"([^"]+)"', re.IGNORECASE
)
_FAQ_KEYWORDS = ("faq", "frequently asked", "frequently-asked")
_TLDR_KEYWORDS = ("tldr", "tl;dr", "summary", "tl dr")
_COMPARISON_HEADING_KEYWORDS = ("comparison", "compare", " vs ", "side-by-side")


def _strip_tags(html: str) -> str:
    return _TAG_RE.sub(" ", html or "")


def _word_count(text: str) -> int:
    return len([w for w in (text or "").split() if w.strip()])


def _heading_text(match_html: str) -> str:
    """Strip nested tags from a heading match (h1/h2/h3 contents)."""
    return _strip_tags(match_html).strip()


# ---------------------------------------------------------------------------
# Reading-grade — a tiny Flesch-Kincaid-ish estimator. Avoids pulling in
# textstat as a dep; the absolute value matters less than relative
# comparisons across the top-10.
# ---------------------------------------------------------------------------

_VOWEL_GROUP_RE = re.compile(r"[aeiouy]+", re.IGNORECASE)
_SENTENCE_END_RE = re.compile(r"[.!?]+")


def _estimate_grade(text: str) -> Optional[float]:
    text = (text or "").strip()
    if not text:
        return None
    sentences = max(1, len([s for s in _SENTENCE_END_RE.split(text) if s.strip()]))
    words = [w for w in re.findall(r"[A-Za-z]+", text)]
    if not words:
        return None
    syllables = sum(max(1, len(_VOWEL_GROUP_RE.findall(w))) for w in words)
    # Flesch-Kincaid grade level
    return round(
        0.39 * (len(words) / sentences) + 11.8 * (syllables / len(words)) - 15.59,
        2,
    )


# ---------------------------------------------------------------------------
# SerpForensics service
# ---------------------------------------------------------------------------


class SerpForensics:
    """Serper + scrape + profile + aggregate.

    Network credentials are read lazily from env, so importing this module
    never fails. ``llm`` is optional; when ``None``, fuzzy fields are left
    blank.
    """

    SERPER_URL = "https://google.serper.dev/search"
    DEFAULT_TIMEOUT_S = 20

    def __init__(
        self,
        serper_api_key: Optional[str] = None,
        firecrawl_api_key: Optional[str] = None,
        firecrawl_url: Optional[str] = None,
        llm: Optional[LLMCaller] = None,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        self.serper_api_key = serper_api_key or os.environ.get("SERPER_API_KEY")
        self.firecrawl_api_key = firecrawl_api_key or os.environ.get("FIRECRAWL_API_KEY")
        self.firecrawl_url = (
            firecrawl_url
            or os.environ.get("FIRECRAWL_URL")
            or "https://api.firecrawl.dev/v1/scrape"
        )
        self.llm = llm
        self.timeout_s = timeout_s

    # ---- SERP ------------------------------------------------------------

    def pull_serp(self, query: str, k: int = 10) -> List[SerpResult]:
        """Top-k organic results for ``query``. Raises if no API key set."""
        if not self.serper_api_key:
            raise RuntimeError(
                "SERPER_API_KEY not set; cannot pull SERP. (Inject results "
                "directly via aggregate() in tests.)"
            )
        r = requests.post(
            self.SERPER_URL,
            json={"q": query, "num": k},
            headers={"X-API-KEY": self.serper_api_key, "Content-Type": "application/json"},
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        body = r.json()
        out: List[SerpResult] = []
        for i, hit in enumerate(body.get("organic", [])[:k]):
            out.append(
                SerpResult(
                    url=hit.get("link", ""),
                    title=hit.get("title", ""),
                    snippet=hit.get("snippet", ""),
                    position=hit.get("position", i + 1),
                )
            )
        return out

    # ---- Scrape ----------------------------------------------------------

    def fetch_html(self, url: str) -> str:
        """Pull raw HTML for ``url``. Tries Firecrawl when configured, else
        a direct GET. Raises on non-2xx."""
        if self.firecrawl_api_key:
            r = requests.post(
                self.firecrawl_url,
                json={"url": url, "formats": ["html"]},
                headers={
                    "Authorization": f"Bearer {self.firecrawl_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout_s,
            )
            r.raise_for_status()
            payload = r.json()
            return payload.get("data", {}).get("html") or payload.get("html") or ""
        # Plain GET fallback. Useful for development and for sites Firecrawl
        # doesn't add value on.
        r = requests.get(url, timeout=self.timeout_s, headers={"User-Agent": "abp-pr5a/1.0"})
        r.raise_for_status()
        return r.text

    # ---- Profile a single URL --------------------------------------------

    def profile_url(
        self,
        url: str,
        *,
        html: Optional[str] = None,
        query: str = "",
    ) -> ArticleProfile:
        """Extract structural features.

        Pass ``html`` to skip the network fetch (the unit tests do this so
        results stay deterministic). ``query`` becomes the target keyword
        and drives ``keyword_density``.
        """
        body = html if html is not None else self.fetch_html(url)
        return _profile_from_html(url=url, html=body, query=query, llm=self.llm)

    # ---- Aggregate -------------------------------------------------------

    def aggregate(
        self,
        profiles: List[ArticleProfile],
        *,
        niche_id: Optional[int] = None,
        target_query_cluster: Optional[List[str]] = None,
        blueprint_id: Optional[str] = None,
    ) -> Tuple[Blueprint, Dict[str, str], Dict[str, Any]]:
        """Fold ``profiles`` into a Blueprint + per-field confidence map +
        the raw aggregate dict (for persistence).

        Returns ``(blueprint, confidence_tiers, profile_aggregate)``.
        """
        if not profiles:
            raise ValueError("aggregate() needs at least one profile")

        confidence: Dict[str, str] = {}
        agg: Dict[str, Any] = {}

        # ---- numeric fields → median + IQR-based confidence -----------
        word_counts = [p.word_count for p in profiles if p.word_count > 0]
        h2_counts = [p.section_count for p in profiles]

        wc_lo, wc_hi, wc_tier = _numeric_range(word_counts, fallback=(1500, 3500))
        h2_lo, h2_hi, h2_tier = _numeric_range(h2_counts, fallback=(4, 12))

        confidence["word_count"] = wc_tier
        confidence["h2_count"] = h2_tier
        agg["word_count_median"] = (
            int(statistics.median(word_counts)) if word_counts else None
        )
        agg["h2_count_median"] = (
            int(statistics.median(h2_counts)) if h2_counts else None
        )

        # ---- boolean fields → ≥80% mode rule --------------------------
        bool_fields = (
            "has_comparison_table",
            "has_faq",
            "has_tldr",
            "has_schema_markup",
        )
        bool_modes: Dict[str, bool] = {}
        for key in bool_fields:
            vals = [bool(getattr(p, key)) for p in profiles]
            mode_val, tier = _boolean_mode(vals)
            confidence[key] = tier
            bool_modes[key] = mode_val
        agg["bool_modes"] = bool_modes

        # ---- required sections — heading keywords seen in ≥50% --------
        required_sections = _common_section_keywords(profiles, threshold=0.5)
        confidence["required_sections"] = (
            "high" if len(required_sections) >= 2 else "medium" if required_sections else "low"
        )
        agg["required_sections_inferred"] = required_sections

        # ---- keyword density (median across profiles, fallback fixed) -
        densities = [p.keyword_density for p in profiles if p.keyword_density > 0]
        if densities:
            kd_med = statistics.median(densities)
            kd_lo, kd_hi = max(0.001, kd_med * 0.5), min(0.05, kd_med * 1.5)
        else:
            kd_lo, kd_hi = 0.003, 0.025
        agg["target_keyword_density"] = [kd_lo, kd_hi]

        # ---- internal links — minimum across profiles -----------------
        internal_counts = [p.internal_link_count for p in profiles]
        min_internal = max(0, int(statistics.median(internal_counts) // 2)) if internal_counts else 0
        confidence["min_internal_links"] = (
            "high" if internal_counts and min(internal_counts) >= 3 else "medium"
        )

        # ---- top-level confidence tier (worst of the structural ones) -
        tier_rank = {"high": 0, "medium": 1, "low": 2}
        worst_axis_tier = max(
            (confidence[k] for k in ("word_count", "h2_count", "required_sections")),
            key=lambda t: tier_rank.get(t, 1),
        )

        # ---- Blueprint id + version ----------------------------------
        bp_id = blueprint_id or _suggest_blueprint_id(niche_id, profiles)

        bp = Blueprint(
            id=bp_id,
            niche_id=niche_id,
            target_query_cluster=list(target_query_cluster or []),
            word_count_range=(wc_lo, wc_hi),
            h2_count_range=(h2_lo, h2_hi),
            required_sections=required_sections,
            target_keyword_density=(kd_lo, kd_hi),
            min_internal_links=min_internal,
            coverage_gaps=[],  # filled below by identify_gaps()
            source_urls=[p.url for p in profiles],
            confidence_tier=worst_axis_tier,  # type: ignore[arg-type]
            requires_feature_image=bool_modes.get("has_schema_markup", False) is False
            and any(p.image_count > 0 for p in profiles),
            requires_schema_markup=bool_modes.get("has_schema_markup", False),
        )
        return bp, confidence, agg

    # ---- Gap identification ---------------------------------------------

    def identify_gaps(
        self,
        profiles: List[ArticleProfile],
        query_cluster: List[str],
    ) -> List[str]:
        """Sub-topics from ``query_cluster`` that <30% of profiles cover.

        Coverage check: a query is "covered" by a profile if any of the
        profile's headings (h2 + h3) contains the query as a substring,
        case-insensitive. Tokenisation is intentionally crude — the goal
        is to spot the obvious gaps the top 10 left open, not to be
        a real semantic-coverage system (PR #5b's retrieval covers that).
        """
        if not profiles or not query_cluster:
            return []

        gaps: List[str] = []
        threshold = max(1, int(len(profiles) * 0.3))
        for q in query_cluster:
            needle = q.lower().strip()
            if not needle:
                continue
            covered = sum(
                1
                for p in profiles
                if any(needle in h.lower() for h in (p.h2_headings + p.h3_headings))
            )
            if covered < threshold:
                gaps.append(q)
        return gaps


# ---------------------------------------------------------------------------
# Profile extraction (module-level so it's exercise-able from tests)
# ---------------------------------------------------------------------------


def _profile_from_html(
    *,
    url: str,
    html: str,
    query: str = "",
    llm: Optional[LLMCaller] = None,
) -> ArticleProfile:
    body_text = _strip_tags(html)
    word_count = _word_count(body_text)
    title = _heading_text((_TITLE_RE.search(html) or _ZERO).group(1)) if _TITLE_RE.search(html) else ""
    h1_match = _H1_RE.search(html)
    h1 = _heading_text(h1_match.group(1)) if h1_match else ""

    h2_headings = [_heading_text(m) for m in _H2_RE.findall(html)]
    h3_headings = [_heading_text(m) for m in _H3_RE.findall(html)]
    first_h2_position = (
        _H2_RE.search(html).start() if _H2_RE.search(html) else -1
    )

    # Comparison table: a <table> exists OR an h2/h3 heading mentions comparison
    headings_blob = " ".join(h2_headings + h3_headings).lower()
    has_comparison_table = bool(_TABLE_RE.search(html)) or any(
        kw in headings_blob for kw in _COMPARISON_HEADING_KEYWORDS
    )
    has_faq = any(kw in headings_blob for kw in _FAQ_KEYWORDS)
    has_tldr = any(kw in headings_blob for kw in _TLDR_KEYWORDS)

    # Schema markup
    schema_blocks = _LDJSON_RE.findall(html)
    has_schema_markup = bool(schema_blocks) or 'itemtype=' in html.lower()
    schema_types: List[str] = []
    for block in schema_blocks:
        try:
            parsed = json.loads(block.strip())
        except (TypeError, ValueError):
            continue
        types_seen = parsed.get("@type") if isinstance(parsed, dict) else None
        if isinstance(types_seen, list):
            schema_types.extend(str(t) for t in types_seen)
        elif isinstance(types_seen, str):
            schema_types.append(types_seen)

    # Links
    internal = 0
    external = 0
    affiliate = 0
    affiliate_positions: List[int] = []
    cta_positions: List[int] = []
    domain = _domain_of(url)
    for m in _AHREF_RE.finditer(html):
        attrs = m.group(1)
        href_match = _HREF_RE.search(attrs)
        if not href_match:
            continue
        href = href_match.group(1)
        rel_match = _REL_RE.search(attrs)
        rel = rel_match.group(1).lower() if rel_match else ""
        if "sponsored" in rel:
            affiliate += 1
            affiliate_positions.append(m.start())
            cta_positions.append(m.start())
        elif _is_internal(href, domain):
            internal += 1
        else:
            external += 1

    # Images
    image_count = 0
    first_image_position = -1
    for m in _IMG_RE.finditer(html):
        if first_image_position == -1:
            first_image_position = m.start()
        image_count += 1

    # Meta description
    meta_match = _META_DESC_RE.search(html)
    meta_description = meta_match.group(1) if meta_match else ""

    # Keyword density
    keyword_density = 0.0
    if query and word_count:
        kw = query.lower().strip()
        if kw:
            keyword_density = body_text.lower().count(kw) / word_count

    # Updated
    last_updated_at: Optional[str] = None
    time_match = _TIME_RE.search(html)
    if time_match:
        last_updated_at = time_match.group(1)

    # Source attribution: external links *outside* affiliate set
    source_attribution_count = external

    # Optional LLM-only fuzzy field
    intro_pattern_type: Optional[str] = None
    if llm is not None:
        try:
            response = llm(
                "Classify the intro pattern (one of: question, statistic, story, "
                "list, contrarian, none). Respond with JSON {pattern: str}.",
                {"first_paragraph": body_text[:600]},
            )
            intro_pattern_type = (response or {}).get("pattern")
        except Exception:  # pragma: no cover - best-effort
            logger.exception("LLM intro classifier failed")

    return ArticleProfile(
        url=url,
        title=title,
        word_count=word_count,
        h1=h1,
        h2_headings=h2_headings,
        h3_headings=h3_headings,
        section_count=len(h2_headings),
        first_h2_position=first_h2_position,
        has_comparison_table=has_comparison_table,
        has_faq=has_faq,
        has_tldr=has_tldr,
        has_schema_markup=has_schema_markup,
        schema_types=schema_types,
        internal_link_count=internal,
        external_link_count=external,
        affiliate_link_count=affiliate,
        affiliate_link_positions=affiliate_positions,
        image_count=image_count,
        first_image_position=first_image_position,
        meta_description=meta_description,
        target_keyword=query,
        keyword_density=round(keyword_density, 4),
        last_updated_at=last_updated_at,
        reading_grade_level=_estimate_grade(body_text),
        intro_pattern_type=intro_pattern_type,
        cta_positions=cta_positions,
        source_attribution_count=source_attribution_count,
    )


# ---------------------------------------------------------------------------
# Aggregator helpers
# ---------------------------------------------------------------------------


def _numeric_range(
    values: List[int],
    *,
    fallback: Tuple[int, int],
) -> Tuple[int, int, str]:
    """Return ``(lo, hi, confidence_tier)`` for a numeric series.

    Tier rule (matches the doc's "≥80% / clustered / no pattern"):
        high   — coefficient of variation < 0.2 (very tight)
        medium — coefficient of variation 0.2 – 0.5
        low    — > 0.5 (or empty)
    The ``(lo, hi)`` band is the inter-quartile range when ≥4 samples
    exist; otherwise ``min..max``. Falls back to ``fallback`` on empty.
    """
    if not values:
        return (*fallback, "low")
    if len(values) >= 4:
        sorted_vals = sorted(values)
        q1 = sorted_vals[len(sorted_vals) // 4]
        q3 = sorted_vals[(3 * len(sorted_vals)) // 4]
        lo, hi = q1, q3
    else:
        lo, hi = min(values), max(values)
    mean_ = statistics.fmean(values)
    if mean_ == 0:
        return int(lo), int(hi), "low"
    cv = statistics.pstdev(values) / mean_ if len(values) > 1 else 0.0
    if cv < 0.2:
        tier = "high"
    elif cv < 0.5:
        tier = "medium"
    else:
        tier = "low"
    return int(lo), int(hi), tier


def _boolean_mode(values: List[bool]) -> Tuple[bool, str]:
    """Return ``(majority_value, tier)`` per the ≥80% rule."""
    if not values:
        return False, "low"
    true_share = sum(1 for v in values if v) / len(values)
    if true_share >= 0.8:
        return True, "high"
    if true_share <= 0.2:
        return False, "high"
    if 0.6 <= true_share or true_share <= 0.4:
        return (true_share > 0.5), "medium"
    return (true_share > 0.5), "low"


def _common_section_keywords(
    profiles: List[ArticleProfile], *, threshold: float
) -> List[str]:
    """Heading keywords appearing in ≥``threshold`` fraction of profiles.

    Returns a list of canonical keywords, deduped. Keywords come from a
    fixed set of section types we care about (intro / comparison / faq /
    verdict / pricing / how / why) so the result is stable across runs.
    """
    section_keywords = (
        "intro",
        "comparison",
        "faq",
        "verdict",
        "pricing",
        "how",
        "why",
        "conclusion",
    )
    n = len(profiles)
    if n == 0:
        return []
    out: List[str] = []
    for kw in section_keywords:
        hits = sum(
            1
            for p in profiles
            if any(kw in h.lower() for h in p.h2_headings)
        )
        if hits / n >= threshold:
            out.append(kw)
    return out


def _suggest_blueprint_id(
    niche_id: Optional[int],
    profiles: List[ArticleProfile],
) -> str:
    base = f"bp_niche{niche_id}" if niche_id else "bp_default"
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{base}_{stamp}_{len(profiles)}"


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

_DOMAIN_RE = re.compile(r"^(?:https?://)?([^/]+)")


def _domain_of(url: str) -> str:
    m = _DOMAIN_RE.search(url or "")
    return (m.group(1) if m else "").lower()


def _is_internal(href: str, domain: str) -> bool:
    if not href:
        return False
    if href.startswith("/") or href.startswith("#") or href.startswith("?"):
        return True
    if not domain:
        return False
    return domain in href.lower()


# Sentinel that's truthy in regex `.search()` but lets us avoid double-checks.
_ZERO = re.compile(r"\Z").search("")  # always-empty match; used as a fallback


# ---------------------------------------------------------------------------
# Freshness policy
# ---------------------------------------------------------------------------


DEFAULT_BLUEPRINT_TTL_DAYS = 30


def is_blueprint_stale(generated_at: datetime, ttl_days: int = DEFAULT_BLUEPRINT_TTL_DAYS) -> bool:
    """Per the doc: 30-day default. Per-niche overrides land in a future PR."""
    return datetime.utcnow() - generated_at > timedelta(days=ttl_days)


__all__ = [
    "ArticleProfile",
    "SerpResult",
    "SerpForensics",
    "is_blueprint_stale",
    "DEFAULT_BLUEPRINT_TTL_DAYS",
    "_profile_from_html",  # exposed for direct test access
]
