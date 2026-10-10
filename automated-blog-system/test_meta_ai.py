"""Acceptance tests for PR #22 — Meta AI integration.

 1. Muse Spark chat hits /chat/completions with a bearer token and records a
    CostEvent at the rate-card price.
 2. Contributor tier (prompts used by Meta) is refused without opt-in.
 3. Muse Image records a flat $0.01 cost event and flags ai_generated.
 4. Campaign drafts are always created PAUSED, on the configured Graph version.
 5. Code can only pause/archive a campaign, never activate.
 6. Conversions API event hashes email and posts to /<pixel>/events.
 7. create_meta_campaign_draft refuses Amazon destinations; compliance
    overseer auto-rejects a proposed draft that points at Amazon.
"""
from __future__ import annotations

import json
import hashlib
import hmac
import os
import sys
import time
from types import SimpleNamespace
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs

import pytest
import responses as resp_lib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))
os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault("GHOST_ADMIN_KEY", "0123456789abcdef01234567:" + "a" * 64)

from src.main import create_app  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.observability import CostEvent  # noqa: E402
from src.models.overseer import OverseerAction, OverseerFinding  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402
from src.services.meta_ai import MetaGraphError, MetaMarketingClient, MetaModelClient, MetaModelError  # noqa: E402
from core.crewai_system.llm_providers import get_content_llm, track_content_generation  # noqa: E402


@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture()
def meta_env(monkeypatch):
    monkeypatch.setenv("META_MODEL_API_KEY", "mk_test")
    monkeypatch.setenv("META_AD_ACCOUNT_ID", "act_123")
    monkeypatch.setenv("META_SYSTEM_USER_TOKEN", "sys_tok")
    monkeypatch.setenv("META_PIXEL_ID", "999")
    monkeypatch.setenv("META_GRAPH_API_VERSION", "v26.0")
    monkeypatch.delenv("META_ALLOW_CONTRIBUTOR_TIER", raising=False)


def _form(call):
    return {k: v[0] for k, v in parse_qs(call.request.body).items()}


@resp_lib.activate
def test_chat_metered(app, meta_env):
    resp_lib.add(
        resp_lib.POST,
        "https://api.meta.ai/v1/chat/completions",
        json={"choices": [{"message": {"content": "Hello desk"}}], "usage": {"prompt_tokens": 1000, "completion_tokens": 2000}},
    )
    r = MetaModelClient().chat([{"role": "user", "content": "hi"}], stage="meta_content")
    assert r.text == "Hello desk"
    # 1000 * 0.00125/1k + 2000 * 0.00425/1k = 0.00125 + 0.0085
    assert r.cost_usd == Decimal("0.009750")
    req = resp_lib.calls[0].request
    assert req.headers["Authorization"] == "Bearer mk_test"
    assert json.loads(req.body)["model"] == "muse-spark-1.3"
    ev = CostEvent.query.one()
    assert ev.model == "muse-spark-1.3" and ev.stage == "meta_content"


def test_contributor_tier_requires_opt_in(app, meta_env, monkeypatch):
    with pytest.raises(MetaModelError):
        MetaModelClient(text_model="muse-spark-1.3-contributor")
    with pytest.raises(MetaModelError):
        MetaModelClient().chat(
            [{"role": "user", "content": "private prompt"}],
            model="muse-spark-1.3-contributor",
        )
    monkeypatch.setenv("META_ALLOW_CONTRIBUTOR_TIER", "true")
    assert MetaModelClient(text_model="muse-spark-1.3-contributor").text_model.endswith("contributor")


@resp_lib.activate
def test_image_flat_cost(app, meta_env):
    resp_lib.add(resp_lib.POST, "https://api.meta.ai/v1/images/generations", json={"data": [{"url": "https://img/x.png"}]})
    body = MetaModelClient().generate_image("a walnut standing desk in a sunlit office")
    assert body["ai_generated"] is True
    ev = CostEvent.query.one()
    assert ev.model == "muse-image-1.0" and Decimal(ev.cost_usd) == Decimal("0.01")


@resp_lib.activate
def test_campaign_draft_always_paused(app, meta_env):
    resp_lib.add(resp_lib.POST, "https://graph.facebook.com/v26.0/act_123/campaigns", json={"id": "cmp_1"})
    out = MetaMarketingClient().create_campaign_draft("Best Standing Desks")
    assert out["id"] == "cmp_1"
    form = _form(resp_lib.calls[0])
    assert form["status"] == "PAUSED" and form["objective"] == "OUTCOME_TRAFFIC"
    assert form["special_ad_categories"] == "[]"
    with pytest.raises(MetaGraphError):
        MetaMarketingClient().create_campaign_draft("x", objective="OUTCOME_SALES_ACTIVE")


def test_code_cannot_activate(app, meta_env):
    with pytest.raises(MetaGraphError):
        MetaMarketingClient().set_campaign_status("cmp_1", "ACTIVE")


@resp_lib.activate
def test_conversion_event(app, meta_env):
    resp_lib.add(resp_lib.POST, "https://graph.facebook.com/v26.0/999/events", json={"events_received": 1})
    MetaMarketingClient().send_conversion_event(
        "Lead",
        event_source_url="https://deskcred.blog/newsletter",
        email=" Reader@Example.com ",
        user_agent="Mozilla/5.0",
        event_id="lead-1",
    )
    ev = json.loads(_form(resp_lib.calls[0])["data"])[0]
    assert ev["event_name"] == "Lead" and ev["action_source"] == "website" and ev["event_id"] == "lead-1"
    import hashlib

    assert ev["user_data"]["em"] == [hashlib.sha256(b"reader@example.com").hexdigest()]
    assert ev["user_data"]["client_user_agent"] == "Mozilla/5.0"


def test_conversion_event_requires_nonempty_user_agent(app, meta_env):
    with pytest.raises(MetaGraphError, match="client_user_agent is required"):
        MetaMarketingClient().send_conversion_event(
            "Lead", event_source_url="https://deskcred.blog/newsletter"
        )


def test_campaign_handler_refuses_amazon(app, meta_env):
    from src.overseers.actions import HANDLERS, ActionError

    with pytest.raises(ActionError):
        HANDLERS["create_meta_campaign_draft"]({"article_id": 1, "destination_url": "https://www.amazon.com/dp/X"})


def test_compliance_rejects_amazon_campaign(app, meta_env):
    from src.overseers.chief import run_cycle
    from src.overseers.compliance import ComplianceOverseer

    n = Niche(name="n")
    db.session.add(n)
    db.session.commit()
    p = Product(name="p", price=900, niche_id=n.id)
    db.session.add(p)
    db.session.commit()
    a = Article(title="t", content="c", product_id=p.id, niche_id=n.id)
    db.session.add(a)
    db.session.commit()
    f = OverseerFinding(fingerprint="revenue|amplify_winner:article:1", overseer="revenue", code="amplify_winner", title="x")
    db.session.add(f)
    db.session.commit()
    bad = OverseerAction(finding_id=f.id, kind="create_meta_campaign_draft", risk="approval",
                         params_json=json.dumps({"article_id": a.id, "destination_url": "https://amzn.to/abc"}))
    db.session.add(bad)
    db.session.commit()
    run_cycle(trigger="test", overseers=[ComplianceOverseer()])
    assert db.session.get(OverseerAction, bad.id).status == "rejected"


def test_meta_actions_are_never_auto(app):
    from src.overseers.actions import AUTO_SAFE, HANDLERS, effective_risk

    for kind in ("create_meta_campaign_draft", "distribute_to_facebook_page"):
        assert kind in HANDLERS and kind not in AUTO_SAFE
        assert effective_risk(kind, "auto") == "approval"


@resp_lib.activate
def test_ghost_newsletter_webhook_sends_lead_with_request_metadata(app, meta_env, monkeypatch):
    secret = "ghost-webhook-secret"
    monkeypatch.setenv("GHOST_WEBHOOK_SECRET", secret)
    resp_lib.add(
        resp_lib.POST,
        "https://graph.facebook.com/v26.0/999/events",
        json={"events_received": 1},
    )
    body = json.dumps(
        {
            "member": {"id": "member-42", "email": "Reader@Example.com"},
            "event_source_url": "https://deskcred.blog/newsletter",
        }
    )
    timestamp = str(int(time.time() * 1000))
    digest = hmac.new(
        secret.encode(), (body + timestamp).encode(), hashlib.sha256
    ).hexdigest()
    response = app.test_client().post(
        "/api/webhooks/ghost/newsletter-signup",
        data=body,
        content_type="application/json",
        headers={
            "X-Ghost-Signature": f"sha256={digest}, t={timestamp}",
            "User-Agent": "Ghost signup client",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["event_id"] == "ghost-member-member-42"
    event = json.loads(_form(resp_lib.calls[0])["data"])[0]
    assert event["event_name"] == "Lead"
    assert event["event_source_url"] == "https://deskcred.blog/newsletter"
    assert event["event_id"] == "ghost-member-member-42"
    assert event["user_data"]["client_user_agent"] == "Ghost signup client"


def test_ghost_newsletter_webhook_requires_configured_token(app, monkeypatch):
    monkeypatch.delenv("GHOST_WEBHOOK_SECRET", raising=False)
    response = app.test_client().post("/api/webhooks/ghost/newsletter-signup", json={})
    assert response.status_code == 503

    monkeypatch.setenv("GHOST_WEBHOOK_SECRET", "configured")
    response = app.test_client().post(
        "/api/webhooks/ghost/newsletter-signup",
        json={},
        headers={"X-Ghost-Signature": "sha256=incorrect, t=0"},
    )
    assert response.status_code == 401


def test_crewai_meta_calls_are_metered_for_current_article(app, meta_env, monkeypatch):
    monkeypatch.setenv("CONTENT_LLM_PROVIDER", "meta")
    niche = Niche(name="Metered content test")
    db.session.add(niche)
    db.session.commit()
    product = Product(name="Desk", price=500, niche_id=niche.id)
    db.session.add(product)
    db.session.commit()
    article = Article(title="Desk", content="", product_id=product.id, niche_id=niche.id)
    db.session.add(article)
    db.session.commit()

    with track_content_generation(article.id):
        llm = get_content_llm()
        llm.callbacks[0].log_success_event(
            kwargs={},
            response_obj=SimpleNamespace(
                usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50)
            ),
            start_time=0,
            end_time=0,
        )

    event = CostEvent.query.one()
    assert event.article_id == article.id
    assert event.stage == "crewai_generation"
    assert event.model == "muse-spark-1.3"
