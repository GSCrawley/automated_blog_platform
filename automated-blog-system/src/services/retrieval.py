"""Unified retrieval interface (PR #5b).

Replaces the naive token-overlap retrieval in :mod:`knowledge_base` with a
LanceDB-backed hybrid (vector + BM25) store. Four collections:

- ``docs``             — static seed content under ``/docs``
- ``profiles``         — :class:`ArticleProfile` text from PR #5a SERP forensics
- ``research_harvest`` — research outputs from the Research crew
- ``own_articles``     — our own published articles (self-retrieval)

Public surface — every consumer (Research crew, Editor, dashboard) goes
through :func:`retrieve`::

    chunks = retrieve(query, "profiles", k=8, filters={"niche_id": 3})

Embedding is injectable so tests stay network-free. Production wires
OpenAI's ``text-embedding-3-small`` (1536-d). Tests pass a deterministic
hash-based stub.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional

logger = logging.getLogger(__name__)


CollectionName = Literal["docs", "profiles", "research_harvest", "own_articles"]
COLLECTIONS: tuple = ("docs", "profiles", "research_harvest", "own_articles")

# Default embedding dimension. Must match whatever embedder is wired in. The
# OpenAI ``text-embedding-3-small`` model is 1536-d; the test stub uses 64-d
# for fast deterministic tests.
DEFAULT_VECTOR_DIM = 1536


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


@dataclass
class Chunk:
    """One retrievable unit. ``id`` is unique within the collection."""

    id: str
    collection: CollectionName
    text: str
    source_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0  # populated by retrieve(); 0 at ingest time

    def to_record(self, vector: List[float]) -> Dict[str, Any]:
        """Project to a LanceDB row."""
        return {
            "id": self.id,
            "collection": self.collection,
            "text": self.text,
            "source_url": self.source_url,
            "metadata_json": json.dumps(self.metadata or {}),
            "vector": vector,
        }

    @classmethod
    def from_record(cls, row: Dict[str, Any]) -> "Chunk":
        meta_raw = row.get("metadata_json") or "{}"
        try:
            meta = json.loads(meta_raw)
        except (TypeError, ValueError):
            meta = {}
        score_val = row.get("_distance")
        if score_val is None:
            score_val = row.get("_score") or row.get("score") or 0.0
        return cls(
            id=row["id"],
            collection=row["collection"],
            text=row["text"],
            source_url=row.get("source_url") or "",
            metadata=meta,
            score=float(score_val),
        )


# ---------------------------------------------------------------------------
# Chunker — split markdown on H2 boundaries, then sliding window within
# any section that exceeds the upper bound.
# ---------------------------------------------------------------------------

_H2_SPLIT_RE = re.compile(r"^##\s", re.MULTILINE)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub(" ", text or "")


def _word_count(text: str) -> int:
    return len([w for w in (text or "").split() if w.strip()])


def chunk_markdown(
    text: str,
    *,
    target_min: int = 400,
    target_max: int = 800,
    overlap: int = 50,
) -> List[str]:
    """Split markdown into ~400-800-word chunks at H2 boundaries.

    Sections smaller than ``target_min`` are merged with the next; sections
    larger than ``target_max`` are sliced into overlapping windows. The
    word counts are deliberately approximate — token-perfect splitting
    needs ``tiktoken``; the bounds are guidance, not a contract.
    """
    if not text:
        return []
    sections = [s.strip() for s in _H2_SPLIT_RE.split(text) if s.strip()]
    if not sections:
        sections = [text.strip()]

    chunks: List[str] = []
    buffer: List[str] = []
    buffer_words = 0

    def _flush():
        if buffer:
            chunks.append("\n\n".join(buffer).strip())
            buffer.clear()

    for section in sections:
        words = section.split()
        if len(words) > target_max:
            _flush()
            for sliced in _sliding_windows(words, target_max, overlap):
                chunks.append(" ".join(sliced))
            buffer_words = 0
            continue
        if buffer_words + len(words) > target_max:
            _flush()
            buffer_words = 0
        buffer.append(section)
        buffer_words += len(words)
        if buffer_words >= target_min:
            _flush()
            buffer_words = 0

    _flush()
    return [c for c in chunks if c.strip()]


def _sliding_windows(words: List[str], window: int, overlap: int) -> Iterable[List[str]]:
    if window <= 0:
        yield words
        return
    step = max(1, window - overlap)
    i = 0
    while i < len(words):
        yield words[i : i + window]
        if i + window >= len(words):
            break
        i += step


def chunk_html(html: str, **kwargs) -> List[str]:
    """HTML chunker — strip tags then defer to :func:`chunk_markdown`."""
    return chunk_markdown(_strip_html(html), **kwargs)


# ---------------------------------------------------------------------------
# Embedders
# ---------------------------------------------------------------------------


# Embedder protocol: takes a list of strings, returns a list of vectors.
Embedder = Callable[[List[str]], List[List[float]]]


def make_hash_embedder(dim: int = 64) -> Embedder:
    """Deterministic hash-based embedder for tests. Identical text → identical
    vector → cosine similarity 1.0, which is exactly what acceptance test #2
    needs ("ingest a chunk, query its exact text, get it back as top-1")."""

    def _embed(texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for text in texts:
            h = hashlib.sha256((text or "").encode("utf-8")).digest()
            # Hash output is 32 bytes; tile to dim.
            byts = (h * ((dim + len(h) - 1) // len(h)))[:dim]
            vec = [(b - 128) / 128.0 for b in byts]
            # L2 normalize so cosine == dot.
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            out.append([v / norm for v in vec])
        return out

    return _embed


def make_openai_embedder(
    model: str = "text-embedding-3-small",
    *,
    api_key: Optional[str] = None,
    article_id: Optional[int] = None,
    stage: str = "stage_5b_retrieval",
) -> Embedder:
    """Embedder backed by OpenAI's embeddings API.

    When ``article_id`` is supplied, every batch is recorded against PR #3's
    :class:`CostMeter` so embedding spend lands in the same per-article and
    per-month roll-ups as completion calls.
    """
    from openai import OpenAI  # lazy — keeps import tree clean for tests

    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def _embed(texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        resp = client.embeddings.create(model=model, input=texts)
        if article_id is not None:
            try:
                from src.services.cost_meter import CostMeter  # noqa: WPS433

                CostMeter.record(
                    article_id=article_id,
                    stage=stage,
                    model=model,
                    prompt_tokens=resp.usage.prompt_tokens,
                    completion_tokens=0,
                )
            except Exception:  # pragma: no cover — observability mustn't break retrieval
                logger.exception("CostMeter.record failed for embedding call")
        return [d.embedding for d in resp.data]

    return _embed


# ---------------------------------------------------------------------------
# Retriever — LanceDB hybrid (vector + BM25)
# ---------------------------------------------------------------------------


# Module-level registry so callers don't have to thread a Retriever instance
# through every call site. Threading lock keeps the singleton init safe.
_RETRIEVER_LOCK = threading.Lock()
_DEFAULT_RETRIEVER: Optional["Retriever"] = None


# Hybrid weighting per the doc spec: "weighted merge (start 0.7/0.3)".
DEFAULT_VECTOR_WEIGHT = 0.7
DEFAULT_LEXICAL_WEIGHT = 0.3


class Retriever:
    """LanceDB-backed retriever with one table per collection.

    Tables live under ``db_path``; each is created lazily on first ingest.
    Hybrid search combines vector similarity (cosine) and BM25 lexical
    scores with a fixed weighted merge.
    """

    def __init__(
        self,
        *,
        db_path: Optional[str] = None,
        embedder: Optional[Embedder] = None,
        vector_dim: int = DEFAULT_VECTOR_DIM,
        vector_weight: float = DEFAULT_VECTOR_WEIGHT,
        lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
    ) -> None:
        import lancedb  # lazy import — heavy

        self.db_path = db_path or os.environ.get(
            "LANCEDB_PATH", "./data/lancedb"
        )
        self.embedder = embedder or make_hash_embedder()
        self.vector_dim = vector_dim
        self.vector_weight = vector_weight
        self.lexical_weight = lexical_weight
        os.makedirs(self.db_path, exist_ok=True)
        self._db = lancedb.connect(self.db_path)
        self._tables: Dict[str, Any] = {}
        self._fts_indexed: Dict[str, bool] = {}

    def _existing_table_names(self) -> List[str]:
        """Return the list of table names from the LanceDB connection.

        ``list_tables()`` was added in newer LanceDB releases but returns a
        ``ListTablesResponse`` object (not a list); the older ``table_names()``
        returns ``List[str]`` but is deprecation-warned. We try the new API
        first, unwrap the response, and fall back to ``table_names()`` if
        anything goes wrong.
        """
        try:
            resp = self._db.list_tables()
        except Exception:  # pragma: no cover
            return list(self._db.table_names())  # type: ignore[no-any-return]
        if isinstance(resp, list):
            return list(resp)
        tables_attr = getattr(resp, "tables", None)
        if tables_attr is not None:
            return list(tables_attr)
        return list(self._db.table_names())  # type: ignore[no-any-return]

    # ---- table mgmt ------------------------------------------------------

    def _table(self, collection: str):
        if collection in self._tables:
            return self._tables[collection]
        if collection in self._existing_table_names():
            t = self._db.open_table(collection)
        else:
            # Probe the embedder to learn the actual dimension.
            probe_vec = self.embedder(["__schema_probe__"])[0]
            schema = _make_arrow_schema(len(probe_vec))
            t = self._db.create_table(collection, schema=schema, mode="create")
        self._tables[collection] = t
        return t

    def _ensure_fts(self, collection: str) -> None:
        """Create the BM25 full-text index over ``text`` if not present.

        Skipped silently if the LanceDB build doesn't support FTS — vector
        search still works, the hybrid degrades to vector-only.
        """
        if self._fts_indexed.get(collection):
            return
        table = self._table(collection)
        try:
            table.create_fts_index("text", replace=True)
            self._fts_indexed[collection] = True
        except Exception:  # pragma: no cover — older LanceDB / no FTS
            logger.debug("FTS index create failed for %s; vector-only", collection)
            self._fts_indexed[collection] = False

    # ---- ingest ---------------------------------------------------------

    def ingest(self, chunks: List[Chunk]) -> int:
        """Embed + insert ``chunks``. Returns the count inserted.

        Chunks are grouped by collection so we hit each LanceDB table once.
        Existing rows with the same id are replaced (insert-or-replace).
        """
        if not chunks:
            return 0
        by_coll: Dict[str, List[Chunk]] = {}
        for c in chunks:
            by_coll.setdefault(c.collection, []).append(c)

        total = 0
        for coll, group in by_coll.items():
            vectors = self.embedder([c.text for c in group])
            rows = [c.to_record(v) for c, v in zip(group, vectors)]
            table = self._table(coll)
            ids = [c.id for c in group]
            # Upsert semantics: drop any existing rows with these ids first.
            try:
                table.delete(_quoted_id_filter(ids))
            except Exception:
                pass
            table.add(rows)
            total += len(rows)
            self._fts_indexed[coll] = False  # FTS index needs re-create
        return total

    # ---- retrieve --------------------------------------------------------

    def retrieve(
        self,
        query: str,
        *,
        collection: CollectionName,
        k: int = 8,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Hybrid search. Returns at most ``k`` :class:`Chunk` objects with
        ``score`` populated."""
        if collection not in COLLECTIONS:
            raise ValueError(f"unknown collection {collection!r}")
        if collection not in self._existing_table_names():
            return []
        table = self._table(collection)

        where = _build_where_clause(filters)

        # Vector branch.
        vec = self.embedder([query])[0]
        vector_hits = _safe_search(table, vec, k=max(k * 4, k), where=where)

        # Lexical (BM25) branch — best-effort.
        self._ensure_fts(collection)
        lex_hits: List[Dict[str, Any]] = []
        if self._fts_indexed.get(collection):
            try:
                lex_hits = _safe_search(table, query, k=max(k * 4, k), where=where, fts=True)
            except Exception:  # pragma: no cover
                lex_hits = []

        # Merge with normalized weights.
        merged = _hybrid_merge(
            vector_hits,
            lex_hits,
            vector_weight=self.vector_weight,
            lexical_weight=self.lexical_weight,
        )
        # Cap to k after merge.
        return [Chunk.from_record(r) for r in merged[:k]]

    # ---- maintenance ----------------------------------------------------

    def reset(self) -> None:
        """Drop every collection table. Tests use this to start clean."""
        for name in list(self._existing_table_names()):
            try:
                self._db.drop_table(name)
            except Exception:  # pragma: no cover
                pass
        self._tables.clear()
        self._fts_indexed.clear()


def _make_arrow_schema(vector_dim: int):
    import pyarrow as pa

    return pa.schema(
        [
            pa.field("id", pa.string()),
            pa.field("collection", pa.string()),
            pa.field("text", pa.string()),
            pa.field("source_url", pa.string()),
            pa.field("metadata_json", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), vector_dim)),
        ]
    )


def _quoted_id_filter(ids: List[str]) -> str:
    """Build a LanceDB-safe ``id IN (...)`` clause."""
    safe = ", ".join(f"'{i.replace(chr(39), chr(39) * 2)}'" for i in ids)
    return f"id IN ({safe})"


def _build_where_clause(filters: Optional[Dict[str, Any]]) -> Optional[str]:
    """Translate a simple ``{key: value}`` dict into a LanceDB SQL ``WHERE``.

    Filters live in :class:`Chunk.metadata`, so we filter via the
    ``metadata_json`` LIKE pattern. This is intentionally simple — the eval
    harness only needs equality filters; richer predicates can come later.
    """
    if not filters:
        return None
    clauses: List[str] = []
    for key, val in filters.items():
        # Match `"key": value` literal in the JSON string.
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            needle = f'"{key}": {val}'
        elif isinstance(val, bool):
            needle = f'"{key}": {str(val).lower()}'
        else:
            safe = str(val).replace("'", "''")
            needle = f'"{key}": "{safe}"'
        clauses.append(f"metadata_json LIKE '%{needle}%'")
    return " AND ".join(clauses) if clauses else None


def _safe_search(table, query, *, k: int, where: Optional[str], fts: bool = False) -> List[Dict[str, Any]]:
    """Run a vector or FTS search and return rows as dicts.

    Wraps LanceDB's fluent API and normalizes the score column to a
    ``_score`` key (vector → ``_distance`` becomes negative cosine; we
    convert later).
    """
    q = table.search(query) if fts else table.search(query)
    if where:
        try:
            q = q.where(where)
        except Exception:
            pass
    try:
        rows = q.limit(k).to_list()
    except Exception:
        rows = q.limit(k).to_pandas().to_dict("records")
    return rows


def _hybrid_merge(
    vector_hits: List[Dict[str, Any]],
    lex_hits: List[Dict[str, Any]],
    *,
    vector_weight: float,
    lexical_weight: float,
) -> List[Dict[str, Any]]:
    """Merge two ranked result lists by weighted reciprocal-rank score.

    Reciprocal-rank fusion (RRF) handles disparate score scales cleanly —
    cosine distances and BM25 raw scores aren't directly comparable, but
    rank position is. Constant 60 is the canonical RRF constant.
    """
    K = 60.0
    by_id: Dict[str, Dict[str, Any]] = {}
    for rank, row in enumerate(vector_hits):
        rid = row.get("id")
        if not rid:
            continue
        contribution = vector_weight * (1.0 / (K + rank))
        existing = by_id.get(rid)
        if existing is None:
            by_id[rid] = {**row, "_score": contribution}
        else:
            existing["_score"] += contribution
    for rank, row in enumerate(lex_hits):
        rid = row.get("id")
        if not rid:
            continue
        contribution = lexical_weight * (1.0 / (K + rank))
        existing = by_id.get(rid)
        if existing is None:
            by_id[rid] = {**row, "_score": contribution}
        else:
            existing["_score"] = existing.get("_score", 0.0) + contribution
    return sorted(by_id.values(), key=lambda r: r["_score"], reverse=True)


# ---------------------------------------------------------------------------
# Module-level convenience wrappers (most callers use these, not the class)
# ---------------------------------------------------------------------------


def get_retriever() -> Retriever:
    """Return the process-wide singleton."""
    global _DEFAULT_RETRIEVER
    if _DEFAULT_RETRIEVER is None:
        with _RETRIEVER_LOCK:
            if _DEFAULT_RETRIEVER is None:
                _DEFAULT_RETRIEVER = Retriever()
    return _DEFAULT_RETRIEVER


def configure_default_retriever(retriever: Retriever) -> None:
    """Pin the singleton (tests use this to inject a tmp-dir Retriever)."""
    global _DEFAULT_RETRIEVER
    with _RETRIEVER_LOCK:
        _DEFAULT_RETRIEVER = retriever


def reset_default_retriever() -> None:
    """Drop the singleton — tests call this between cases."""
    global _DEFAULT_RETRIEVER
    with _RETRIEVER_LOCK:
        _DEFAULT_RETRIEVER = None


def retrieve(
    query: str,
    collection: CollectionName,
    *,
    k: int = 8,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Chunk]:
    """The public retrieval API. Every consumer goes through here."""
    return get_retriever().retrieve(query, collection=collection, k=k, filters=filters)


# ---------------------------------------------------------------------------
# Ingest helpers — one per collection
# ---------------------------------------------------------------------------


def _id(prefix: str, *parts: Any) -> str:
    h = hashlib.sha1("::".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"


def ingest_doc(path: str, text: str, *, retriever: Optional[Retriever] = None) -> int:
    """Chunk + embed + insert a single doc into the ``docs`` collection."""
    r = retriever or get_retriever()
    chunks = [
        Chunk(
            id=_id("doc", path, i),
            collection="docs",
            text=chunk_text,
            source_url=path,
            metadata={"path": path, "chunk_index": i},
        )
        for i, chunk_text in enumerate(chunk_markdown(text))
    ]
    return r.ingest(chunks)


def reindex_docs(
    docs_root: str,
    *,
    retriever: Optional[Retriever] = None,
) -> int:
    """Re-embed every ``*.md`` under ``docs_root`` into the ``docs`` collection."""
    import glob

    n = 0
    for path in glob.glob(os.path.join(docs_root, "**", "*.md"), recursive=True):
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        n += ingest_doc(path, text, retriever=retriever)
    return n


def ingest_profile(
    profile: Any,
    *,
    query: str,
    retriever: Optional[Retriever] = None,
) -> int:
    """Insert an :class:`ArticleProfile` into the ``profiles`` collection.

    The profile is collapsed to a small structured document — enough to be
    retrievable by query, but not the full HTML (the SERP-profiles cache
    table from PR #5a holds the raw extraction).
    """
    text_parts = [
        profile.title,
        " | ".join(profile.h2_headings or []),
        profile.meta_description or "",
    ]
    text = "\n".join(p for p in text_parts if p)
    chunk = Chunk(
        id=_id("profile", profile.url, query),
        collection="profiles",
        text=text,
        source_url=profile.url,
        metadata={
            "url": profile.url,
            "query": query,
            "word_count": profile.word_count,
            "section_count": profile.section_count,
            "has_faq": profile.has_faq,
            "has_comparison_table": profile.has_comparison_table,
        },
    )
    r = retriever or get_retriever()
    return r.ingest([chunk])


def ingest_research(
    article_id: int,
    harvest: Any,
    *,
    retriever: Optional[Retriever] = None,
) -> int:
    """Insert the Research crew's stage-0 output into ``research_harvest``."""
    if harvest is None:
        return 0
    if isinstance(harvest, str):
        text = harvest
    else:
        try:
            text = json.dumps(harvest, default=str)
        except (TypeError, ValueError):
            text = str(harvest)
    r = retriever or get_retriever()
    chunks = [
        Chunk(
            id=_id("research", article_id, i),
            collection="research_harvest",
            text=chunk_text,
            source_url=f"article://{article_id}",
            metadata={"article_id": article_id, "chunk_index": i},
        )
        for i, chunk_text in enumerate(chunk_markdown(text))
    ]
    return r.ingest(chunks)


def ingest_own_article(
    article_id: int,
    title: str,
    body: str,
    *,
    niche_id: Optional[int] = None,
    published_url: str = "",
    retriever: Optional[Retriever] = None,
) -> int:
    """Insert one of our own published articles into ``own_articles``."""
    text = f"{title}\n\n{_strip_html(body)}"
    r = retriever or get_retriever()
    chunks = [
        Chunk(
            id=_id("own", article_id, i),
            collection="own_articles",
            text=chunk_text,
            source_url=published_url or f"article://{article_id}",
            metadata={
                "article_id": article_id,
                "niche_id": niche_id,
                "chunk_index": i,
            },
        )
        for i, chunk_text in enumerate(chunk_markdown(text))
    ]
    return r.ingest(chunks)


__all__ = [
    "Chunk",
    "CollectionName",
    "COLLECTIONS",
    "DEFAULT_VECTOR_DIM",
    "Embedder",
    "Retriever",
    "chunk_markdown",
    "chunk_html",
    "configure_default_retriever",
    "get_retriever",
    "ingest_doc",
    "ingest_own_article",
    "ingest_profile",
    "ingest_research",
    "make_hash_embedder",
    "make_openai_embedder",
    "reindex_docs",
    "reset_default_retriever",
    "retrieve",
]
