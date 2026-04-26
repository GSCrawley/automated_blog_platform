"""LLM rate card (PR #3).

Per-1K-token prices in **USD**. Sourced from public OpenAI pricing as of
2026-04 — when prices change, edit this file (the only place rates live).

Embedding models charge for input tokens only; their ``completion`` cost is
``Decimal("0")``.

If a model name isn't in the card, :func:`cost_for_call` raises so we
*notice* missing entries rather than silently logging $0 spend.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Dict, NamedTuple


class Rate(NamedTuple):
    prompt_per_1k: Decimal
    completion_per_1k: Decimal


# Defensive copy on read — the dict is read-only at use sites, but keep it
# private to make that obvious.
_RATES: Dict[str, Rate] = {
    # OpenAI chat
    "gpt-4o-mini": Rate(Decimal("0.000150"), Decimal("0.000600")),
    "gpt-4o": Rate(Decimal("0.0025"), Decimal("0.01")),
    "gpt-4-turbo": Rate(Decimal("0.01"), Decimal("0.03")),
    "gpt-3.5-turbo": Rate(Decimal("0.0005"), Decimal("0.0015")),
    # OpenAI embeddings
    "text-embedding-3-small": Rate(Decimal("0.00002"), Decimal("0")),
    "text-embedding-3-large": Rate(Decimal("0.00013"), Decimal("0")),
    "text-embedding-ada-002": Rate(Decimal("0.0001"), Decimal("0")),
}


class UnknownModelError(KeyError):
    """Raised when ``cost_for_call`` is asked about an unrated model."""


def cost_for_call(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    """Return the USD cost for a single LLM call.

    Quantized to 6 decimal places so micro-call totals round predictably
    in the database (cost_events.cost_usd is Numeric(10, 6)).
    """
    if model not in _RATES:
        raise UnknownModelError(
            f"Model {model!r} not in rate card; add it to src/services/model_rates.py"
        )
    rate = _RATES[model]
    cost = (
        rate.prompt_per_1k * Decimal(prompt_tokens) / Decimal(1000)
        + rate.completion_per_1k * Decimal(completion_tokens) / Decimal(1000)
    )
    return cost.quantize(Decimal("0.000001"))


def known_models() -> list[str]:
    return sorted(_RATES.keys())


__all__ = ["Rate", "UnknownModelError", "cost_for_call", "known_models"]
