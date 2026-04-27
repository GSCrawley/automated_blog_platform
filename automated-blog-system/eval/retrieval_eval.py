"""Retrieval eval harness (PR #5b §5b.4).

Two retrievers, one corpus, one query set with ground-truth doc IDs,
two metrics. The doc's acceptance rule: PR #5b's hybrid retriever must
beat the pre-PR-#5b token-overlap baseline on nDCG@8 and Recall@8 — if
not, **stop and ask the user before merging**.

The harness is structured so it can be run two ways:

1. **Unit test** — ``pytest -q test_retrieval.py::test_retrieval_eval_beats_baseline``
   uses the hash embedder + a synthetic corpus to verify the plumbing
   end-to-end. With identical-text queries, both retrievers score 1.0 on
   exact matches, so the "new ≥ baseline" assertion is trivially true and
   the test catches regressions in the harness itself.
2. **Manual run** — ``python -m eval.retrieval_eval`` reads the real
   ``/docs`` corpus and uses OpenAI embeddings (requires ``OPENAI_API_KEY``)
   to produce the numbers the human reviews before merging the PR.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from src.services.retrieval import (
    Chunk,
    Retriever,
    chunk_markdown,
    ingest_doc,
    retrieve as default_retrieve,
)


# ---------------------------------------------------------------------------
# Corpus + query types
# ---------------------------------------------------------------------------


@dataclass
class EvalDoc:
    """One corpus entry. ``id`` is the ground-truth identifier; ``path`` is
    the human-readable label."""

    id: str
    path: str
    text: str


@dataclass
class EvalQuery:
    """One labeled query.

    ``relevant_ids`` is the set of doc ids considered relevant for this
    query. Order doesn't matter — Recall@k just checks set membership;
    nDCG uses binary relevance gains (1 for relevant, 0 otherwise).
    """

    query: str
    relevant_ids: List[str]


# ---------------------------------------------------------------------------
# Baseline retriever — what we had before PR #5b: lowercased token overlap.
# Kept here (rather than imported from knowledge_base) so the eval is the
# single source of truth for "the old behavior".
# ---------------------------------------------------------------------------


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


def baseline_retrieve(query: str, corpus: List[EvalDoc], k: int = 8) -> List[str]:
    """Pre-PR-#5b retrieval — token-overlap, no embeddings. Returns the
    top-``k`` doc ids by overlap count."""
    q_tokens = set(_tokens(query))
    scored: List[Tuple[int, str]] = []
    for doc in corpus:
        overlap = len(q_tokens.intersection(_tokens(doc.text)))
        if overlap > 0:
            scored.append((overlap, doc.id))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc_id for _, doc_id in scored[:k]]


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def recall_at_k(predicted: List[str], relevant: List[str], k: int = 8) -> float:
    if not relevant:
        return 0.0
    top_k = set(predicted[:k])
    return len(top_k.intersection(relevant)) / len(relevant)


def ndcg_at_k(predicted: List[str], relevant: List[str], k: int = 8) -> float:
    """Binary-relevance nDCG@k. Equivalent to the standard form when each
    relevant doc has gain 1 and all others 0."""
    if not relevant:
        return 0.0
    rel_set = set(relevant)
    dcg = 0.0
    for i, doc_id in enumerate(predicted[:k]):
        if doc_id in rel_set:
            dcg += 1.0 / math.log2(i + 2)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


@dataclass
class EvalResult:
    name: str
    ndcg_at_8: float
    recall_at_8: float
    per_query: List[Dict[str, float]]


def run_eval(
    retrieve_fn: Callable[[str, int], List[str]],
    queries: List[EvalQuery],
    *,
    name: str,
    k: int = 8,
) -> EvalResult:
    """Run ``retrieve_fn`` over every ``queries[i].query`` and aggregate
    metrics. ``retrieve_fn(query, k)`` must return a list of doc ids."""
    per: List[Dict[str, float]] = []
    ndcgs: List[float] = []
    recalls: List[float] = []
    for q in queries:
        predicted = retrieve_fn(q.query, k)
        ndcg = ndcg_at_k(predicted, q.relevant_ids, k=k)
        recall = recall_at_k(predicted, q.relevant_ids, k=k)
        ndcgs.append(ndcg)
        recalls.append(recall)
        per.append({"query": q.query, "ndcg@8": ndcg, "recall@8": recall})
    return EvalResult(
        name=name,
        ndcg_at_8=sum(ndcgs) / len(ndcgs) if ndcgs else 0.0,
        recall_at_8=sum(recalls) / len(recalls) if recalls else 0.0,
        per_query=per,
    )


def compare_baseline_vs_hybrid(
    corpus: List[EvalDoc],
    queries: List[EvalQuery],
    *,
    retriever: Optional[Retriever] = None,
) -> Dict[str, EvalResult]:
    """Run both retrievers, return a dict ``{baseline: ..., hybrid: ...}``.

    The caller decides whether the resulting metrics justify shipping —
    this function is pure measurement, no assertions."""
    if retriever is not None:
        for d in corpus:
            ingest_doc(d.path, d.text, retriever=retriever)

    def _hybrid_retrieve(q: str, k: int) -> List[str]:
        if retriever is not None:
            chunks: List[Chunk] = retriever.retrieve(q, collection="docs", k=k)
        else:
            chunks = default_retrieve(q, "docs", k=k)
        # Map chunks back to doc ids via the ``path`` metadata field; that's
        # how the eval corpus is keyed.
        seen = []
        for c in chunks:
            doc_id = (c.metadata or {}).get("path") or c.source_url
            if doc_id and doc_id not in seen:
                seen.append(doc_id)
        return seen

    return {
        "baseline": run_eval(
            lambda q, k: baseline_retrieve(q, corpus, k=k),
            queries,
            name="token_overlap",
        ),
        "hybrid": run_eval(_hybrid_retrieve, queries, name="lancedb_hybrid"),
    }


__all__ = [
    "EvalDoc",
    "EvalQuery",
    "EvalResult",
    "baseline_retrieve",
    "ndcg_at_k",
    "recall_at_k",
    "run_eval",
    "compare_baseline_vs_hybrid",
]
