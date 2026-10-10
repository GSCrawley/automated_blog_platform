"""Overseer layer API (PR #21) — all under ``/api/overseer``.

    GET  /roster                         overseers, functions, mandates, auto-safe kinds
    GET  /status                         last run + open findings by severity + pause flag
    POST /run                            run one cycle   {trigger?, auto_apply?}
    GET  /runs                           recent runs
    GET  /findings                       ?status=open&overseer=&severity=&category=
    GET  /findings/<id>
    POST /findings/<id>/dismiss          {reason}
    POST /actions/<id>/approve           {by}   approve (and apply unless {"apply": false})
    POST /actions/<id>/reject            {by, reason}
    POST /actions/<id>/apply             apply an already-approved action
    GET  /engineering-queue              approved engineering tickets (JSON or ?format=md)
    POST /controls/pipeline/resume       human-only resume after an overseer pause
    GET  /author-model                   author-agent model gate: provider + verification checks
    POST /controls/author-model/revert   human: put the author back on the default model (locks the gate)
    POST /controls/author-model/rearm    human: clear a revert so the gate can verify again
    POST /revenue/associates-csv         body = Associates Central CSV; ?date=YYYY-MM-DD

Mutating endpoints require ``X-Overseer-Token``. The token must be configured
outside tests; production requests fail closed when it is absent.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from functools import wraps

from flask import Blueprint, jsonify, request

from src.models.overseer import OverseerAction, OverseerControl, OverseerFinding, OverseerRun
from src.models.user import db

overseer_bp = Blueprint("overseer", __name__)
log = logging.getLogger(__name__)


def _err(msg: str, code: int):
    return jsonify({"success": False, "error": msg}), code


def _guarded(fn):
    @wraps(fn)
    def inner(*a, **kw):
        token = os.getenv("OVERSEER_API_TOKEN")
        if not token:
            from flask import current_app

            if current_app.testing:
                return fn(*a, **kw)
            return _err("OVERSEER_API_TOKEN is not configured", 503)
        if request.headers.get("X-Overseer-Token") != token:
            return _err("invalid or missing X-Overseer-Token", 401)
        return fn(*a, **kw)

    return inner


@overseer_bp.get("/roster")
def roster():
    from src.overseers.actions import AUTO_SAFE, HANDLERS
    from src.overseers.chief import default_roster

    return jsonify(
        {
            "success": True,
            "overseers": [o.describe() for o in default_roster()],
            "action_kinds": sorted(HANDLERS),
            "auto_safe": sorted(AUTO_SAFE),
        }
    )


@overseer_bp.get("/status")
def status():
    last = OverseerRun.query.order_by(OverseerRun.id.desc()).first()
    open_rows = OverseerFinding.query.filter_by(status="open").all()
    by_sev = {}
    for r in open_rows:
        by_sev[r.severity] = by_sev.get(r.severity, 0) + 1
    return jsonify(
        {
            "success": True,
            "last_run": last.to_dict() if last else None,
            "open_findings": len(open_rows),
            "open_by_severity": by_sev,
            "pipeline_paused": OverseerControl.get("pipeline_paused", {"paused": False}),
        }
    )


@overseer_bp.post("/run")
@_guarded
def run():
    from src.overseers.chief import run_cycle

    body = request.get_json(silent=True) or {}
    result = run_cycle(trigger=body.get("trigger", "api"), auto_apply=body.get("auto_apply"))
    return jsonify({"success": True, "run": result})


@overseer_bp.get("/runs")
def runs():
    limit = min(int(request.args.get("limit", 20)), 100)
    rows = OverseerRun.query.order_by(OverseerRun.id.desc()).limit(limit).all()
    return jsonify({"success": True, "runs": [r.to_dict() for r in rows]})


@overseer_bp.get("/findings")
def findings():
    q = OverseerFinding.query
    for field in ("status", "overseer", "severity", "category", "code"):
        v = request.args.get(field, "open" if field == "status" else None)
        if v and v != "all":
            q = q.filter(getattr(OverseerFinding, field) == v)
    rows = q.order_by(OverseerFinding.last_seen_at.desc()).limit(min(int(request.args.get("limit", 100)), 500)).all()
    return jsonify({"success": True, "findings": [r.to_dict() for r in rows]})


@overseer_bp.get("/findings/<int:fid>")
def finding(fid):
    row = db.session.get(OverseerFinding, fid)
    if row is None:
        return _err("not found", 404)
    return jsonify({"success": True, "finding": row.to_dict()})


@overseer_bp.post("/findings/<int:fid>/dismiss")
@_guarded
def dismiss(fid):
    row = db.session.get(OverseerFinding, fid)
    if row is None:
        return _err("not found", 404)
    body = request.get_json(silent=True) or {}
    row.status = "dismissed"
    row.resolved_at = datetime.utcnow()
    row.detail = (row.detail or "") + f"\n[dismissed] {body.get('reason', '')}"
    db.session.commit()
    return jsonify({"success": True, "finding": row.to_dict()})


@overseer_bp.post("/actions/<int:aid>/approve")
@_guarded
def approve(aid):
    from src.overseers.actions import apply_action

    act = db.session.get(OverseerAction, aid)
    if act is None:
        return _err("not found", 404)
    if act.status != "proposed":
        return _err("action cannot be approved", 409)
    body = request.get_json(silent=True) or {}
    act.status = "approved"
    act.decided_by = body.get("by", "human")
    act.decided_at = datetime.utcnow()
    db.session.commit()
    if body.get("apply", True):
        act = apply_action(act, by=act.decided_by)
    return jsonify({"success": act.status in ("approved", "applied"), "action": act.to_dict()})


@overseer_bp.post("/actions/<int:aid>/reject")
@_guarded
def reject(aid):
    act = db.session.get(OverseerAction, aid)
    if act is None:
        return _err("not found", 404)
    if act.status not in ("proposed", "approved"):
        return _err("action cannot be rejected", 409)
    body = request.get_json(silent=True) or {}
    act.status = "rejected"
    act.decided_by = body.get("by", "human")
    act.decided_at = datetime.utcnow()
    act.result_json = json.dumps({"reason": body.get("reason", "")})
    db.session.commit()
    return jsonify({"success": True, "action": act.to_dict()})


@overseer_bp.post("/actions/<int:aid>/apply")
@_guarded
def apply(aid):
    from src.overseers.actions import ActionError, apply_action

    act = db.session.get(OverseerAction, aid)
    if act is None:
        return _err("not found", 404)
    try:
        act = apply_action(act, by="human")
    except ActionError as e:
        log.warning("Action %s could not be applied: %s", aid, e)
        return _err("action cannot be applied", 409)
    return jsonify({"success": act.status == "applied", "action": act.to_dict()})


@overseer_bp.get("/engineering-queue")
def engineering_queue():
    """Approved engineering tickets, in a shape a coding agent can act on."""
    rows = (
        OverseerAction.query.join(OverseerFinding)
        .filter(OverseerAction.kind == "engineering_ticket")
        .filter(OverseerAction.status.in_(("approved", "applied")))
        .filter(OverseerFinding.status == "open")
        .all()
    )
    items = [
        {
            "action_id": a.id,
            "finding_id": a.finding.id,
            "severity": a.finding.severity,
            "title": a.finding.title,
            "detail": a.finding.detail,
            "evidence": json.loads(a.finding.evidence_json) if a.finding.evidence_json else None,
            "params": a.params,
        }
        for a in rows
    ]
    if request.args.get("format") == "md":
        md = ["# Overseer engineering queue", ""]
        for i in items:
            md += [f"## [{i['severity']}] {i['title']}", "", i["detail"] or "", "", f"```json\n{json.dumps(i['evidence'] or i['params'], indent=2)}\n```", ""]
        return "\n".join(md), 200, {"Content-Type": "text/markdown; charset=utf-8"}
    return jsonify({"success": True, "items": items})


@overseer_bp.post("/controls/pipeline/resume")
@_guarded
def resume_pipeline():
    body = request.get_json(silent=True) or {}
    OverseerControl.set("pipeline_paused", {"paused": False, "reason": body.get("reason", "resumed by human")}, by=body.get("by", "human"))
    db.session.commit()
    return jsonify({"success": True, "pipeline_paused": OverseerControl.get("pipeline_paused")})


@overseer_bp.get("/author-model")
def author_model():
    from src.overseers import author_model_gate

    return jsonify({"success": True, "author_model": author_model_gate.status()})


@overseer_bp.post("/controls/author-model/revert")
@_guarded
def author_model_revert():
    from src.overseers import author_model_gate

    body = request.get_json(silent=True) or {}
    state = author_model_gate.revert(by=body.get("by", "human"), reason=body.get("reason", "reverted by human"))
    return jsonify({"success": True, "author_model": state})


@overseer_bp.post("/controls/author-model/rearm")
@_guarded
def author_model_rearm():
    from src.overseers import author_model_gate

    body = request.get_json(silent=True) or {}
    return jsonify({"success": True, "author_model": author_model_gate.rearm(by=body.get("by", "human"))})


@overseer_bp.post("/revenue/associates-csv")
@_guarded
def associates_csv():
    from src.services.analytics.associates_csv import import_associates_csv

    raw = request.files["file"].read().decode("utf-8-sig") if "file" in request.files else request.get_data(as_text=True)
    if not raw.strip():
        return _err("empty body; POST the CSV text or a multipart 'file'", 400)
    d = request.args.get("date")
    try:
        for_date = date.fromisoformat(d) if d else date.today()
        result = import_associates_csv(raw, for_date=for_date)
    except ValueError as e:
        log.warning("Associates CSV import rejected: %s", e)
        return _err("invalid Associates CSV request", 400)
    return jsonify({"success": True, **result})


__all__ = ["overseer_bp"]
