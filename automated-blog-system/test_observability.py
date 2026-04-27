"""Acceptance tests for PR #3 — observability + cost metering + Alembic.

Five tests from ``PRs_2_through_7.md`` §3.6:

1. Alembic round-trip: ``flask db upgrade`` from empty produces the current
   schema; ``flask db downgrade -1`` reverses the most recent migration.
2. Cost metering: a recorded LLM call creates a ``cost_events`` row and
   bumps ``Article.cost_usd`` correctly per the rate card.
3. Per-article budget halt: setting ``cost_budget_usd = 0.01`` and running
   a recorded cost above that flips ``current_stage`` to ``halted_budget``.
4. Monthly cap refusal: pre-populating the ``budgets`` row at cap causes
   :func:`assert_can_start_flow` to refuse.
5. Stage outputs persist: walking an article through all four stages
   populates ``research_report_json`` / ``strategy_json`` /
   ``draft_sections_json`` / ``last_verdict_json``.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import inspect

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault(
    "GHOST_ADMIN_KEY",
    "0123456789abcdef01234567:" + "a" * 64,
)

from src.main import create_app  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.observability import Budget, CostEvent, EditorialReport  # noqa: E402
from src.models.product import Article, Product  # noqa: E402
from src.models.user import db  # noqa: E402
from src.services.cost_meter import (  # noqa: E402
    BudgetExceeded,
    CostMeter,
    DEFAULT_MONTHLY_CAP_USD,
)
from src.services.editorial_review import run_editorial_review  # noqa: E402
from src.services.model_rates import cost_for_call  # noqa: E402
from src.services.stage_persistence import (  # noqa: E402
    check_and_halt_if_over_budget,
    persist_stage_output,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app():
    """In-memory SQLite + db.create_all(); used by tests #2-#5.

    Test #1 (Alembic round-trip) doesn't use this fixture — it stands up its
    own temp-file SQLite and runs migrations against it.
    """
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _make_article(*, cost_budget_usd: float = 5.00) -> Article:
    niche = Niche.query.filter_by(name="Cybersecurity SMB").first()
    if niche is None:
        niche = Niche(name="Cybersecurity SMB")
        db.session.add(niche)
        db.session.flush()
    product = Product(name="Acme VPN Pro", niche_id=niche.id)
    db.session.add(product)
    db.session.flush()
    article = Article(
        title="Best VPN for SMBs in 2026",
        content="<h2>Intro</h2><p>...</p>",
        meta_description="A quick guide.",
        keywords=json.dumps(["vpn", "smb"]),
        product_id=product.id,
        niche_id=niche.id,
        editorial_verdict="PENDING",
        cost_budget_usd=Decimal(str(cost_budget_usd)),
    )
    db.session.add(article)
    db.session.commit()
    return article


# ---------------------------------------------------------------------------
# Test #1 — Alembic round-trip (its own DB; doesn't share the fixture)
# ---------------------------------------------------------------------------


_ALEMBIC_TEST_SCRIPT = """
import os, sys, json
os.environ.setdefault('GHOST_API_URL', 'https://ghost.test.local')
os.environ.setdefault('GHOST_ADMIN_KEY', '0123456789abcdef01234567:' + 'a'*64)
sys.path.insert(0, {root!r})

import builtins
_real_print = builtins.print

# IMPORTANT: override Config BEFORE create_app() runs. Flask-SQLAlchemy 3.x
# binds the engine at db.init_app() time, which is inside create_app(); any
# URI mutation after that point is ignored.
from src.config import Config
Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + {db_path!r}

from src.main import create_app
from src.models.user import db
from sqlalchemy import inspect
from flask_migrate import upgrade, downgrade

# Silence the create_app route-banner so our JSON is the only line on stdout.
builtins.print = lambda *a, **kw: None
app = create_app()
builtins.print = _real_print

with app.app_context():
    upgrade()
    insp = inspect(db.engine)
    after_up = {{
        'tables': sorted(insp.get_table_names()),
        'article_columns': sorted(c['name'] for c in insp.get_columns('articles')),
    }}

    # Downgrade ALL THE WAY to 0001 to verify both PR #3 and PR #5a are
    # reversible. Using a fixed target (rather than -1) keeps the test
    # stable as new migrations land.
    downgrade(revision='0001')
    insp = inspect(db.engine)
    after_down = {{
        'tables': sorted(insp.get_table_names()),
        'article_columns': sorted(c['name'] for c in insp.get_columns('articles')),
    }}

print(json.dumps({{'after_up': after_up, 'after_down': after_down}}))
"""


def test_alembic_upgrade_then_downgrade_one_round_trip():
    """``flask db upgrade`` + ``flask db downgrade -1`` round-trip.

    Runs in a subprocess so the ``db = SQLAlchemy()`` singleton isn't already
    pinned to another test's URI. Asserts:

    - upgrade → ``cost_events`` / ``budgets`` / ``editorial_reports`` tables
      exist; ``articles.cost_usd`` and ``articles.current_stage`` are
      present; ``articles.wordpress_post_id`` is absent.
    - downgrade -1 → those PR #3 artifacts are gone; ``wordpress_post_id``
      is restored; baseline tables (``articles`` etc.) survive.
    """
    import subprocess

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        Path(db_path).unlink(missing_ok=True)  # ensure empty
        script = _ALEMBIC_TEST_SCRIPT.format(root=str(ROOT), db_path=db_path)
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            check=False,
        )
        assert result.returncode == 0, (
            f"subprocess failed (code {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
        # Last stdout line is the JSON payload.
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        up, down = payload["after_up"], payload["after_down"]

        # After upgrade — full schema (baseline + PR #3 + PR #5a)
        assert {"cost_events", "budgets", "editorial_reports"} <= set(up["tables"])
        assert {"blueprints", "serp_profiles"} <= set(up["tables"])
        assert "articles" in up["tables"]
        assert "cost_usd" in up["article_columns"]
        assert "current_stage" in up["article_columns"]
        assert "wordpress_post_id" not in up["article_columns"]

        # After downgrade to 0001 — PR #3 + PR #5a artifacts gone, baseline
        # tables intact, wordpress_post_id restored.
        assert "cost_events" not in down["tables"]
        assert "budgets" not in down["tables"]
        assert "editorial_reports" not in down["tables"]
        assert "blueprints" not in down["tables"]
        assert "serp_profiles" not in down["tables"]
        assert "articles" in down["tables"]  # baseline survives
        assert "cost_usd" not in down["article_columns"]
        assert "wordpress_post_id" in down["article_columns"]
    finally:
        Path(db_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test #2 — Cost metering creates events + bumps Article.cost_usd
# ---------------------------------------------------------------------------


def test_cost_meter_record_creates_event_and_bumps_article_cost(app):
    """Known token counts → expected cost per the rate card; both rows update.

    Token counts chosen so the cost lands cleanly in ``Numeric(10, 4)`` (the
    precision of ``Article.cost_usd``). ``CostEvent.cost_usd`` is
    ``Numeric(10, 6)`` and matches the rate-card calculation exactly.
    """
    article = _make_article()

    # 10000 prompt + 5000 completion of gpt-4o-mini.
    # gpt-4o-mini = $0.000150 prompt, $0.000600 completion per 1K.
    # Expected: 10*0.000150 + 5*0.000600 = 0.001500 + 0.003000 = 0.004500
    expected = cost_for_call("gpt-4o-mini", 10000, 5000)
    assert expected == Decimal("0.004500")

    cost = CostMeter.record(
        article_id=article.id,
        stage="stage_2_creation",
        model="gpt-4o-mini",
        prompt_tokens=10000,
        completion_tokens=5000,
    )
    assert cost == expected

    events = CostEvent.query.filter_by(article_id=article.id).all()
    assert len(events) == 1
    e = events[0]
    assert e.stage == "stage_2_creation"
    assert e.model == "gpt-4o-mini"
    assert e.prompt_tokens == 10000
    assert e.completion_tokens == 5000
    assert Decimal(e.cost_usd) == expected  # full 6-decimal precision

    # Article.cost_usd is Numeric(10, 4) per the PR #3 spec — quantize
    # before comparing so we're not testing the rate card twice.
    refreshed = db.session.get(Article, article.id)
    assert Decimal(refreshed.cost_usd) == expected.quantize(Decimal("0.0001"))

    assert CostMeter.total_for_article(article.id) == expected


# ---------------------------------------------------------------------------
# Test #3 — Per-article budget halt
# ---------------------------------------------------------------------------


def test_per_article_budget_halt(app):
    """Article cost_budget_usd=0.01 + a $0.000450 spend → not over (still room).
    Push spend above 0.01 → article transitions to current_stage='halted_budget'."""
    article = _make_article(cost_budget_usd=0.01)

    # First small spend stays under cap.
    CostMeter.record(article.id, "stage_0_research", "gpt-4o-mini", 1000, 500)
    halted = check_and_halt_if_over_budget(article.id)
    assert halted is False, "should not halt while under cap"

    # Push well over the $0.01 cap with a large gpt-4-turbo call.
    # gpt-4-turbo: $0.01 prompt + $0.03 completion per 1K.
    # 1000 prompt + 1000 completion = 0.01 + 0.03 = $0.04 — over $0.01 cap.
    CostMeter.record(article.id, "stage_2_creation", "gpt-4-turbo", 1000, 1000)
    halted = check_and_halt_if_over_budget(article.id)
    assert halted is True

    refreshed = db.session.get(Article, article.id)
    assert refreshed.current_stage == "halted_budget"
    assert refreshed.stage_status == "halted"


# ---------------------------------------------------------------------------
# Test #4 — Monthly cap refusal
# ---------------------------------------------------------------------------


def test_monthly_cap_refusal(app):
    """Pre-populating budgets at cap → assert_can_start_flow raises BudgetExceeded."""
    from datetime import datetime

    month = datetime.utcnow().strftime("%Y-%m")
    cap = DEFAULT_MONTHLY_CAP_USD  # $100
    db.session.add(Budget(month=month, cap_usd=cap, spent_usd=cap))
    db.session.commit()

    with pytest.raises(BudgetExceeded):
        CostMeter.assert_can_start_flow()


# ---------------------------------------------------------------------------
# Test #5 — Stage outputs persist across all four stages
# ---------------------------------------------------------------------------


def test_stage_outputs_persist_across_pipeline(app):
    """Walking an article through all four stages populates every JSON column."""
    article = _make_article()

    persist_stage_output(article.id, "stage_0_research", {"trends": ["smb-vpn"]})
    persist_stage_output(article.id, "stage_1_strategy", {"topics": ["best-vpn-smb"]})
    persist_stage_output(
        article.id, "stage_2_creation", {"draft": "<h2>Intro</h2>..."}
    )

    # Stage 3 — Editorial — uses the real run_editorial_review path so we
    # exercise the same wiring the flow uses, including last_verdict_json.
    verdict = run_editorial_review(article.id)
    assert verdict.verdict in ("PUBLISH", "REJECT")

    refreshed = db.session.get(Article, article.id)
    assert refreshed.research_report_json is not None
    assert refreshed.strategy_json is not None
    assert refreshed.draft_sections_json is not None
    assert refreshed.last_verdict_json is not None
    # stage 3 also flips current_stage to awaiting_human_review (PR #2 invariant)
    # and bumps stage_status to 'complete' so the dashboard / queue see the
    # right state (foundation-cleanup fix; smoke-test caught this).
    assert refreshed.current_stage == "awaiting_human_review"
    assert refreshed.stage_status == "complete"

    # Editorial report row exists too (PR #3 normalization).
    reports = EditorialReport.query.filter_by(article_id=article.id).all()
    assert len(reports) == 1
    assert reports[0].verdict == verdict.verdict
