"""Market Overseer — embodies the *Automated E-commerce Research* function.

Mandate: make sure the pipeline is writing about products that can actually
earn — in-strategy price points, real affiliate destinations, healthy niche
pipelines — before tokens are spent on them.
"""
from __future__ import annotations

from typing import List

from src.models.niche import Niche
from src.models.product import Article, Product
from src.overseers.base import ActionSpec, BaseOverseer, Finding

MSRP_FLOOR_USD = 500.0  # GOALS.md: research trending products with MSRP >= $500


class MarketOverseer(BaseOverseer):
    name = "market"
    function = "Automated E-commerce Research"
    mandate = (
        "Keep the product set on-strategy (MSRP >= $500, real affiliate links) "
        "and the niche pipelines healthy."
    )

    def sense(self) -> List[Finding]:
        out: List[Finding] = []
        for n in Niche.query.filter(Niche.active.is_(True)).all():
            if (n.pipeline_status or "") == "error":
                out.append(
                    Finding(
                        code="niche_pipeline_error",
                        title=f"Niche '{n.name}' pipeline is in error",
                        severity="high",
                        detail=(n.pipeline_message or "")[:500],
                        subject_type="niche",
                        subject_id=str(n.id),
                        actions=[ActionSpec("notify_human", {"niche_id": n.id}, risk="auto")],
                    )
                )

        for p in Product.query.all():
            live_or_pending = Article.query.filter(Article.product_id == p.id).filter(Article.status != "archived").count()
            if not live_or_pending:
                continue
            if p.price is not None and p.price < MSRP_FLOOR_USD:
                out.append(
                    Finding(
                        code="below_msrp_floor",
                        title=f"Product {p.id} '{p.name}' is ${p.price:.0f}, below the ${MSRP_FLOOR_USD:.0f} floor",
                        severity="medium",
                        detail="Off-strategy for a high-ticket affiliate site; commissions will not cover cost.",
                        evidence={"price": p.price, "articles": live_or_pending},
                        subject_type="product",
                        subject_id=str(p.id),
                        actions=[ActionSpec("notify_human", {"product_id": p.id}, risk="auto")],
                    )
                )
            if not p.affiliate_url or not p.tracking_id:
                out.append(
                    Finding(
                        code="product_not_monetized",
                        title=f"Product {p.id} '{p.name}' has no affiliate URL or tracking ID",
                        severity="high",
                        detail="Articles for this product cannot earn and cannot be attributed.",
                        evidence={"affiliate_url": p.affiliate_url, "tracking_id": p.tracking_id},
                        subject_type="product",
                        subject_id=str(p.id),
                        actions=[ActionSpec("notify_human", {"product_id": p.id}, risk="auto")],
                    )
                )
        return out


__all__ = ["MarketOverseer", "MSRP_FLOOR_USD"]
