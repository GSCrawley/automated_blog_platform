"""LLM provider selection for CrewAI agents (PR #22).

``CONTENT_LLM_PROVIDER`` picks the model behind the content-writing agents:

- ``openai`` (default): returns ``None`` so CrewAI keeps its existing
  default (OPENAI_API_KEY / gpt-4o-mini) — zero behaviour change.
- ``meta``: Meta Model API (Muse Spark) via its OpenAI-compatible endpoint.
  LiteLLM's ``openai/`` prefix routes to any OpenAI-compatible base URL.

The contributor tier (prompts used to improve Meta products) is refused
unless ``META_ALLOW_CONTRIBUTOR_TIER=true``.
"""
from __future__ import annotations

import os
from typing import Optional


def get_content_llm() -> Optional[object]:
    provider = (os.getenv("CONTENT_LLM_PROVIDER") or "openai").lower()
    if provider != "meta":
        return None
    model = os.getenv("META_TEXT_MODEL", "muse-spark-1.3")
    if model.endswith("-contributor") and os.getenv("META_ALLOW_CONTRIBUTOR_TIER", "").lower() != "true":
        raise RuntimeError(f"{model} requires META_ALLOW_CONTRIBUTOR_TIER=true")
    from crewai import LLM  # lazy: keeps this module importable without CrewAI

    return LLM(
        model=f"openai/{model}",
        base_url=os.getenv("META_MODEL_API_BASE", "https://api.meta.ai/v1"),
        api_key=os.getenv("META_MODEL_API_KEY"),
        temperature=float(os.getenv("META_TEXT_TEMPERATURE", "0.6")),
    )


def llm_kwargs() -> dict:
    """``Agent(**llm_kwargs())`` — empty dict when the default provider is in use."""
    llm = get_content_llm()
    return {"llm": llm} if llm is not None else {}


__all__ = ["get_content_llm", "llm_kwargs"]
