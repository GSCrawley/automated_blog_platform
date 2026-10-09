"""Base types for the overseer layer (PR #21).

An overseer is a pure *sensor + diagnostician*: ``sense()`` reads system
state and returns :class:`Finding` objects. It never mutates state itself —
mutations happen only through :mod:`src.overseers.actions` handlers, which
the Chief Overseer applies under the risk gate.

That split keeps every overseer trivially testable (seed DB -> call
``sense()`` -> assert findings) and keeps the blast radius of any one
overseer bug to "a wrong row in a review queue".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass
class ActionSpec:
    """A concrete remediation an overseer proposes alongside a finding."""

    kind: str
    params: Dict[str, Any] = field(default_factory=dict)
    # ``risk`` is a *request*; the action registry has the final say (an
    # overseer cannot mark a dangerous handler as auto).
    risk: str = "approval"


@dataclass
class Finding:
    code: str
    title: str
    severity: str = "medium"
    category: str = "operational"  # operational|engineering|redundancy|compliance
    detail: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    subject_type: Optional[str] = None
    subject_id: Optional[str] = None
    actions: List[ActionSpec] = field(default_factory=list)

    @property
    def fingerprint(self) -> str:
        return f"{self.code}:{self.subject_type or '-'}:{self.subject_id or '-'}"


class BaseOverseer:
    """Subclass and implement :meth:`sense`."""

    #: short id stored on findings, e.g. ``"systems"``
    name: str = "base"
    #: the business function this overseer embodies (from the v1 blueprint)
    function: str = ""
    #: one-line mandate, surfaced on ``GET /api/overseer/roster``
    mandate: str = ""

    def __init__(self, now: Optional[datetime] = None) -> None:
        self._now = now

    @property
    def now(self) -> datetime:
        return self._now or datetime.utcnow()

    def ago(self, **kw) -> datetime:
        return self.now - timedelta(**kw)

    def sense(self) -> List[Finding]:  # pragma: no cover - abstract
        raise NotImplementedError

    def describe(self) -> Dict[str, str]:
        return {"name": self.name, "function": self.function, "mandate": self.mandate}


__all__ = ["ActionSpec", "Finding", "BaseOverseer", "SEVERITY_ORDER"]
