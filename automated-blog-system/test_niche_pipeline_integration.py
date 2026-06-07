"""PR #6.4 — Integration test: NichePipelineService now invokes
BlogCreationFlow instead of the legacy ContentGenerator. We mock the flow
itself (no real LLM calls) and assert the wiring is correct.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Force safe defaults; individual tests override as needed.
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("PIPELINE_ALLOW_TEMPLATE_FALLBACK", "true")

from src.main import create_app  # noqa: E402
from src.models.user import db  # noqa: E402
from src.models.niche import Niche  # noqa: E402
from src.models.product import Product, Article  # noqa: E402
from src.services.niche_pipeline import NichePipelineService  # noqa: E402


@pytest.fixture()
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_pipeline_invokes_blog_creation_flow(app):
    """Creating a niche kicks off NichePipelineService which, for each
    product, invokes BlogCreationFlow with the right inputs."""
    from src.config import Config

    # Force the no-AI + template-fallback path so the test never hits OpenAI.
    # (Config attrs are read at module-import time; module-level os.environ
    # tweaks at the top of this file may have lost the race against an
    # earlier test file's `from src.main import ...`.)
    original_key = Config.OPENAI_API_KEY
    original_flag = Config.PIPELINE_ALLOW_TEMPLATE_FALLBACK
    Config.OPENAI_API_KEY = None
    Config.PIPELINE_ALLOW_TEMPLATE_FALLBACK = True

    try:
        niche = Niche(
            name="Test Niche",
            description="A test niche.",
            target_keywords="test, niche",
            active=True,
        )
        db.session.add(niche)
        db.session.commit()

        service = NichePipelineService()

        # Mock BlogCreationFlow at its import path inside niche_pipeline.
        with patch(
            "core.crewai_system.blog_creation_flow.BlogCreationFlow"
        ) as MockFlow:
            instance = MagicMock()
            MockFlow.return_value = instance
            # _execute_pipeline runs synchronously when called directly.
            service._execute_pipeline(app, niche.id)

        db.session.expire_all()
        products = Product.query.filter_by(niche_id=niche.id).all()
        articles = Article.query.filter_by(niche_id=niche.id).all()
        assert len(products) > 0, "expected products to be seeded"
        assert len(articles) == len(products), \
            "expected one stub article per product"
        assert instance.kickoff.call_count == len(products), \
            "BlogCreationFlow.kickoff should be called once per product"

        # Verify the inputs passed to kickoff have the keys the flow expects.
        for call in instance.kickoff.call_args_list:
            kwargs = call.kwargs
            inputs = kwargs.get("inputs") or (call.args[0] if call.args else {})
            assert "niche" in inputs
            assert "blog_instance_id" in inputs
            assert "current_article_id" in inputs
            assert inputs["niche"] == "Test Niche"
    finally:
        Config.OPENAI_API_KEY = original_key
        Config.PIPELINE_ALLOW_TEMPLATE_FALLBACK = original_flag


def test_pipeline_refuses_template_fallback_by_default(app):
    """Without PIPELINE_ALLOW_TEMPLATE_FALLBACK, the dummy template path is
    blocked when OPENAI_API_KEY is missing — pipeline should land in error
    state rather than seeding off-niche products."""
    from src.config import Config

    original_flag = Config.PIPELINE_ALLOW_TEMPLATE_FALLBACK
    original_key = Config.OPENAI_API_KEY
    Config.PIPELINE_ALLOW_TEMPLATE_FALLBACK = False
    Config.OPENAI_API_KEY = None

    try:
        niche = Niche(name="Refuse Test", active=True)
        db.session.add(niche)
        db.session.commit()

        service = NichePipelineService()
        service._execute_pipeline(app, niche.id)

        # Force the test's session to drop its cached identity-map view of
        # the niche so we observe what _execute_pipeline committed.
        db.session.expire_all()
        refreshed = db.session.get(Niche, niche.id)
        assert refreshed.pipeline_status == "error", \
            f"expected pipeline_status='error', got {refreshed.pipeline_status!r}"
        # No products should have been seeded.
        assert Product.query.filter_by(niche_id=niche.id).count() == 0
        assert Article.query.filter_by(niche_id=niche.id).count() == 0
    finally:
        Config.PIPELINE_ALLOW_TEMPLATE_FALLBACK = original_flag
        Config.OPENAI_API_KEY = original_key


def test_article_to_headless_contract_includes_affiliate_cta(app):
    """Article.to_headless_contract() must populate calls_to_action from the
    linked Product's affiliate_url + tracking_id (PR #6.4 fix)."""
    niche = Niche(name="CTA Test", active=True)
    db.session.add(niche)
    db.session.flush()

    product = Product(
        name="Test Product",
        niche_id=niche.id,
        affiliate_url="https://www.amazon.com/dp/B0EXAMPLE",
        tracking_id="deskcred-20",
    )
    db.session.add(product)
    db.session.flush()

    article = Article(
        title="Test Title",
        content="<p>Body.</p>",
        meta_description="A short summary.",
        product_id=product.id,
        niche_id=niche.id,
    )
    db.session.add(article)
    db.session.commit()

    contract = article.to_headless_contract()
    ctas = contract["calls_to_action"]
    assert len(ctas) == 1
    cta = ctas[0]
    assert cta["type"] == "affiliate"
    assert "amazon.com/dp/B0EXAMPLE" in cta["target"]
    assert "tag=deskcred-20" in cta["target"]
    assert "Test Product" in cta["anchor"]


def test_article_to_headless_contract_omits_cta_when_no_affiliate_url(app):
    """No affiliate_url on the product → no CTA emitted (article still
    publishes, just without a link)."""
    niche = Niche(name="No CTA", active=True)
    db.session.add(niche)
    db.session.flush()

    product = Product(name="Bare Product", niche_id=niche.id)  # no affiliate_url
    db.session.add(product)
    db.session.flush()

    article = Article(
        title="No CTA Title",
        content="<p>Body.</p>",
        product_id=product.id,
        niche_id=niche.id,
    )
    db.session.add(article)
    db.session.commit()

    contract = article.to_headless_contract()
    assert contract["calls_to_action"] == []


def test_article_to_headless_contract_does_not_double_append_tag(app):
    """If the affiliate_url already contains a tag= param, don't append
    another one."""
    niche = Niche(name="Tag Test", active=True)
    db.session.add(niche)
    db.session.flush()

    product = Product(
        name="Already-Tagged",
        niche_id=niche.id,
        affiliate_url="https://www.amazon.com/dp/B0X?tag=other-20",
        tracking_id="deskcred-20",
    )
    db.session.add(product)
    db.session.flush()

    article = Article(
        title="t", content="c", product_id=product.id, niche_id=niche.id,
    )
    db.session.add(article)
    db.session.commit()

    target = article.to_headless_contract()["calls_to_action"][0]["target"]
    assert target.count("tag=") == 1
    assert "tag=other-20" in target  # original preserved
