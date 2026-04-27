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

from dataclasses import dataclass, field
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
    # New metadata fields (ontology-aligned; may be None if not parsed)
    category: Optional[str] = None
    lever: Optional[str] = None
    applies_to: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    priority: int = 3
    version: str = "v0"

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
            meta = self._extract_metadata(raw)
            self.chunks.append(KBChunk(
                doc_path=path,
                section_title=title,
                content=body,
                tokens=tokens,
                category=meta.get("category"),
                lever=meta.get("lever"),
                applies_to=meta.get("applies_to", []),
                tags=meta.get("tags", []),
                priority=meta.get("priority", 3),
                version=meta.get("version", "v0")
            ))

    def _extract_metadata(self, section_text: str) -> Dict[str, any]:
        """Very lightweight metadata pattern extractor.

        Patterns (case-insensitive) inside section lines:
        Category: <value>
        Lever: <value>
        Applies-To: AgentA, AgentB
        Tags: tag1, tag2
        Priority: 1-5
        Version: vX
        """
        meta: Dict[str, any] = {}
        for line in section_text.splitlines()[:12]:  # scan only first few lines
            lower = line.lower()
            if lower.startswith("category:"):
                meta["category"] = line.split(":",1)[1].strip()
            elif lower.startswith("lever:"):
                meta["lever"] = line.split(":",1)[1].strip()
            elif lower.startswith("applies-to:"):
                agents = line.split(":",1)[1]
                meta["applies_to"] = [a.strip() for a in agents.split(",") if a.strip()]
            elif lower.startswith("tags:"):
                tags = line.split(":",1)[1]
                meta["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
            elif lower.startswith("priority:"):
                try:
                    meta["priority"] = int(line.split(":",1)[1].strip())
                except ValueError:
                    pass
            elif lower.startswith("version:"):
                meta["version"] = line.split(":",1)[1].strip()
        return meta

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def is_ready(self) -> bool:
        return self._loaded and len(self.chunks) > 0

    def retrieve(self, query: str, k: int = 5, filter_agent: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, str]]:
        if not self.is_ready():
            raise RuntimeError("KnowledgeBase not loaded. Call load() first.")
        q_tokens = set(self._tokenize(query))
        scored = []
        for ch in self.chunks:
            if filter_agent and filter_agent not in ch.applies_to and ch.applies_to:
                continue
            if category and ch.category and ch.category.lower() != category.lower():
                continue
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
                "snippet": ch.content[:240],
                "category": ch.category,
                "lever": ch.lever,
                "applies_to": ch.applies_to,
                "tags": ch.tags,
                "priority": ch.priority,
                "version": ch.version
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
