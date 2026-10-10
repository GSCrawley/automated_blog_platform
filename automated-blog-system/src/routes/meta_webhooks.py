"""Authenticated webhook for Ghost newsletter member signups."""
from __future__ import annotations

import hashlib
import hmac
import os
import time

from flask import Blueprint, jsonify, request

from src.services.meta_ai import MetaGraphError, MetaMarketingClient

meta_webhook_bp = Blueprint("meta_webhooks", __name__)


def _valid_ghost_signature(secret: str, raw_body: bytes, header: str) -> bool:
    try:
        digest_part, timestamp_part = header.split(",", 1)
        algorithm, digest = digest_part.strip().split("=", 1)
        timestamp_key, timestamp = timestamp_part.strip().split("=", 1)
        timestamp_ms = int(timestamp)
    except (ValueError, TypeError):
        return False
    if algorithm != "sha256" or timestamp_key != "t":
        return False
    if abs(time.time() * 1000 - timestamp_ms) > 5 * 60 * 1000:
        return False
    expected = hmac.new(
        secret.encode(),
        raw_body + timestamp.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(digest, expected)


@meta_webhook_bp.route("/ghost/newsletter-signup", methods=["POST"])
def ghost_newsletter_signup():
    secret = os.getenv("GHOST_WEBHOOK_SECRET", "")
    if not secret:
        return jsonify({"error": "Newsletter conversion webhook is not configured"}), 503
    if not _valid_ghost_signature(
        secret,
        request.get_data(cache=True),
        request.headers.get("X-Ghost-Signature", ""),
    ):
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected a JSON object"}), 400
    member = payload.get("member", payload)
    if not isinstance(member, dict):
        return jsonify({"error": "Expected a member object"}), 400

    email = member.get("email")
    event_source_url = (
        payload.get("event_source_url")
        or member.get("event_source_url")
        or os.getenv("GHOST_API_URL", "").rstrip("/")
    )
    user_agent = request.headers.get("User-Agent", "")
    if not isinstance(email, str) or not email.strip():
        return jsonify({"error": "Member email is required"}), 400
    if not isinstance(event_source_url, str) or not event_source_url.strip():
        return jsonify({"error": "event_source_url or GHOST_API_URL is required"}), 400
    if not user_agent.strip():
        return jsonify({"error": "User-Agent is required"}), 400

    member_id = member.get("id")
    if member_id is not None:
        event_id = f"ghost-member-{member_id}"
    else:
        event_id = hashlib.sha256(email.strip().lower().encode()).hexdigest()

    try:
        MetaMarketingClient().send_conversion_event(
            "Lead",
            event_source_url=event_source_url,
            email=email,
            client_ip=request.remote_addr,
            user_agent=user_agent,
            event_id=event_id,
        )
    except MetaGraphError:
        return jsonify({"error": "Could not send newsletter conversion event"}), 502

    return jsonify({"status": "sent", "event_id": event_id}), 200


__all__ = ["meta_webhook_bp"]
