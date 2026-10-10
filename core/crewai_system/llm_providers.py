"""LLM provider selection for CrewAI agents (PR #22).

``CONTENT_LLM_PROVIDER`` picks the model behind the content-writing agents:

- ``openai`` (default): returns ``None`` so CrewAI keeps its existing
  default (OPENAI_API_KEY / gpt-4o-mini) — zero behaviour change.
- ``meta``: Meta Model API (Muse Spark) via its OpenAI-compatible endpoint.
  LiteLLM's ``openai/`` prefix routes to any OpenAI-compatible base URL.

The contributor tier (prompts used to improve Meta products) is refused
unless ``META_ALLOW_CONTRIBUTOR_TIER=true``.

Author agent (Oct 9, 2026 decision): ``author_llm_kwargs()`` moves only the
author agent to Muse Spark, and only after the overseer layer has verified
the whole system (``src/overseers/author_model_gate.py``). Until then it
returns ``{}`` so the author keeps the current default. ``AUTHOR_LLM_PROVIDER``
can be ``gated`` (default), ``default`` (never switch) or ``meta`` (force).
``CONTENT_LLM_PROVIDER=meta`` still forces the whole content crew to Meta.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import os
from typing import Iterator, Optional


_CURRENT_ARTICLE_ID: ContextVar[Optional[int]] = ContextVar(
    "current_crewai_article_id", default=None
)


@contextmanager
def track_content_generation(article_id: Optional[int]) -> Iterator[None]:
    token = _CURRENT_ARTICLE_ID.set(article_id)
    try:
        yield
    finally:
        _CURRENT_ARTICLE_ID.reset(token)


def _cost_meter_callback(model: str) -> object:
    from litellm.integrations.custom_logger import CustomLogger

    class CostMeterCallback(CustomLogger):
        def log_success_event(self, kwargs, response_obj, start_time, end_time):
            article_id = _CURRENT_ARTICLE_ID.get()
            if article_id is None:
                return
            usage = (
                response_obj.get("usage")
                if isinstance(response_obj, dict)
                else getattr(response_obj, "usage", None)
            )
            if usage is None:
                usage = (getattr(response_obj, "model_extra", None) or {}).get("usage")
            if isinstance(usage, dict):
                prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
                completion_tokens = usage.get(
                    "completion_tokens", usage.get("output_tokens")
                )
            else:
                prompt_tokens = getattr(usage, "prompt_tokens", None)
                completion_tokens = getattr(usage, "completion_tokens", None)
            if prompt_tokens is None or completion_tokens is None:
                return

            from src.services.cost_meter import CostMeter

            CostMeter.record(
                article_id,
                "crewai_generation",
                model,
                int(prompt_tokens),
                int(completion_tokens),
            )

    return CostMeterCallback()


def _meta_llm() -> object:
    model = os.getenv("META_TEXT_MODEL", "muse-spark-1.3")
    if model.endswith("-contributor") and os.getenv("META_ALLOW_CONTRIBUTOR_TIER", "").lower() != "true":
        raise RuntimeError(f"{model} requires META_ALLOW_CONTRIBUTOR_TIER=true")
    from crewai import LLM  # lazy: keeps this module importable without CrewAI

    return LLM(
        model=f"openai/{model}",
        base_url=os.getenv("META_MODEL_API_BASE", "https://api.meta.ai/v1"),
        api_key=os.getenv("META_MODEL_API_KEY"),
        temperature=float(os.getenv("META_TEXT_TEMPERATURE", "0.6")),
        is_litellm=True,
        callbacks=[_cost_meter_callback(model)],
    )


def get_content_llm() -> Optional[object]:
    provider = (os.getenv("CONTENT_LLM_PROVIDER") or "openai").lower()
    if provider != "meta":
        return None
    return _meta_llm()


def _author_provider() -> str:
    """``meta`` once the author-model gate has switched, else ``default``.

    Any failure to read the gate (no app context, DB down) keeps the default:
    the cheaper model is the safe fallback.
    """
    mode = (os.getenv("AUTHOR_LLM_PROVIDER") or "gated").lower()
    if mode == "meta":
        return "meta"
    if mode == "default":
        return "default"
    try:
        from src.overseers.author_model_gate import current_author_provider

        return current_author_provider()
    except Exception:
        return "default"


def get_author_llm() -> Optional[object]:
    if (os.getenv("CONTENT_LLM_PROVIDER") or "openai").lower() == "meta":
        return _meta_llm()
    return _meta_llm() if _author_provider() == "meta" else None


def author_llm_kwargs() -> dict:
    """``Agent(**author_llm_kwargs())`` for the author agent only."""
    llm = get_author_llm()
    return {"llm": llm} if llm is not None else {}


def llm_kwargs() -> dict:
    """``Agent(**llm_kwargs())`` — empty dict when the default provider is in use."""
    llm = get_content_llm()
    return {"llm": llm} if llm is not None else {}


__all__ = ["author_llm_kwargs", "get_author_llm", "get_content_llm", "llm_kwargs", "track_content_generation"]
