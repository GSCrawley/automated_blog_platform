"""Blueprint proposal lifecycle routes (PR #7).

Endpoints (all under ``/api/proposals``):

    GET  /                       List proposals (filterable by status, niche_id)
    GET  /<proposal_id>          Full proposal detail
    POST /<proposal_id>/accept   Accept → create new Blueprint version
    POST /<proposal_id>/reject   Reject → close without Blueprint change
    POST /generate/<niche_id>    On-demand: run feedback engine for a niche

On accept, a new Blueprint version is created via the PR #5a machinery
(``refresh_blueprint`` / ``persist_blueprint``), a background thread fans
out ``generate_improvement_proposals`` to all published articles in the
niche, and the proposal row is updated with the new Blueprint ID.
"""
from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from src.models.analytics import BlueprintProposal
from src.models.user import db

logger = logging.getLogger(__name__)
proposals_bp = Blueprint("proposals", __name__)


def _err(message: str, status: int):
    return jsonify({"success": False, "error": message}), status


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@proposals_bp.route("/", methods=["GET"])
def list_proposals():
    """List blueprint proposals.

    Query params: ``status`` (pending|accepted|rejected), ``niche_id``,
    ``limit`` (max 200), ``offset``.
    """
    q = BlueprintProposal.query

    status = request.args.get("status")
    if status:
        q = q.filter(BlueprintProposal.status == status.lower())

    niche_id = request.args.get("niche_id")
    if niche_id:
        try:
            q = q.filter(BlueprintProposal.niche_id == int(niche_id))
        except ValueError:
            return _err("niche_id must be an integer.", 400)

    q = q.order_by(BlueprintProposal.generated_at.desc())

    try:
        limit = max(1, min(200, int(request.args.get("limit", 50))))
        offset = max(0, int(request.args.get("offset", 0)))
    except (TypeError, ValueError):
        limit, offset = 50, 0

    total = q.count()
    rows = q.limit(limit).offset(offset).all()

    return jsonify(
        {
            "success": True,
            "proposals": [p.to_dict() for p in rows],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


@proposals_bp.route("/<int:proposal_id>", methods=["GET"])
def get_proposal(proposal_id: int):
    """Full proposal detail."""
    p = BlueprintProposal.query.get(proposal_id)
    if p is None:
        return _err(f"Proposal {proposal_id} not found.", 404)
    return jsonify({"success": True, "proposal": p.to_dict()})


@proposals_bp.route("/<int:proposal_id>/accept", methods=["POST"])
def accept_proposal(proposal_id: int):
    """Accept a proposal.

    Creates a new Blueprint version using the PR #5a machinery, marks the
    proposal ``status='accepted'``, and launches a background fan-out of
    ``generate_improvement_proposals`` for all published articles in the
    same niche.
    """
    proposal = BlueprintProposal.query.get(proposal_id)
    if proposal is None:
        return _err(f"Proposal {proposal_id} not found.", 404)
    if proposal.status != "pending":
        return _err(
            f"Proposal is already '{proposal.status}'; only pending proposals can be accepted.",
            409,
        )

    # Create a new Blueprint version.
    new_blueprint_id: str = ""
    try:
        from src.services.blueprint_repo import get_active_blueprint_row, persist_blueprint

        parent_row = get_active_blueprint_row(proposal.niche_id)
        if parent_row is None:
            return _err("No active blueprint found for this niche — cannot create a new version.", 400)

        # Build an updated Blueprint from the parent, applying the proposed value.
        blueprint = parent_row.to_blueprint()
        proposed = proposal.proposed_value()
        _apply_proposal_to_blueprint(blueprint, proposal.blueprint_field, proposed)

        # Assign a new unique ID so persist_blueprint doesn't hit a UNIQUE constraint.
        blueprint.id = f"bp_niche{proposal.niche_id}_{uuid.uuid4().hex[:8]}"

        new_row = persist_blueprint(
            blueprint,
            profile_aggregate=_safe_json(parent_row.profile_aggregate),
            confidence_tiers=_safe_json(parent_row.confidence_tiers),
            parent=parent_row,
        )
        new_blueprint_id = new_row.id
    except Exception:
        logger.exception("Failed to create new Blueprint version for proposal %d", proposal_id)
        return _err("Failed to create new Blueprint version; proposal not accepted.", 500)

    # Mark proposal accepted.
    proposal.status = "accepted"
    proposal.reviewed_at = datetime.utcnow()
    proposal.resulting_blueprint_id = new_blueprint_id
    db.session.commit()

    # Fan-out improvement proposals in background thread.
    niche_id = proposal.niche_id
    _launch_fanout(proposal_id=proposal_id, niche_id=niche_id)

    return jsonify(
        {
            "success": True,
            "proposal_id": proposal_id,
            "new_blueprint_id": new_blueprint_id,
            "status": "accepted",
        }
    )


@proposals_bp.route("/<int:proposal_id>/reject", methods=["POST"])
def reject_proposal(proposal_id: int):
    """Reject a proposal — marks it closed without changing the Blueprint."""
    proposal = BlueprintProposal.query.get(proposal_id)
    if proposal is None:
        return _err(f"Proposal {proposal_id} not found.", 404)
    if proposal.status != "pending":
        return _err(
            f"Proposal is already '{proposal.status}'; only pending proposals can be rejected.",
            409,
        )

    body = request.get_json(force=True, silent=True) or {}
    proposal.status = "rejected"
    proposal.reviewed_at = datetime.utcnow()
    proposal.reviewed_by = str(body.get("reviewed_by", ""))
    db.session.commit()

    return jsonify({"success": True, "proposal_id": proposal_id, "status": "rejected"})


@proposals_bp.route("/generate/<int:niche_id>", methods=["POST"])
def generate_proposals(niche_id: int):
    """On-demand: run the feedback engine for one niche and surface proposals.

    Returns immediately with counts; heavy work happens synchronously but
    is fast (pure Python, no network).
    """
    try:
        from src.services.feedback_engine import propose_blueprint_updates

        body = request.get_json(force=True, silent=True) or {}
        min_n = int(body.get("min_n", 3))
        proposals = propose_blueprint_updates(niche_id, min_n=min_n)
        return jsonify(
            {
                "success": True,
                "niche_id": niche_id,
                "proposals_created": len(proposals),
                "proposal_ids": [p.id for p in proposals],
            }
        )
    except Exception:
        logger.exception("generate_proposals failed for niche %d", niche_id)
        return _err("Failed to generate proposals.", 500)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_json(raw) -> dict:
    import json
    try:
        return json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}


def _apply_proposal_to_blueprint(blueprint, field: str, proposed_value) -> None:
    """Apply a proposed field value to an in-memory Blueprint dataclass.

    Only modifies fields that have a direct attribute on Blueprint; others
    are no-ops (the human's intent is captured in the proposal row, and the
    aggregator will bake it in on the next SERP refresh).
    """
    if proposed_value is None:
        return  # human needs to supply a concrete value; skip mutation
    if field == "word_count_range" and isinstance(proposed_value, (list, tuple)) and len(proposed_value) == 2:
        object.__setattr__(blueprint, "word_count_range", tuple(proposed_value))
    elif field == "h2_count_range" and isinstance(proposed_value, (list, tuple)) and len(proposed_value) == 2:
        object.__setattr__(blueprint, "h2_count_range", tuple(proposed_value))
    elif field == "min_internal_links" and isinstance(proposed_value, int):
        object.__setattr__(blueprint, "min_internal_links", proposed_value)
    elif field == "requires_feature_image":
        object.__setattr__(blueprint, "requires_feature_image", bool(proposed_value))
    elif field == "requires_schema_markup":
        object.__setattr__(blueprint, "requires_schema_markup", bool(proposed_value))


def _launch_fanout(*, proposal_id: int, niche_id) -> None:
    """Spawn a background thread to fan out improvement proposals."""
    from flask import current_app
    app = current_app._get_current_object()  # capture reference for the thread

    def _run():
        with app.app_context():
            try:
                from src.services.feedback_engine import fanout_improvement_proposals
                fanout_improvement_proposals(proposal_id, niche_id)
            except Exception:
                logger.exception("fanout_improvement_proposals failed for proposal %d", proposal_id)

    t = threading.Thread(target=_run, name=f"fanout-proposal-{proposal_id}", daemon=True)
    t.start()


__all__ = ["proposals_bp"]
