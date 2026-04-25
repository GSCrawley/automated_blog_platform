"""EditorialVerdict + AxisReport contract (PR #2).

The Editor's terminal output. Verdict is binary: ``PUBLISH`` or ``REJECT``.
There is no automated revision loop in this design — every article ends up in
the human review queue regardless of verdict (see PR #6). REJECT articles
arrive with the full axis report so a human reviewer can see why.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional

Axis = Literal["conformance", "content_quality", "monetization", "compliance"]
Verdict = Literal["PUBLISH", "REJECT"]


@dataclass
class AxisReport:
    """One axis's verdict on an article.

    ``checklist`` is a list of ``{item, passed, expected, actual, note}`` dicts.
    ``evidence`` is free-form machine-readable diagnostic data the axis chooses
    to expose (e.g. parsed word count, link counts, regex matches).
    """

    axis: Axis
    score: float
    passed: bool
    checklist: List[Dict[str, Any]] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "AxisReport":
        return cls(
            axis=data["axis"],
            score=float(data["score"]),
            passed=bool(data["passed"]),
            checklist=list(data.get("checklist") or []),
            evidence=dict(data.get("evidence") or {}),
        )


@dataclass
class EditorialVerdict:
    verdict: Verdict
    axis_reports: List[AxisReport]
    blocking_axes: List[Axis] = field(default_factory=list)
    article_id: Optional[int] = None
    blueprint_id: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "axis_reports": [r.to_json() for r in self.axis_reports],
            "blocking_axes": list(self.blocking_axes),
            "article_id": self.article_id,
            "blueprint_id": self.blueprint_id,
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "EditorialVerdict":
        return cls(
            verdict=data["verdict"],
            axis_reports=[AxisReport.from_json(r) for r in data.get("axis_reports", [])],
            blocking_axes=list(data.get("blocking_axes") or []),
            article_id=data.get("article_id"),
            blueprint_id=data.get("blueprint_id"),
        )


__all__ = ["Axis", "Verdict", "AxisReport", "EditorialVerdict"]
