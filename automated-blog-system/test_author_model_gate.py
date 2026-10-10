"""Author-model gate: Muse Spark for the author agent only after verification.

Coverage:
 1. Fresh system: gate stays on the default; every unmet check is reported.
 2. Fully verified system switches only after the stability window.
 3. A failing check resets the stability window.
 4. Open high/critical findings and crashed overseers block the switch.
 5. The switch is sticky; revert locks the gate; rearm clears the lock.
 6. AUTHOR_LLM_PROVIDER=default never switches; =meta forces it.
 7. Crew wiring: the author agent gets Muse Spark after the switch and the
    monetization specialist keeps the default.
 8. Systems overseer requires META_MODEL_API_KEY only after the switch.
 9. Revert/rearm endpoints are token-guarded; status endpoint lists checks.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))

os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault("GHOST_ADMIN_KEY", "0123456789abcdef01234567:" + "a" * 64)

from src.main import create_app  # noqa: E402
from src.models.analytics import ArticleAnalyticsDaily  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.observability import CostEvent  # noqa: E402
from src.models.overseer import OverseerAction, OverseerControl, OverseerFinding  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402
from src.overseers import author_model_gate as gate  # noqa: E402
from src.overseers.base import BaseOverseer, Finding  # noqa: E402
from src.overseers.chief import run_cycle  # noqa: E402
from src.overseers.systems import SystemsOverseer  # noqa: E402

T0 = datetime(2026, 11, 2, 12, 0, 0)


class _Quiet(BaseOverseer):
    name = "quiet"

    def sense(self):
        return []


class _Crashes(BaseOverseer):
    name = "crashes"

    def sense(self):
        raise RuntimeError("boom")


class _RaisesHigh(BaseOverseer):
    name = "systems"

    def sense(self):
        return [Finding(code="llm_spend_unmetered", title="unmetered", severity="high", subject_id="cost_meter")]


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.delenv("AUTHOR_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("CONTENT_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("META_MODEL_API_KEY", raising=False)
    monkeypatch.delenv("OVERSEER_API_TOKEN", raising=False)
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app


def _verified_system(monkeypatch):
    monkeypatch.setenv("META_MODEL_API_KEY", "test-key")
    niche = Niche(name="Gate test niche", description="t")
    db.session.add(niche)
    db.session.commit()
    product = Product(name="Standing Desk", price=899.0, niche_id=niche.id, tracking_id="deskcred-a1-20")
    db.session.add(product)
    db.session.commit()
    article = Article(
        title="Best Standing Desks",
        content="<p>x</p>",
        product_id=product.id,
        niche_id=niche.id,
        status="published",
        published_url="https://blog.test/best-standing-desks/",
    )
    db.session.add(article)
    db.session.commit()
    finding = OverseerFinding(
        fingerprint="audience|not_distributed:article:1", overseer="audience", code="not_distributed",
        severity="low", title="share", status="resolved",
    )
    db.session.add(finding)
    db.session.flush()
    db.session.add(
        OverseerAction(finding_id=finding.id, kind="distribute_to_facebook_page", status="verified",
                       params_json='{"article_id": %d}' % article.id)
    )
    db.session.add(ArticleAnalyticsDaily(article_id=article.id, date=date(2026, 10, 30), source="gsc", impressions=40))
    db.session.add(ArticleAnalyticsDaily(article_id=article.id, date=date(2026, 10, 30), source="affiliate", clicks=3))
    db.session.add(CostEvent(article_id=article.id, stage="crewai_generation", model="gpt-4.1-mini", cost_usd=0))
    db.session.commit()
    return article


def _failing(result):
    return {c["check"] for c in result["checks"] if not c["ok"]}


# 1 -------------------------------------------------------------------------
def test_fresh_system_stays_on_default_and_lists_unmet_checks(app):
    result = gate.evaluate(T0)
    assert result["provider"] == "default" and not result["switched"]
    assert {
        "live_article_on_ghost",
        "distribution_fired",
        "search_impressions_recorded",
        "generation_spend_metered",
        "affiliate_earnings_ingested",
        "meta_api_key_configured",
    } <= _failing(result)
    assert gate.current_author_provider() == "default"


# 2 -------------------------------------------------------------------------
def test_verified_system_switches_after_stability_window(app, monkeypatch):
    _verified_system(monkeypatch)
    first = run_cycle(trigger="test", overseers=[_Quiet()], now=T0)
    assert first["summary"]["author_model"]["provider"] == "default"
    assert first["summary"]["author_model_checks_failing"] == []
    assert gate.current_author_provider() == "default"

    still = gate.evaluate(T0 + timedelta(hours=23))
    assert still["provider"] == "default"

    switched = run_cycle(trigger="test", overseers=[_Quiet()], now=T0 + timedelta(hours=24))
    assert switched["summary"]["author_model"]["switched"] is True
    assert gate.current_author_provider() == "meta"
    state = OverseerControl.get(gate.CONTROL_KEY)
    assert state["model"] == "muse-spark-1.3"
    assert state["passing_since"] == T0.isoformat()


# 3 -------------------------------------------------------------------------
def test_failing_check_resets_stability_window(app, monkeypatch):
    _verified_system(monkeypatch)
    gate.evaluate(T0)
    monkeypatch.delenv("META_MODEL_API_KEY")
    assert "meta_api_key_configured" in _failing(gate.evaluate(T0 + timedelta(hours=12)))
    monkeypatch.setenv("META_MODEL_API_KEY", "test-key")
    restarted = gate.evaluate(T0 + timedelta(hours=13))
    assert restarted["passing_since"] == (T0 + timedelta(hours=13)).isoformat()
    assert gate.evaluate(T0 + timedelta(hours=30))["provider"] == "default"
    assert gate.evaluate(T0 + timedelta(hours=37))["switched"] is True


# 4 -------------------------------------------------------------------------
def test_high_findings_and_crashed_overseers_block_the_switch(app, monkeypatch):
    _verified_system(monkeypatch)
    blocked = run_cycle(trigger="test", overseers=[_RaisesHigh()], now=T0)
    assert "no_open_critical_or_high_findings" in blocked["summary"]["author_model_checks_failing"]

    OverseerFinding.query.filter_by(code="llm_spend_unmetered").update({"status": "resolved"})
    db.session.commit()
    crashed = run_cycle(trigger="test", overseers=[_Crashes()], now=T0 + timedelta(hours=25))
    assert "overseers_healthy" in crashed["summary"]["author_model_checks_failing"]
    assert gate.current_author_provider() == "default"


# 5 -------------------------------------------------------------------------
def test_switch_is_sticky_and_revert_locks_until_rearm(app, monkeypatch):
    _verified_system(monkeypatch)
    gate.evaluate(T0)
    gate.evaluate(T0 + timedelta(hours=24))
    assert gate.current_author_provider() == "meta"

    monkeypatch.delenv("META_MODEL_API_KEY")  # a later fault does not silently flip models
    assert gate.evaluate(T0 + timedelta(hours=25))["provider"] == "meta"
    monkeypatch.setenv("META_MODEL_API_KEY", "test-key")

    gate.revert(by="gideon", reason="prose check")
    assert gate.current_author_provider() == "default"
    assert gate.evaluate(T0 + timedelta(hours=100))["locked"] is True
    assert gate.evaluate(T0 + timedelta(hours=200))["provider"] == "default"

    gate.rearm(by="gideon")
    gate.evaluate(T0 + timedelta(hours=300))
    assert gate.evaluate(T0 + timedelta(hours=324))["switched"] is True


# 6 -------------------------------------------------------------------------
def test_env_overrides(app, monkeypatch):
    _verified_system(monkeypatch)
    monkeypatch.setenv("AUTHOR_LLM_PROVIDER", "default")
    gate.evaluate(T0)
    gate.evaluate(T0 + timedelta(days=5))
    assert gate.current_author_provider() == "default"
    assert OverseerControl.get(gate.CONTROL_KEY) is None

    monkeypatch.setenv("AUTHOR_LLM_PROVIDER", "meta")
    assert gate.current_author_provider() == "meta"


# 7 -------------------------------------------------------------------------
def test_author_agent_only_moves_to_muse_spark_after_switch(app, monkeypatch):
    pytest.importorskip("crewai")
    from core.crewai_system.llm_providers import author_llm_kwargs, llm_kwargs

    _verified_system(monkeypatch)
    assert author_llm_kwargs() == {}
    gate.evaluate(T0)
    gate.evaluate(T0 + timedelta(hours=24))

    author = author_llm_kwargs()
    assert author["llm"].model.endswith("muse-spark-1.3")
    assert llm_kwargs() == {}  # monetization specialist keeps the default


def test_author_falls_back_to_default_without_app_context(monkeypatch):
    from core.crewai_system.llm_providers import author_llm_kwargs

    monkeypatch.delenv("AUTHOR_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("CONTENT_LLM_PROVIDER", raising=False)
    assert author_llm_kwargs() == {}


# 8 -------------------------------------------------------------------------
def test_meta_key_is_required_only_after_switch(app, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    keys = lambda: {f.subject_id for f in SystemsOverseer()._config() if f.severity == "critical"}  # noqa: E731
    assert "META_MODEL_API_KEY" not in keys()

    OverseerControl.set(gate.CONTROL_KEY, {"provider": "meta"})
    db.session.commit()
    assert "META_MODEL_API_KEY" in keys()
    assert "OPENAI_API_KEY" not in keys()


# 9 -------------------------------------------------------------------------
def test_author_model_endpoints(app, monkeypatch):
    client = app.test_client()
    r = client.get("/api/overseer/author-model")
    assert r.status_code == 200
    body = r.get_json()["author_model"]
    assert body["mode"] == "gated" and body["provider"] == "default"
    assert {c["check"] for c in body["checks"]} >= {"live_article_on_ghost", "meta_api_key_configured"}

    monkeypatch.setenv("OVERSEER_API_TOKEN", "s3cret")
    assert client.post("/api/overseer/controls/author-model/revert", json={}).status_code == 401
    r = client.post(
        "/api/overseer/controls/author-model/revert",
        json={"by": "gideon", "reason": "test"},
        headers={"X-Overseer-Token": "s3cret"},
    )
    assert r.status_code == 200 and r.get_json()["author_model"]["locked"] is True
    r = client.post("/api/overseer/controls/author-model/rearm", json={}, headers={"X-Overseer-Token": "s3cret"})
    assert r.status_code == 200
    assert OverseerControl.get(gate.CONTROL_KEY) is None
