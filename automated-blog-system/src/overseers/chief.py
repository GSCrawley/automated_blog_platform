"""Chief Overseer — the orchestrator of the overseer layer (PR #21).

One ``run_cycle()`` = one pass of the control loop:

    sense (all overseers) -> dedupe/persist findings -> resolve findings
    that stopped firing (and verify their applied actions) -> auto-apply
    AUTO_SAFE actions -> write an OverseerRun summary.

The Chief also owns the one cross-cutting financial guard: if the current
month's burn rate projects past the cap, it pauses *new* flows (in-flight
articles finish; nothing is deleted). Only a human can resume.

Triggers: APScheduler (every ``OVERSEER_INTERVAL_MINUTES``, default 30),
``POST /api/overseer/run`` (manual or a Grok Bot routine), or tests.
"""
from __future__ import annotations

import calendar
import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Iterable, List, Optional

from sqlalchemy.exc import IntegrityError

from src.models.overseer import OverseerAction, OverseerFinding, OverseerRun
from src.models.user import db
from src.overseers.actions import apply_action, dispatch_pending_retries, effective_risk
from src.overseers.audience import AudienceOverseer
from src.overseers.base import SEVERITY_ORDER, ActionSpec, BaseOverseer, Finding
from src.overseers.compliance import ComplianceOverseer
from src.overseers.content import ContentOverseer
from src.overseers.market import MarketOverseer
from src.overseers.revenue import RevenueOverseer
from src.overseers.systems import SystemsOverseer

log = logging.getLogger(__name__)


class ChiefOverseer(BaseOverseer):
    name = "chief"
    function = "Orchestration + budget"
    mandate = "Run the loop, prioritise findings, hold the monthly budget line."

    def sense(self) -> List[Finding]:
        from src.models.observability import Budget
        from src.services.cost_meter import DEFAULT_MONTHLY_CAP_USD

        month = self.now.strftime("%Y-%m")
        row = Budget.query.filter_by(month=month).first()
        spent = Decimal(row.spent_usd or 0) if row else Decimal(0)
        cap = Decimal(row.cap_usd or DEFAULT_MONTHLY_CAP_USD) if row else DEFAULT_MONTHLY_CAP_USD
        day = self.now.day
        days = calendar.monthrange(self.now.year, self.now.month)[1]
        if day < 3 or spent <= 0:
            return []  # too early in the month to project meaningfully
        projected = (spent / Decimal(day)) * Decimal(days)
        if projected <= cap:
            return []
        return [
            Finding(
                code="budget_burn_projection",
                title=f"Projected month spend ${projected:.2f} exceeds the ${cap:.2f} cap",
                severity="high",
                detail="New flows paused; in-flight articles continue. A human resumes.",
                evidence={"spent": str(spent), "cap": str(cap), "day": day, "days_in_month": days},
                subject_type="budget",
                subject_id=month,
                actions=[
                    ActionSpec("pause_pipeline", {"reason": f"projected ${projected:.2f} > cap ${cap:.2f}"}, risk="auto"),
                    ActionSpec("resume_pipeline", {}),
                ],
            )
        ]


def default_roster(now: Optional[datetime] = None) -> List[BaseOverseer]:
    return [
        ChiefOverseer(now),
        SystemsOverseer(now),
        ContentOverseer(now),
        MarketOverseer(now),
        RevenueOverseer(now),
        AudienceOverseer(now),
        ComplianceOverseer(now),
    ]


def _auto_apply_enabled(explicit: Optional[bool]) -> bool:
    if explicit is not None:
        return explicit
    return os.getenv("OVERSEER_AUTO_APPLY", "true").lower() == "true"


def _record_occurrence(row: OverseerFinding, finding: Finding, now: datetime) -> None:
    values = {
        "last_seen_at": now,
        "occurrences": OverseerFinding.occurrences + 1,
        "title": finding.title[:300],
    }
    if finding.evidence:
        values["evidence_json"] = json.dumps(finding.evidence, default=str)
    db.session.query(OverseerFinding).filter_by(id=row.id, status="open").update(
        values, synchronize_session=False
    )


def run_cycle(
    *,
    trigger: str = "manual",
    auto_apply: Optional[bool] = None,
    overseers: Optional[Iterable[BaseOverseer]] = None,
    now: Optional[datetime] = None,
) -> Dict:
    now = now or datetime.utcnow()
    roster = list(overseers) if overseers is not None else default_roster(now)
    try:
        dispatch_pending_retries()
    except Exception:
        db.session.rollback()
        log.exception("Could not dispatch pending overseer retries")
    run = OverseerRun(trigger=trigger, started_at=now)
    db.session.add(run)
    db.session.flush()

    seen: set = set()
    healthy: set = set()
    opened = 0
    per_overseer: Dict[str, int] = {}

    for ov in roster:
        try:
            with db.session.begin_nested():
                findings = ov.sense()
            healthy.add(ov.name)
        except Exception as e:  # an overseer bug must not stop the others
            log.exception("Overseer %s crashed", ov.name)
            findings = [
                Finding(
                    code="overseer_crashed",
                    title=f"{ov.name} overseer raised {type(e).__name__}",
                    severity="high",
                    category="engineering",
                    detail=str(e)[:500],
                    subject_type="overseer",
                    subject_id=ov.name,
                    actions=[ActionSpec("engineering_ticket", {"area": "overseer", "overseer": ov.name})],
                )
            ]
            ov_name = "systems"
        else:
            ov_name = ov.name
        per_overseer[ov.name] = len(findings)

        for f in findings:
            fp = f"{ov_name}|{f.fingerprint}"
            if fp in seen:
                continue
            seen.add(fp)
            existing = OverseerFinding.query.filter_by(fingerprint=fp, status="open").first()
            if existing:
                _record_occurrence(existing, f, now)
                continue
            try:
                with db.session.begin_nested():
                    row = OverseerFinding(
                        fingerprint=fp,
                        overseer=ov_name,
                        code=f.code,
                        severity=f.severity,
                        category=f.category,
                        title=f.title[:300],
                        detail=f.detail,
                        evidence_json=json.dumps(f.evidence, default=str) if f.evidence else None,
                        subject_type=f.subject_type,
                        subject_id=f.subject_id,
                        first_seen_at=now,
                        last_seen_at=now,
                        first_run_id=run.id,
                    )
                    db.session.add(row)
                    db.session.flush()
                    for spec in f.actions:
                        db.session.add(
                            OverseerAction(
                                finding_id=row.id,
                                kind=spec.kind,
                                risk=effective_risk(spec.kind, spec.risk),
                                params_json=json.dumps(spec.params, default=str),
                                created_at=now,
                            )
                        )
                opened += 1
            except IntegrityError:
                existing = OverseerFinding.query.filter_by(fingerprint=fp, status="open").first()
                if existing is None:
                    raise
                _record_occurrence(existing, f, now)

    # Verify: open findings from healthy overseers that did not fire this
    # cycle are resolved; their applied actions are marked verified.
    resolved = 0
    for row in OverseerFinding.query.filter(OverseerFinding.status == "open").all():
        if row.overseer in healthy and row.fingerprint not in seen:
            row.status = "resolved"
            row.resolved_at = now
            resolved += 1
            for act in row.actions:
                if act.status == "applied":
                    act.status = "verified"
                    act.verified_at = now
                elif act.status == "proposed":
                    act.status = "superseded"
    db.session.commit()

    auto_applied = 0
    if _auto_apply_enabled(auto_apply):
        pending = (
            OverseerAction.query.join(OverseerFinding)
            .filter(OverseerFinding.status == "open")
            .filter(OverseerAction.status == "proposed")
            .filter(OverseerAction.risk == "auto")
            .all()
        )
        for act in pending:
            if apply_action(act, by="overseer").status == "applied":
                auto_applied += 1

    open_rows = OverseerFinding.query.filter_by(status="open").all()
    top = sorted(open_rows, key=lambda r: (SEVERITY_ORDER.get(r.severity, 9), r.first_seen_at))[:10]
    run = db.session.get(OverseerRun, run.id)
    run.finished_at = datetime.utcnow()
    run.findings_opened = opened
    run.findings_resolved = resolved
    run.actions_auto_applied = auto_applied
    summary = {
        "per_overseer": per_overseer,
        "open_by_severity": {s: sum(1 for r in open_rows if r.severity == s) for s in SEVERITY_ORDER},
        "awaiting_approval": OverseerAction.query.join(OverseerFinding)
        .filter(OverseerFinding.status == "open", OverseerAction.status == "proposed", OverseerAction.risk == "approval")
        .count(),
        "top": [{"id": r.id, "severity": r.severity, "overseer": r.overseer, "title": r.title} for r in top],
    }
    run.summary_json = json.dumps(summary)
    db.session.commit()
    return run.to_dict()


__all__ = ["ChiefOverseer", "default_roster", "run_cycle"]
