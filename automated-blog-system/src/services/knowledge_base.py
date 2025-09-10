"""Knowledge Base service (initial scaffold).

This module will:
- Load seed marketing & niche research documents from /docs
- Build/refresh an in-memory corpus index (placeholder for future vector store)
- Provide simple keyword + naive semantic (lowercased token overlap) retrieval
- Expose a retrieval API for agents and content generation pipeline

Planned extensions:
- Pluggable embedding backend (local model or API)
- Hybrid retrieval (BM25 + dense vectors)
- Ontology / entity graph integration
- Caching & incremental refresh
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Iterable, Optional
import re

DOCS_ROOT = Path(__file__).resolve().parents[3] / "docs"

@dataclass
class KBChunk:
    doc_path: Path
    section_title: str
    content: str
    tokens: List[str]

class KnowledgeBase:
    def __init__(self, root: Path = DOCS_ROOT):
        self.root = root
        self.chunks: List[KBChunk] = []
        self._loaded = False

    def load(self, force: bool = False) -> None:
        if self._loaded and not force:
            return
        self.chunks.clear()
        for path in self._iter_doc_files():
            self._index_file(path)
        self._loaded = True

    def _iter_doc_files(self) -> Iterable[Path]:
        if not self.root.exists():
            return []
        for p in self.root.rglob("*.md"):
            yield p

    def _index_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Split on headings (simple heuristic)
        sections = re.split(r"^#+ ", text, flags=re.MULTILINE)
        if not sections:
            return
        # First chunk: pre-heading preamble if any
        for raw in sections:
            raw = raw.strip()
            if not raw:
                continue
            # Extract first line as title surrogate
            lines = raw.splitlines()
            title = lines[0][:80]
            body = "\n".join(lines[1:]) if len(lines) > 1 else ""
            tokens = self._tokenize(raw)
            self.chunks.append(KBChunk(doc_path=path, section_title=title, content=body, tokens=tokens))

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def is_ready(self) -> bool:
        return self._loaded and len(self.chunks) > 0

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        if not self.is_ready():
            raise RuntimeError("KnowledgeBase not loaded. Call load() first.")
        q_tokens = set(self._tokenize(query))
        scored = []
        for ch in self.chunks:
            overlap = len(q_tokens.intersection(ch.tokens))
            if overlap == 0:
                continue
            scored.append((overlap, ch))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, ch in scored[:k]:
            results.append({
                "score": str(score),
                "path": str(ch.doc_path.relative_to(self.root)),
                "title": ch.section_title,
                "snippet": ch.content[:240]
            })
        return results

# Singleton accessor (lightweight) -------------------------------------------------
_kb: Optional[KnowledgeBase] = None

def get_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
        _kb.load()
    return _kb

__all__ = ["KnowledgeBase", "get_kb", "KBChunk"]
