"""Editorial contracts shared between EditorCrew, BlogCreationFlow, and the API.

Two dataclass families live here:

- ``editorial_verdict`` — what the Editor emits about an article.
- ``blueprint``         — what the Editor measures the article against.

Both are pure-data, JSON-serializable, and deliberately framework-free.
"""

from core.crewai_system.contracts.editorial_verdict import (
    AxisReport,
    EditorialVerdict,
)
from core.crewai_system.contracts.blueprint import Blueprint, load_stub_blueprint

__all__ = [
    "AxisReport",
    "EditorialVerdict",
    "Blueprint",
    "load_stub_blueprint",
]
