"""Meta Model API client (Muse Spark text, Muse Image) — PR #21.

The Meta Model API is OpenAI-compatible (base URL ``https://api.meta.ai/v1``),
so this is a thin ``requests`` client rather than a new SDK dependency.
Every call is metered through :class:`CostMeter` so Meta spend counts
against the same $100/month cap as OpenAI spend.

Tier choice is a data-governance decision, not a price optimisation:

- ``muse-spark-1.3`` (default): prompts are *not* used to improve Meta's
  products.
- ``muse-spark-1.3-contributor``: ~12x cheaper, but prompts *are* used to
  improve Meta's products. Opt-in only via ``META_ALLOW_CONTRIBUTOR_TIER=true``.

Env:
    META_MODEL_API_KEY            bearer token
    META_MODEL_API_BASE           default https://api.meta.ai/v1
    META_TEXT_MODEL               default muse-spark-1.3
    META_IMAGE_MODEL              default muse-image-1.0
    META_ALLOW_CONTRIBUTOR_TIER   default false
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

import requests

DEFAULT_BASE = "https://api.meta.ai/v1"
DEFAULT_TEXT_MODEL = "muse-spark-1.3"
DEFAULT_IMAGE_MODEL = "muse-image-1.0"
IMAGE_PRICE_USD = Decimal("0.01")  # Muse Image, per image


class MetaModelError(RuntimeError):
    pass


@dataclass
class ChatResult:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: Decimal
    raw: Dict[str, Any]


class MetaModelClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        text_model: Optional[str] = None,
        image_model: Optional[str] = None,
        http: Optional[requests.Session] = None,
        meter: bool = True,
    ) -> None:
        self.api_key = api_key or os.getenv("META_MODEL_API_KEY", "")
        self.base_url = (base_url or os.getenv("META_MODEL_API_BASE") or DEFAULT_BASE).rstrip("/")
        self.text_model = text_model or os.getenv("META_TEXT_MODEL") or DEFAULT_TEXT_MODEL
        self.image_model = image_model or os.getenv("META_IMAGE_MODEL") or DEFAULT_IMAGE_MODEL
        self.http = http or requests.Session()
        self.meter = meter
        if self.text_model.endswith("-contributor") and os.getenv("META_ALLOW_CONTRIBUTOR_TIER", "").lower() != "true":
            raise MetaModelError(
                f"{self.text_model} sends prompts to Meta for product improvement; "
                "set META_ALLOW_CONTRIBUTOR_TIER=true to opt in."
            )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise MetaModelError("META_MODEL_API_KEY is not set")
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        article_id: Optional[int] = None,
        stage: str = "meta_content",
        model: Optional[str] = None,
        **params: Any,
    ) -> ChatResult:
        model = model or self.text_model
        resp = self.http.post(
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json={"model": model, "messages": messages, **params},
            timeout=120,
        )
        if resp.status_code >= 400:
            raise MetaModelError(f"Meta chat {resp.status_code}: {resp.text[:300]}")
        body = resp.json()
        usage = body.get("usage") or {}
        pt, ct = int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
        text = ((body.get("choices") or [{}])[0].get("message") or {}).get("content", "")
        cost = self._meter(article_id, stage, model, pt, ct)
        return ChatResult(text=text, model=model, prompt_tokens=pt, completion_tokens=ct, cost_usd=cost, raw=body)

    def generate_image(
        self,
        prompt: str,
        *,
        article_id: Optional[int] = None,
        stage: str = "meta_image",
        size: str = "1024x1024",
        n: int = 1,
    ) -> Dict[str, Any]:
        resp = self.http.post(
            f"{self.base_url}/images/generations",
            headers=self._headers(),
            json={"model": self.image_model, "prompt": prompt, "size": size, "n": n},
            timeout=180,
        )
        if resp.status_code >= 400:
            raise MetaModelError(f"Meta image {resp.status_code}: {resp.text[:300]}")
        body = resp.json()
        if self.meter:
            from src.services.cost_meter import CostMeter

            CostMeter.record_flat(article_id, stage, self.image_model, IMAGE_PRICE_USD * n)
        # Flag for downstream ad/compliance use: this media is AI-generated.
        body["ai_generated"] = True
        return body

    def _meter(self, article_id: Optional[int], stage: str, model: str, pt: int, ct: int) -> Decimal:
        if not self.meter:
            from src.services.model_rates import cost_for_call

            return cost_for_call(model, pt, ct)
        from src.services.cost_meter import CostMeter

        return CostMeter.record(article_id, stage, model, pt, ct)


__all__ = ["MetaModelClient", "MetaModelError", "ChatResult"]
