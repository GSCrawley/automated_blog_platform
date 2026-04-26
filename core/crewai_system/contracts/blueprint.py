"""Blueprint contract + stub loader (PR #2).

A Blueprint describes the empirically-winning structural pattern the Editor
should measure an article against. PR #5a will populate Blueprints from real
SERP forensics; PR #2 ships a hand-written stub keyed by niche so PR #2's
plumbing is testable on its own.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

ConfidenceTier = Literal["high", "medium", "low"]


@dataclass
class Blueprint:
    id: str
    niche_id: Optional[int]
    target_query_cluster: List[str] = field(default_factory=list)
    word_count_range: Tuple[int, int] = (1500, 3000)
    h2_count_range: Tuple[int, int] = (4, 12)
    required_sections: List[str] = field(default_factory=list)
    target_keyword_density: Tuple[float, float] = (0.005, 0.025)
    min_internal_links: int = 0
    coverage_gaps: List[str] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    confidence_tier: ConfidenceTier = "medium"
    requires_feature_image: bool = False
    requires_schema_markup: bool = False

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Blueprint":
        return cls(
            id=data["id"],
            niche_id=data.get("niche_id"),
            target_query_cluster=list(data.get("target_query_cluster") or []),
            word_count_range=tuple(data.get("word_count_range") or (1500, 3000)),  # type: ignore[arg-type]
            h2_count_range=tuple(data.get("h2_count_range") or (4, 12)),  # type: ignore[arg-type]
            required_sections=list(data.get("required_sections") or []),
            target_keyword_density=tuple(  # type: ignore[arg-type]
                data.get("target_keyword_density") or (0.005, 0.025)
            ),
            min_internal_links=int(data.get("min_internal_links") or 0),
            coverage_gaps=list(data.get("coverage_gaps") or []),
            source_urls=list(data.get("source_urls") or []),
            confidence_tier=data.get("confidence_tier") or "medium",
            requires_feature_image=bool(data.get("requires_feature_image") or False),
            requires_schema_markup=bool(data.get("requires_schema_markup") or False),
        )


# ---------------------------------------------------------------------------
# Stub loader — replaced by PR #5a's SerpForensics-driven blueprints.
# ---------------------------------------------------------------------------

# Hand-written stubs keyed by lowercased niche name. Values are deliberately
# loose so a competently-written article passes; the Editor's job in PR #2 is
# to catch obvious structural failures, not to enforce a winning pattern (that
# arrives with PR #5a). Anything not listed falls through to ``_DEFAULT``.
_STUBS: Dict[str, Blueprint] = {
    "cybersecurity smb": Blueprint(
        id="bp_smb_cybersec_stub",
        niche_id=None,
        target_query_cluster=["best vpn smb", "vpn for small business 2026"],
        word_count_range=(1500, 3500),
        h2_count_range=(4, 12),
        required_sections=["intro", "comparison", "faq", "verdict"],
        target_keyword_density=(0.003, 0.025),
        min_internal_links=0,
        coverage_gaps=["pricing per seat", "migration from incumbent"],
        confidence_tier="medium",
    ),
}

_DEFAULT = Blueprint(
    id="bp_default_stub",
    niche_id=None,
    target_query_cluster=[],
    word_count_range=(1500, 3500),
    h2_count_range=(3, 12),
    required_sections=["intro", "comparison", "faq", "verdict"],
    target_keyword_density=(0.003, 0.025),
    min_internal_links=0,
    coverage_gaps=[],
    confidence_tier="low",
)


def load_stub_blueprint(niche_name: Optional[str]) -> Blueprint:
    """Return a hand-written Blueprint stub for the given niche, or a default.

    PR #5a replaces this with a Pattern-Library-backed lookup.
    """
    if not niche_name:
        return _DEFAULT
    return _STUBS.get(niche_name.strip().lower(), _DEFAULT)


__all__ = ["Blueprint", "ConfidenceTier", "load_stub_blueprint"]
