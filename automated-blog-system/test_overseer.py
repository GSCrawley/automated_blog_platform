"""Acceptance tests for PR #21 — overseer layer.

Coverage:
 1. Roster exposes the chief + six function overseers and the auto-safe set.
 2. Empty system -> 'no_live_articles' critical finding; notify auto-applies.
 3. Stuck article -> auto mark_article_error -> next cycle: stuck finding
    resolves (action verified) and an approval-gated article_failed opens.
 4. retry_article needs approval, calls the flow runner, enforces budget=2.
 5. Findings dedupe across cycles (occurrences increments).
 6. Budget burn projection auto-pauses new flows; CostMeter refuses; human
    resume clears it.
 7. Compliance: missing Amazon disclosure, publish-gate bypass.
 8. Revenue: tracking-ID collision is an engineering finding.
 9. Associates CSV import writes affiliate analytics rows.
10. Startup blueprint failures surface as critical findings.
11. Approval-gated actions cannot auto-apply; engineering queue lists approved tickets.
12. OVERSEER_API_TOKEN guards mutating endpoints.
"""
from __future__ import annotations

import os
import json
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))

os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault("GHOST_ADMIN_KEY", "0123456789abcdef01234567:" + "a" * 64)

from src.main import _schedule_overseer_job, create_app  # noqa: E402
from src.models.analytics import ArticleAnalyticsDaily  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.observability import Budget  # noqa: E402
from src.models.overseer import OverseerAction, OverseerControl, OverseerDispatch, OverseerFinding, OverseerRun  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.observability import CostEvent  # noqa: E402
from src.models.user import db  # noqa: E402
from src.overseers import actions as actions_mod  # noqa: E402
from src.overseers.chief import ChiefOverseer, run_cycle  # noqa: E402
from src.overseers.base import BaseOverseer, Finding  # noqa: E402
from src.overseers.audience import AudienceOverseer  # noqa: E402
from src.overseers.compliance import ComplianceOverseer  # noqa: E402
from src.overseers.revenue import RevenueOverseer  # noqa: E402
from src.overseers.systems import SystemsOverseer  # noqa: E402


@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def niche(app):
    n = Niche(name="Home Office Overseer Test", description="t")
    db.session.add(n)
    db.session.commit()
    return n


def _product(niche, **kw):
    p = Product(
        name=kw.pop("name", "Standing Desk Pro"),
        price=kw.pop("price", 899.0),
        niche_id=niche.id,
        tracking_id=kw.pop("tracking_id", "deskcred-20"),
        affiliate_url=kw.pop("affiliate_url", "https://www.amazon.com/dp/B000TEST?tag=deskcred-20"),
        **kw,
    )
    db.session.add(p)
    db.session.commit()
    return p


def _article(product, **kw):
    a = Article(
        title=kw.pop("title", "Best Standing Desks 2026"),
        content=kw.pop("content", "<p>" + "word " * 1500 + "</p>"),
        product_id=product.id,
        niche_id=product.niche_id,
        **kw,
    )
    db.session.add(a)
    db.session.commit()
    return a


def _open(code):
    return OverseerFinding.query.filter_by(code=code, status="open").all()


def test_audience_distribution_needs_completed_action_and_partial_config(app, niche, monkeypatch):
    monkeypatch.delenv("META_PAGE_ID", raising=False)
    monkeypatch.delenv("META_PAGE_ACCESS_TOKEN", raising=False)
    article = _article(_product(niche), status="published", published_url="https://deskcred.blog/post")
    overseer = AudienceOverseer()

    assert not any(f.code == "distribution_unconfigured" for f in overseer.sense())

    monkeypatch.setenv("META_PAGE_ID", "page-1")
    findings = overseer.sense()
    assert any(f.code == "distribution_unconfigured" for f in findings)

    monkeypatch.setenv("META_PAGE_ACCESS_TOKEN", "page-token")
    finding = OverseerFinding(
        fingerprint="audience|distribution_test",
        overseer="audience",
        code="distribution_test",
        title="test",
    )
    db.session.add(finding)
    db.session.commit()
    action = OverseerAction(
        finding_id=finding.id,
        kind="distribute_to_facebook_page",
        risk="approval",
        params_json=json.dumps({"article_id": article.id}),
        status="proposed",
    )
    db.session.add(action)
    db.session.commit()

    assert any(f.code == "not_distributed" for f in overseer.sense())

    action.status = "approved"
    db.session.commit()
    assert any(f.code == "not_distributed" for f in overseer.sense())

    action.status = "applied"
    db.session.commit()
    assert not any(f.code == "not_distributed" for f in overseer.sense())


# 1 -------------------------------------------------------------------------
def test_roster(client):
    body = client.get("/api/overseer/roster").get_json()
    names = [o["name"] for o in body["overseers"]]
    assert names == ["chief", "systems", "content", "market", "revenue", "audience", "compliance"]
    functions = {o["function"] for o in body["overseers"]}
    for f in (
        "Programmatic Content Agency",
        "24/7 Lead Generation",
        "Automated E-commerce Research",
        "Custom Bot Development",
        "Affiliate Funnel Management",
    ):
        assert f in functions
    assert "unpublish_article" not in body["auto_safe"]
    assert "retry_article" not in body["auto_safe"]


# 2 -------------------------------------------------------------------------
def test_empty_system_flags_no_live_articles(app):
    summary = run_cycle(trigger="test")
    rows = _open("no_live_articles")
    assert len(rows) == 1 and rows[0].severity == "critical"
    assert rows[0].actions[0].status == "applied"  # notify_human is auto-safe
    assert summary["actions_auto_applied"] >= 1


# 3 -------------------------------------------------------------------------
def test_stuck_article_auto_marked_then_verified(app, niche):
    p = _product(niche)
    a = _article(p, current_stage="stage_1_strategy", stage_status="running",
                 last_transition_at=datetime.utcnow() - timedelta(hours=7))
    run_cycle(trigger="test")
    stuck = _open("stuck_article")
    assert len(stuck) == 1
    act = stuck[0].actions[0]
    assert act.kind == "mark_article_error" and act.status == "applied"
    assert db.session.get(Article, a.id).stage_status == "error"
    assert act.undo["stage_status"] == "running"

    run_cycle(trigger="test")
    resolved = OverseerFinding.query.filter_by(code="stuck_article").first()
    assert resolved.status == "resolved"
    assert resolved.actions[0].status == "verified"
    failed = _open("article_failed")
    assert len(failed) == 1
    assert {x.kind: x.risk for x in failed[0].actions} == {"retry_article": "approval", "archive_article": "approval"}
    assert all(x.status == "proposed" for x in failed[0].actions)


# 4 -------------------------------------------------------------------------
def test_retry_requires_approval_and_respects_budget(app, client, niche, monkeypatch):
    calls = []
    monkeypatch.setattr(actions_mod, "FLOW_RUNNER", lambda aid: calls.append(aid))
    p = _product(niche)
    a = _article(p, current_stage="stage_2_creation", stage_status="error", last_error="boom")
    run_cycle(trigger="test")
    retry = next(x for x in _open("article_failed")[0].actions if x.kind == "retry_article")

    with pytest.raises(actions_mod.ActionError):
        actions_mod.apply_action(retry)  # proposed + approval-risk => refused

    r = client.post(f"/api/overseer/actions/{retry.id}/approve", json={"by": "gideon"})
    assert r.get_json()["action"]["status"] == "applied"
    assert calls == [a.id]
    assert OverseerControl.get(f"retries:{a.id}") == 1

    OverseerControl.set(f"retries:{a.id}", 2)
    db.session.commit()
    act = OverseerAction(finding_id=retry.finding_id, kind="retry_article", risk="approval",
                         params_json=retry.params_json, status="approved")
    db.session.add(act)
    db.session.commit()
    failed = actions_mod.apply_action(act)
    assert failed.status == "failed"
    assert failed.to_dict()["result"] == {"error": "action failed"}
    assert calls == [a.id]


def test_retry_dispatch_failure_is_queued_without_reusing_budget(app, niche, monkeypatch):
    p = _product(niche)
    a = _article(p, current_stage="stage_2_creation", stage_status="error", last_error="boom")
    run_cycle(trigger="test")
    retry = next(x for x in _open("article_failed")[0].actions if x.kind == "retry_article")
    retry.status = "approved"
    db.session.commit()

    attempts = []

    def flaky_runner(article_id):
        attempts.append(article_id)
        if len(attempts) == 1:
            raise RuntimeError("thread startup failed")

    monkeypatch.setattr(actions_mod, "FLOW_RUNNER", flaky_runner)
    assert actions_mod.apply_action(retry).status == "applied"
    dispatch = OverseerDispatch.query.one()
    assert dispatch.status == "pending" and dispatch.attempts == 1
    assert OverseerControl.get(f"retries:{a.id}") == 1

    actions_mod.dispatch_pending_retries()
    assert dispatch.status == "dispatched" and dispatch.attempts == 2
    assert attempts == [a.id, a.id]
    assert OverseerControl.get(f"retries:{a.id}") == 1


# 5 -------------------------------------------------------------------------
def test_findings_dedupe(app):
    run_cycle(trigger="test")
    run_cycle(trigger="test")
    rows = OverseerFinding.query.filter_by(code="no_live_articles").all()
    assert len(rows) == 1 and rows[0].occurrences == 2


def test_open_finding_fingerprint_is_unique_and_resolved_findings_can_repeat(app):
    finding = OverseerFinding(
        fingerprint="systems|duplicate:test",
        overseer="systems",
        code="duplicate",
        title="Duplicate finding",
    )
    run = OverseerRun(trigger="test")
    db.session.add(run)
    db.session.flush()
    finding.first_run_id = run.id
    db.session.add(finding)
    db.session.commit()

    from sqlalchemy.exc import IntegrityError

    db.session.add(
        OverseerFinding(
            fingerprint=finding.fingerprint,
            overseer="systems",
            code="duplicate",
            title="Duplicate finding",
        )
    )
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()

    finding.status = "resolved"
    db.session.commit()
    db.session.add(
        OverseerFinding(
            fingerprint=finding.fingerprint,
            overseer="systems",
            code="duplicate",
            title="Reopened finding",
        )
    )
    db.session.commit()


def test_sensor_failure_preserves_run_and_prior_findings(app):
    class BrokenOverseer(BaseOverseer):
        name = "broken"

        def sense(self):
            db.session.add(
                OverseerFinding(
                    fingerprint="broken|partial",
                    overseer="broken",
                    code="partial",
                    title="Must roll back",
                )
            )
            raise RuntimeError("sensor failure")

    class HealthyOverseer(BaseOverseer):
        name = "healthy"

        def sense(self):
            return [Finding(code="survived", title="Still recorded")]

    result = run_cycle(trigger="test", auto_apply=False, overseers=[BrokenOverseer(), HealthyOverseer()])
    run = db.session.get(OverseerRun, result["id"])
    assert run is not None
    assert OverseerFinding.query.filter_by(code="partial").count() == 0
    assert OverseerFinding.query.filter_by(code="survived", status="open").count() == 1


# 6 -------------------------------------------------------------------------
def test_budget_projection_pauses_and_human_resumes(app, client):
    from src.services.cost_meter import BudgetExceeded, CostMeter

    now = datetime(2026, 10, 10, 12, 0)
    db.session.add(Budget(month="2026-10", cap_usd=Decimal("100"), spent_usd=Decimal("50")))
    db.session.commit()
    run_cycle(trigger="test", now=now, overseers=[ChiefOverseer(now)])
    f = _open("budget_burn_projection")
    assert len(f) == 1
    kinds = {x.kind: x.status for x in f[0].actions}
    assert kinds == {"pause_pipeline": "applied", "resume_pipeline": "proposed"}
    with pytest.raises(BudgetExceeded):
        CostMeter.assert_can_start_flow()

    client.post("/api/overseer/controls/pipeline/resume", json={"by": "gideon"})
    assert OverseerControl.get("pipeline_paused")["paused"] is False


# 7 -------------------------------------------------------------------------
def test_compliance_disclosure_and_publish_gate(app, niche):
    p = _product(niche)
    _article(p, status="published", editorial_verdict="PUBLISH",
             content='<p>Buy <a href="https://www.amazon.com/dp/X?tag=deskcred-20">here</a></p>')
    _article(p, title="Bypassed", status="published", editorial_verdict="REJECT",
             content="<p>As an Amazon Associate I earn from qualifying purchases. (paid link) amazon.com</p>")
    codes = [f.code for f in ComplianceOverseer().sense()]
    assert codes.count("missing_amazon_disclosure") == 1
    assert "missing_link_disclosure" in codes
    assert codes.count("publish_gate_bypassed") == 1


def test_link_disclosure_is_checked_per_amazon_link_block(app, niche):
    p = _product(niche)
    _article(
        p,
        status="published",
        editorial_verdict="PUBLISH",
        content=(
            '<p>Buy <a href="https://amazon.com/dp/ONE">one</a> (affiliate link)</p>'
            '<p>Buy <a href="https://amazon.com/dp/TWO">two</a></p>'
            "<footer>This is an affiliate website.</footer>"
        ),
    )
    findings = [f for f in ComplianceOverseer().sense() if f.code == "missing_link_disclosure"]
    assert len(findings) == 1


def test_link_disclosure_in_each_amazon_link_block_passes(app, niche):
    p = _product(niche)
    _article(
        p,
        status="published",
        editorial_verdict="PUBLISH",
        content=(
            '<p><a href="https://amazon.com/dp/ONE">one</a> (affiliate link)</p>'
            '<p><a href="https://amazon.com/dp/TWO">two</a> (paid link)</p>'
        ),
    )
    findings = [f for f in ComplianceOverseer().sense() if f.code == "missing_link_disclosure"]
    assert findings == []


def test_footer_disclosure_does_not_cover_link_in_shared_container(app, niche):
    p = _product(niche)
    _article(
        p,
        status="published",
        editorial_verdict="PUBLISH",
        content=(
            '<div><a href="https://amazon.com/dp/ONE">Buy one</a>'
            "<footer>This is an affiliate website.</footer></div>"
        ),
    )
    findings = [f for f in ComplianceOverseer().sense() if f.code == "missing_link_disclosure"]
    assert len(findings) == 1


def test_is_amazon_url():
    from src.overseers.compliance import is_amazon_url

    assert is_amazon_url("https://www.amazon.com/dp/X")
    assert is_amazon_url("https://amazon.co.uk/x")
    assert is_amazon_url("https://amzn.to/abc")
    assert not is_amazon_url("https://deskcred.blog/best-standing-desks")
    assert not is_amazon_url("https://myamazonfinds.com/x")


# 8 -------------------------------------------------------------------------
def test_tracking_id_collision(app, niche):
    p1 = _product(niche, name="Desk A")
    p2 = _product(niche, name="Desk B")
    _article(p1, status="published", editorial_verdict="PUBLISH")
    _article(p2, title="Other", status="published", editorial_verdict="PUBLISH")
    f = [x for x in RevenueOverseer().sense() if x.code == "tracking_id_collision"]
    assert len(f) == 1 and f[0].category == "engineering"
    assert len(f[0].evidence["article_ids"]) == 2


# 9 -------------------------------------------------------------------------
def test_associates_csv_import(app, client, niche):
    p = _product(niche, tracking_id="deskcred-desk-20")
    a = _article(p, status="published", editorial_verdict="PUBLISH")
    csv_text = (
        "Fee-Tracking Report for deskcred-20 from 2026-10-01 to 2026-10-07\n"
        "Tracking ID,Clicks,Items Ordered,Items Shipped,Revenue,Ad Fees\n"
        'deskcred-desk-20,120,3,2,"$1,799.98",$54.00\n'
        "unknown-20,5,0,0,$0.00,$0.00\n"
    )
    r = client.post("/api/overseer/revenue/associates-csv?date=2026-10-07", data=csv_text,
                    content_type="text/csv")
    body = r.get_json()
    assert body["success"] and body["written"] == 1
    assert body["unmatched_tracking_ids"] == ["unknown-20"]
    row = ArticleAnalyticsDaily.query.filter_by(article_id=a.id, source="affiliate").one()
    assert row.clicks == 120 and row.conversions == 2 and Decimal(row.revenue_usd) == Decimal("54.00")
    assert row.date == date(2026, 10, 7)


# 10 ------------------------------------------------------------------------
def test_blueprint_failure_surfaces(app):
    app.extensions["blueprint_errors"] = {"blog": "ModuleNotFoundError: No module named 'google'"}
    f = [x for x in SystemsOverseer().sense() if x.code == "route_group_failed_to_load"]
    assert len(f) == 1 and f[0].severity == "critical"


def test_systems_flags_legacy_affiliate_endpoint_and_redundancies(app, tmp_path, monkeypatch):
    import src.overseers.systems as systems_mod

    codes = {x.code for x in SystemsOverseer().sense()}
    assert "affiliate_ingest_endpoint_invalid" in codes
    assert "redundant_paths" not in codes  # cleanup PR removed all superseded paths

    (tmp_path / "dump.rdb").write_bytes(b"")
    (tmp_path / "memory-bank").mkdir()
    monkeypatch.setattr(systems_mod, "_repo_root", lambda: tmp_path)
    found = [x for x in SystemsOverseer().sense() if x.code == "redundant_paths"]
    assert len(found) == 1
    assert sorted(found[0].evidence["paths"]) == ["dump.rdb", "memory-bank"]


def test_unmetered_spend_requires_crewai_generation_marker(app, niche):
    p = _product(niche)
    a = _article(p, draft_sections_json='{"draft":"written"}')
    db.session.add(CostEvent(article_id=a.id, stage="retrieval", model="embedding", cost_usd=0))
    db.session.commit()
    systems = SystemsOverseer()
    assert "llm_spend_unmetered" in {f.code for f in systems.sense()}

    db.session.add(
        CostEvent(article_id=a.id, stage="crewai_generation", model="gpt-4o", cost_usd=0)
    )
    db.session.commit()
    assert "llm_spend_unmetered" not in {f.code for f in systems.sense()}


# 11 ------------------------------------------------------------------------
def test_overseer_cannot_self_promote_risk(app):
    from src.overseers.actions import effective_risk

    assert effective_risk("archive_article", "auto") == "approval"
    assert effective_risk("unpublish_article", "auto") == "approval"
    assert effective_risk("notify_human", "auto") == "auto"


def test_engineering_queue(app, client):
    app.extensions["blueprint_errors"] = {"blog": "ModuleNotFoundError: google"}
    run_cycle(trigger="test")
    f = _open("route_group_failed_to_load")[0]
    ticket = f.actions[0]
    assert ticket.kind == "engineering_ticket" and ticket.status == "proposed"
    assert client.get("/api/overseer/engineering-queue").get_json()["items"] == []
    client.post(f"/api/overseer/actions/{ticket.id}/approve", json={"by": "gideon"})
    items = client.get("/api/overseer/engineering-queue").get_json()["items"]
    assert [i["finding_id"] for i in items] == [f.id]
    md = client.get("/api/overseer/engineering-queue?format=md").get_data(as_text=True)
    assert "route group 'blog'" in md


# 12 ------------------------------------------------------------------------
def test_token_guard(client, monkeypatch):
    monkeypatch.setenv("OVERSEER_API_TOKEN", "s3cret")
    assert client.post("/api/overseer/run", json={}).status_code == 401
    r = client.post("/api/overseer/run", json={"trigger": "grok_routine"}, headers={"X-Overseer-Token": "s3cret"})
    assert r.status_code == 200 and r.get_json()["run"]["trigger"] == "grok_routine"


def test_mutating_routes_fail_closed_when_token_is_unconfigured(client, app, monkeypatch):
    monkeypatch.delenv("OVERSEER_API_TOKEN", raising=False)
    app.config["TESTING"] = False
    response = client.post("/api/overseer/run", json={})
    assert response.status_code == 503


def test_invalid_overseer_interval_does_not_break_other_scheduled_jobs(monkeypatch):
    class Scheduler:
        def __init__(self):
            self.jobs = []

        def add_job(self, *args, **kwargs):
            self.jobs.append((args, kwargs))

    scheduler = Scheduler()
    scheduler.add_job(lambda: None, trigger="cron", id="daily_analytics_ingest")
    monkeypatch.setenv("OVERSEER_INTERVAL_MINUTES", "not-a-number")
    _schedule_overseer_job(scheduler, lambda: None)
    assert [job[1]["id"] for job in scheduler.jobs] == ["daily_analytics_ingest"]
