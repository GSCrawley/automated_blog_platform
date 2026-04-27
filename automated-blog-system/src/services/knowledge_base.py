"""Knowledge Base shim (PR #5b — token-overlap retired).

The naive token-overlap retriever lived here through PR #5a. PR #5b moves
all retrieval to :mod:`src.services.retrieval` (LanceDB hybrid search). The
public surface of this module — ``KnowledgeBase`` / ``KBChunk`` /
``get_kb()`` — is preserved for backwards compatibility with existing
CrewAI agents and the legacy ``test_knowledge_base.py`` smoke test.

To migrate a caller, switch from::

    from src.services.knowledge_base import get_kb
    kb = get_kb()
    hits = kb.retrieve(query, k=5)

to::

    from src.services.retrieval import retrieve
    chunks = retrieve(query, "docs", k=5)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

DOCS_ROOT = Path(__file__).resolve().parents[3] / "docs"


@dataclass
class KBChunk:
    """Legacy chunk shape. Retained so the old test contract still type-checks.

    Populated only via the legacy ``load()`` + ``retrieve()`` path, which
    PR #5b made a no-op. New code should use :class:`Chunk` from
    :mod:`src.services.retrieval` instead.
    """

    doc_path: Path
    section_title: str
    content: str
    tokens: List[str] = field(default_factory=list)
    category: Optional[str] = None
    lever: Optional[str] = None
    applies_to: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    priority: int = 3
    version: str = "v0"


class KnowledgeBase:
    """Backwards-compatible facade over :mod:`retrieval`.

    Calling ``load()`` + ``retrieve()`` returns the same shape the old
    token-overlap implementation did, but the actual lookup goes through
    LanceDB. Tests and CrewAI agents that imported ``KnowledgeBase``
    continue to function without changes.
    """

    def __init__(self, root: Path = DOCS_ROOT):
        self.root = root
        self.chunks: List[KBChunk] = []  # always empty under the shim
        self._loaded = False

    def load(self, force: bool = False) -> None:
        """No-op for backwards compatibility.

        The new pipeline ingests ``/docs`` via
        :func:`src.services.retrieval.reindex_docs` at startup; calling
        ``load()`` here just flips the readiness flag without re-ingesting.
        """
        self._loaded = True

    def is_ready(self) -> bool:
        return self._loaded

    def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_agent: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Delegate to :func:`src.services.retrieval.retrieve` and reshape
        the result to match the old envelope.

        ``filter_agent`` and ``category`` are honored when the new
        ``Chunk.metadata`` carries those keys; otherwise ignored.
        """
        from src.services.retrieval import retrieve as _retrieve  # noqa: WPS433

        filters: Dict[str, Any] = {}
        if filter_agent:
            filters["filter_agent"] = filter_agent
        if category:
            filters["category"] = category

        try:
            chunks = _retrieve(query, "docs", k=k, filters=filters or None)
        except Exception:
            return []

        return [
            {
                "score": str(round(c.score, 4)),
                "path": (c.metadata or {}).get("path", c.source_url),
                "title": (c.metadata or {}).get("section_title", "")
                or c.text.splitlines()[0][:80] if c.text else "",
                "snippet": c.text[:240],
                "category": (c.metadata or {}).get("category"),
                "lever": (c.metadata or {}).get("lever"),
                "applies_to": (c.metadata or {}).get("applies_to", []),
                "tags": (c.metadata or {}).get("tags", []),
                "priority": (c.metadata or {}).get("priority", 3),
                "version": (c.metadata or {}).get("version", "v0"),
            }
            for c in chunks
        ]


# Singleton accessor — preserved for legacy callers.
_kb: Optional[KnowledgeBase] = None


def get_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
        _kb.load()
    return _kb


__all__ = ["KnowledgeBase", "get_kb", "KBChunk"]
