"""Overseer layer persistence (PR #21).

The overseer layer is a supervisory control plane that sits *above* the
CrewAI BlogCreationFlow, the analytics ingest, and the publisher. It never
writes content and never publishes. Its job is to:

1. **Sense**     — read the system's own telemetry (articles, cost events,
                   editorial reports, analytics, config) on a schedule.
2. **Diagnose**  — turn anomalies into typed :class:`OverseerFinding` rows.
3. **Propose**   — attach a concrete :class:`OverseerAction` to each finding.
4. **Gate**      — low-risk, reversible actions may auto-apply; everything
                   else waits for a human ``approve``.
5. **Verify**    — on the next cycle, a finding that no longer fires is
                   marked ``resolved`` and its applied action ``verified``.

Tables
------
``overseer_runs``      one row per cycle (who ran it, counts, duration)
``overseer_findings``  deduplicated by ``fingerprint`` while open
``overseer_actions``   proposed / approved / applied / verified / rejected
``overseer_controls``  tiny key/value store for control flags such as
                       ``pipeline_paused`` (read by CostMeter)
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Index, text

from src.models.user import db


class OverseerRun(db.Model):
    __tablename__ = "overseer_runs"

    id = db.Column(db.Integer, primary_key=True)
    trigger = db.Column(db.String(40), nullable=False, default="manual")  # manual|schedule|grok_routine|api
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    findings_opened = db.Column(db.Integer, default=0, nullable=False)
    findings_resolved = db.Column(db.Integer, default=0, nullable=False)
    actions_auto_applied = db.Column(db.Integer, default=0, nullable=False)
    summary_json = db.Column(db.Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "trigger": self.trigger,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "findings_opened": self.findings_opened,
            "findings_resolved": self.findings_resolved,
            "actions_auto_applied": self.actions_auto_applied,
            "summary": json.loads(self.summary_json) if self.summary_json else None,
        }


class OverseerFinding(db.Model):
    __tablename__ = "overseer_findings"

    id = db.Column(db.Integer, primary_key=True)
    # Stable identity for dedupe: "<code>:<subject>", e.g. "stuck_article:42".
    fingerprint = db.Column(db.String(200), nullable=False)
    overseer = db.Column(db.String(40), nullable=False, index=True)  # systems|content|market|revenue|audience|compliance|chief
    code = db.Column(db.String(80), nullable=False, index=True)
    severity = db.Column(db.String(10), nullable=False, default="medium")  # low|medium|high|critical
    category = db.Column(db.String(20), nullable=False, default="operational")  # operational|engineering|redundancy|compliance
    title = db.Column(db.String(300), nullable=False)
    detail = db.Column(db.Text, nullable=True)
    evidence_json = db.Column(db.Text, nullable=True)
    subject_type = db.Column(db.String(40), nullable=True)  # article|product|niche|system|config
    subject_id = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open", index=True)  # open|resolved|dismissed
    first_seen_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    occurrences = db.Column(db.Integer, nullable=False, default=1)
    first_run_id = db.Column(db.Integer, db.ForeignKey("overseer_runs.id"), nullable=True)

    actions = db.relationship("OverseerAction", backref="finding", lazy=True)

    __table_args__ = (
        Index(
            "uq_overseer_findings_open_fingerprint",
            "fingerprint",
            unique=True,
            sqlite_where=text("status = 'open'"),
            postgresql_where=text("status = 'open'"),
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "fingerprint": self.fingerprint,
            "overseer": self.overseer,
            "code": self.code,
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "detail": self.detail,
            "evidence": json.loads(self.evidence_json) if self.evidence_json else None,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "status": self.status,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "occurrences": self.occurrences,
            "actions": [a.to_dict() for a in self.actions],
        }


class OverseerAction(db.Model):
    __tablename__ = "overseer_actions"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("overseer_findings.id"), nullable=False, index=True)
    kind = db.Column(db.String(60), nullable=False)  # key into src.overseers.actions.HANDLERS
    risk = db.Column(db.String(10), nullable=False, default="approval")  # auto|approval
    params_json = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="proposed", index=True)
    # proposed -> approved -> applied -> verified
    #          \-> superseded (finding resolved before anyone acted)
    #          \-> rejected        \-> failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    decided_by = db.Column(db.String(100), nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    applied_at = db.Column(db.DateTime, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    result_json = db.Column(db.Text, nullable=True)
    # Reversal recipe captured at apply time so a human can roll back.
    undo_json = db.Column(db.Text, nullable=True)

    @property
    def params(self) -> Dict[str, Any]:
        return json.loads(self.params_json) if self.params_json else {}

    @property
    def undo(self) -> Optional[Dict[str, Any]]:
        return json.loads(self.undo_json) if self.undo_json else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "kind": self.kind,
            "risk": self.risk,
            "params": self.params,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "result": json.loads(self.result_json) if self.result_json else None,
            "undo": json.loads(self.undo_json) if self.undo_json else None,
        }


class OverseerControl(db.Model):
    """Small key/value table for control-plane flags (e.g. pipeline_paused)."""

    __tablename__ = "overseer_controls"

    key = db.Column(db.String(80), primary_key=True)
    value_json = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100), nullable=True)

    @staticmethod
    def get(key: str, default: Optional[Any] = None) -> Any:
        row = db.session.get(OverseerControl, key)
        if row is None:
            return default
        return json.loads(row.value_json)

    @staticmethod
    def set(key: str, value: Any, *, by: str = "overseer") -> None:
        row = db.session.get(OverseerControl, key)
        if row is None:
            row = OverseerControl(key=key, value_json=json.dumps(value), updated_by=by)
            db.session.add(row)
        else:
            row.value_json = json.dumps(value)
            row.updated_by = by
            row.updated_at = datetime.utcnow()


class OverseerDispatch(db.Model):
    """Durable, retryable dispatches created alongside approved actions."""

    __tablename__ = "overseer_dispatches"

    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.Integer, db.ForeignKey("overseer_actions.id"), nullable=False, unique=True)
    article_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    last_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


__all__ = ["OverseerRun", "OverseerFinding", "OverseerAction", "OverseerControl", "OverseerDispatch"]
