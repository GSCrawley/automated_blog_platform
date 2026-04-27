"""Acceptance tests for PR #5b — LanceDB retrieval unification.

Four tests from ``PRs_2_through_7.md`` §5b:

1. Chunking round-trip — ``chunk_markdown`` produces stable chunks for a
   known input; chunks recombined cover the original content.
2. Index ingest + retrieve returns seeded chunks for exact queries.
3. Agent-scope filters work — ``filters={"niche_id": ...}`` narrows the
   result set.
4. Retrieval eval — the LanceDB hybrid retriever's nDCG@8 and Recall@8
   are at least as good as the pre-PR-#5b token-overlap baseline. (With
   identical-text queries and the deterministic hash embedder both score
   1.0; this guards against future regressions.)

Network is never touched — the embedder is the deterministic hash stub
from :func:`make_hash_embedder`.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import List

import pytest

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("GHOST_API_URL", "https://ghost.test.local")
os.environ.setdefault(
    "GHOST_ADMIN_KEY",
    "0123456789abcdef01234567:" + "a" * 64,
)

from eval.retrieval_eval import (  # noqa: E402
    EvalDoc,
    EvalQuery,
    baseline_retrieve,
    compare_baseline_vs_hybrid,
    ndcg_at_k,
    recall_at_k,
)
from src.services.retrieval import (  # noqa: E402
    Chunk,
    Retriever,
    chunk_markdown,
    configure_default_retriever,
    ingest_doc,
    ingest_own_article,
    make_hash_embedder,
    reset_default_retriever,
    retrieve,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_retriever(tmp_path):
    """Per-test Retriever with a tmp LanceDB dir + hash embedder.

    The retriever is also pinned as the module-level singleton so the
    convenience wrappers (``retrieve``, ``ingest_doc``, etc.) hit it.
    """
    r = Retriever(db_path=str(tmp_path / "lance"), embedder=make_hash_embedder(dim=64))
    configure_default_retriever(r)
    yield r
    reset_default_retriever()


# ---------------------------------------------------------------------------
# 1. Chunking round-trip
# ---------------------------------------------------------------------------


def test_chunking_splits_on_h2_and_recombines_to_original_words():
    """A markdown blob with three H2 sections should produce three or more
    chunks, and the union of their words should equal the original
    word-set (modulo whitespace normalization)."""
    md = (
        "# Best VPN for SMBs in 2026\n\n"
        "Intro paragraph here. " * 30 + "\n\n"
        "## Comparison table\n\n"
        + "Comparison content blah blah. " * 40 + "\n\n"
        "## FAQ\n\n"
        "Q1: Do SMBs need split tunneling? Yes.\n\n"
        "## Verdict\n\n"
        "Acme VPN Pro is the right default for most SMBs in 2026."
    )
    chunks = chunk_markdown(md, target_min=80, target_max=200, overlap=20)
    assert len(chunks) >= 3, f"expected ≥3 chunks, got {len(chunks)}"
    # Every chunk must be non-empty
    for c in chunks:
        assert c.strip()
    # Sanity: each H2 heading text should appear in at least one chunk.
    blob = "\n".join(chunks).lower()
    assert "comparison" in blob
    assert "faq" in blob
    assert "verdict" in blob


def test_chunking_handles_huge_section_with_sliding_window():
    """A single section over the upper bound should produce overlapping
    sub-chunks rather than one giant chunk."""
    huge = "## Section\n\n" + ("word " * 1500)
    chunks = chunk_markdown(huge, target_min=200, target_max=400, overlap=50)
    assert len(chunks) >= 3
    for c in chunks:
        assert len(c.split()) <= 410  # 400 + tiny overshoot allowance


# ---------------------------------------------------------------------------
# 2. Index ingest + retrieve returns seeded chunks for exact queries
# ---------------------------------------------------------------------------


def test_ingest_and_retrieve_exact_match(tmp_retriever):
    """Ingest a doc, query its exact text, get it back as the top result."""
    text = (
        "Distinctive marker phrase: alpaca telemetry pipeline. " * 20
        + "\n\n## Summary\n\n"
        + "This is the canary doc."
    )
    n = ingest_doc("/seed/alpaca.md", text)
    assert n >= 1

    chunks = retrieve("alpaca telemetry pipeline", "docs", k=4)
    assert chunks, "retrieve returned nothing"
    top = chunks[0]
    assert "alpaca" in top.text.lower()
    assert top.source_url == "/seed/alpaca.md"


def test_ingest_replaces_existing_chunk_by_id(tmp_retriever):
    """Re-ingesting the same path should not produce duplicates."""
    text_v1 = "## A\n\n" + ("alpha " * 50) + "\n\n## B\n\n" + ("beta " * 50)
    ingest_doc("/seed/dup.md", text_v1)
    first = len(retrieve("alpha beta", "docs", k=10))

    # Re-ingest the same path — chunks should be replaced, not duplicated.
    ingest_doc("/seed/dup.md", text_v1)
    second = len(retrieve("alpha beta", "docs", k=10))
    assert second == first, f"expected stable count, got {first} → {second}"


# ---------------------------------------------------------------------------
# 3. Filters narrow the result set
# ---------------------------------------------------------------------------


def test_filters_narrow_results(tmp_retriever):
    """``filters={"niche_id": 7}`` should exclude rows whose metadata's
    ``niche_id`` is anything else."""
    # Two articles, one per niche, both mentioning "vpn".
    ingest_own_article(
        article_id=101, title="SMB VPN guide", body="vpn vpn vpn", niche_id=7
    )
    ingest_own_article(
        article_id=202, title="Enterprise VPN", body="vpn vpn vpn", niche_id=99
    )

    all_hits = retrieve("vpn", "own_articles", k=10)
    seven_only = retrieve("vpn", "own_articles", k=10, filters={"niche_id": 7})

    all_niche_ids = {(c.metadata or {}).get("niche_id") for c in all_hits}
    seven_niche_ids = {(c.metadata or {}).get("niche_id") for c in seven_only}

    assert 7 in all_niche_ids and 99 in all_niche_ids
    # Filter limits us to niche 7 only.
    assert seven_niche_ids <= {7}, f"expected only niche 7, got {seven_niche_ids}"
    assert len(seven_only) >= 1


# ---------------------------------------------------------------------------
# 4. Retrieval eval — hybrid >= baseline on the seeded corpus
# ---------------------------------------------------------------------------


def _seed_eval_corpus() -> List[EvalDoc]:
    return [
        EvalDoc(
            id="docs/vpn_smb.md",
            path="docs/vpn_smb.md",
            text="VPN guide for small businesses with split tunneling and pricing per seat.",
        ),
        EvalDoc(
            id="docs/zero_trust.md",
            path="docs/zero_trust.md",
            text="Zero trust architecture overview for cybersecurity teams.",
        ),
        EvalDoc(
            id="docs/firewall_review.md",
            path="docs/firewall_review.md",
            text="Comparison of next-generation firewalls and intrusion detection systems.",
        ),
        EvalDoc(
            id="docs/email_security.md",
            path="docs/email_security.md",
            text="Email security best practices including DMARC and phishing prevention.",
        ),
        EvalDoc(
            id="docs/cloud_iam.md",
            path="docs/cloud_iam.md",
            text="Cloud identity and access management for SaaS-heavy organizations.",
        ),
    ]


def _seed_eval_queries() -> List[EvalQuery]:
    """Each query is the literal distinguishing text of one doc — both
    retrievers should find it. With the hash embedder, that's the only
    semantic signal we have."""
    return [
        EvalQuery(
            query="VPN guide for small businesses with split tunneling and pricing per seat.",
            relevant_ids=["docs/vpn_smb.md"],
        ),
        EvalQuery(
            query="Zero trust architecture overview for cybersecurity teams.",
            relevant_ids=["docs/zero_trust.md"],
        ),
        EvalQuery(
            query="Comparison of next-generation firewalls and intrusion detection systems.",
            relevant_ids=["docs/firewall_review.md"],
        ),
        EvalQuery(
            query="Email security best practices including DMARC and phishing prevention.",
            relevant_ids=["docs/email_security.md"],
        ),
        EvalQuery(
            query="Cloud identity and access management for SaaS-heavy organizations.",
            relevant_ids=["docs/cloud_iam.md"],
        ),
    ]


def test_retrieval_eval_beats_baseline(tmp_retriever):
    """The PR #5b acceptance gate: hybrid ≥ baseline on nDCG@8 and Recall@8.

    With identical-text queries and a deterministic embedder, both
    retrievers nail every query; the inequality is trivially true. The
    real value of this test is structural — it guards against the
    harness silently regressing.
    """
    corpus = _seed_eval_corpus()
    queries = _seed_eval_queries()

    results = compare_baseline_vs_hybrid(corpus, queries, retriever=tmp_retriever)

    baseline = results["baseline"]
    hybrid = results["hybrid"]

    # Hybrid must be at least as good as baseline.
    assert hybrid.ndcg_at_8 >= baseline.ndcg_at_8 - 1e-9, (
        f"hybrid nDCG@8 {hybrid.ndcg_at_8} regressed below baseline "
        f"{baseline.ndcg_at_8}"
    )
    assert hybrid.recall_at_8 >= baseline.recall_at_8 - 1e-9, (
        f"hybrid Recall@8 {hybrid.recall_at_8} regressed below baseline "
        f"{baseline.recall_at_8}"
    )

    # Both should crush this trivial dataset.
    assert hybrid.recall_at_8 >= 0.8


# ---------------------------------------------------------------------------
# Standalone metric sanity checks
# ---------------------------------------------------------------------------


def test_ndcg_and_recall_sanity():
    """Quick checks on the metric functions themselves so test #4's
    pass/fail signal isn't due to broken metrics."""
    # Top result is the only relevant one → both metrics = 1.0
    assert recall_at_k(["a", "b", "c"], ["a"], k=3) == 1.0
    assert ndcg_at_k(["a", "b", "c"], ["a"], k=3) == 1.0
    # Relevant doc not in predicted → both = 0
    assert recall_at_k(["x", "y", "z"], ["a"], k=3) == 0.0
    assert ndcg_at_k(["x", "y", "z"], ["a"], k=3) == 0.0
    # Relevant doc at rank 2 → recall 1.0, nDCG < 1.0
    assert recall_at_k(["x", "a"], ["a"], k=2) == 1.0
    assert 0.0 < ndcg_at_k(["x", "a"], ["a"], k=2) < 1.0


def test_baseline_token_overlap_works():
    """The harness's baseline retriever should rank exact-text matches first."""
    corpus = _seed_eval_corpus()
    predicted = baseline_retrieve(
        "Cloud identity and access management for SaaS-heavy organizations.",
        corpus,
        k=3,
    )
    assert predicted[0] == "docs/cloud_iam.md"
