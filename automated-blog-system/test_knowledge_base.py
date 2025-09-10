import os
from pathlib import Path
from src.services.knowledge_base import KnowledgeBase

def test_load_and_retrieve():
    kb = KnowledgeBase()
    kb.load(force=True)
    assert kb.is_ready() or len(kb.chunks) == 0  # Allow empty docs directory
    results = kb.retrieve("marketing optimization", k=3) if kb.is_ready() else []
    if kb.is_ready():
        assert isinstance(results, list)
        # If we have results they should have required keys
        if results:
            for r in results:
                base_keys = {"score", "path", "title", "snippet"}
                assert base_keys.issubset(r.keys())
                # Metadata keys are optional but if present must be non-empty type-wise
                if "applies_to" in r:
                    assert isinstance(r["applies_to"], list)
