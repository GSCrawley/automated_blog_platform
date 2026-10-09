"""Compliance Overseer — cross-cutting guardrail for all five functions.

Mandate: protect the accounts the revenue depends on (Amazon Associates,
Google Search, Meta Ads). It checks invariants and disclosures; it never
edits content itself.

Rules enforced
--------------
- Publish gate invariant: nothing live without ``editorial_verdict == PUBLISH``.
- Amazon Operating Agreement s.5: the site must state "As an Amazon
  Associate I earn from qualifying purchases."  FTC link-level disclosure
  is also required near affiliate links.
- Amazon Commission Income Statement (Apr 14 2026 update): purchases
  referred by paid/boosted ads *linking to Amazon* are disqualified, so any
  Meta campaign must point at the blog, never at Amazon or a redirect.
"""
from __future__ import annotations

import os
import re
from typing import List
from urllib.parse import urlparse

from src.models.overseer import OverseerAction
from src.models.product import Article
from src.overseers.base import ActionSpec, BaseOverseer, Finding

AMAZON_DISCLOSURE = re.compile(r"as an amazon associate,? i earn from qualifying purchases", re.I)
LINK_DISCLOSURE = re.compile(r"(affiliate|commission|paid link|#ad\b|#commissionsearned)", re.I)
AMAZON_SHORT_HOSTS = {"amzn.to", "amzn.com", "amzn.eu", "a.co"}


def is_amazon_url(url: str) -> bool:
    """True for amazon.<tld> (any subdomain) and Amazon short-link hosts."""
    host = (urlparse(url or "").hostname or "").lower()
    if not host:
        return False
    if host in AMAZON_SHORT_HOSTS or any(host.endswith("." + h) for h in AMAZON_SHORT_HOSTS):
        return True
    labels = host.split(".")
    return "amazon" in labels[:-1]


class ComplianceOverseer(BaseOverseer):
    name = "compliance"
    function = "Cross-cutting compliance"
    mandate = "Protect the Amazon, Google and Meta accounts the revenue depends on."

    def sense(self) -> List[Finding]:
        out: List[Finding] = []
        site_disclosure = os.getenv("SITE_AFFILIATE_DISCLOSURE_PRESENT", "").lower() == "true"
        for a in Article.query.filter(Article.status == "published").all():
            if (a.editorial_verdict or "").upper() != "PUBLISH":
                out.append(
                    Finding(
                        code="publish_gate_bypassed",
                        title=f"Article {a.id} is live with verdict {a.editorial_verdict!r}",
                        severity="critical",
                        category="compliance",
                        detail="Invariant violated: only PUBLISH articles may reach Ghost.",
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[ActionSpec("unpublish_article", {"article_id": a.id})],
                    )
                )
            html = a.content or ""
            amazon_linked = "amazon." in html.lower() or "amzn.to" in html.lower() or (
                a.product is not None and is_amazon_url(a.product.affiliate_url or "")
            )
            if amazon_linked and not (AMAZON_DISCLOSURE.search(html) or site_disclosure):
                out.append(
                    Finding(
                        code="missing_amazon_disclosure",
                        title=f"Article {a.id} links to Amazon without the required Associate statement",
                        severity="critical",
                        category="compliance",
                        detail=(
                            'Add "As an Amazon Associate I earn from qualifying purchases." '
                            "to the article or the site template (then set "
                            "SITE_AFFILIATE_DISCLOSURE_PRESENT=true)."
                        ),
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[ActionSpec("notify_human", {"article_id": a.id}, risk="auto")],
                    )
                )
            if amazon_linked and not LINK_DISCLOSURE.search(html):
                out.append(
                    Finding(
                        code="missing_link_disclosure",
                        title=f"Article {a.id} has no link-level affiliate disclosure",
                        severity="high",
                        category="compliance",
                        subject_type="article",
                        subject_id=str(a.id),
                        actions=[ActionSpec("notify_human", {"article_id": a.id}, risk="auto")],
                    )
                )

        for act in OverseerAction.query.filter(OverseerAction.kind == "create_meta_campaign_draft").all():
            dest = act.params.get("destination_url", "")
            if is_amazon_url(dest) and act.status in ("proposed", "approved"):
                out.append(
                    Finding(
                        code="paid_ad_links_to_amazon",
                        title=f"Meta campaign draft (action {act.id}) points directly at Amazon",
                        severity="critical",
                        category="compliance",
                        detail="Amazon disqualifies purchases referred by paid ads linking to Amazon.",
                        subject_type="overseer_action",
                        subject_id=str(act.id),
                        actions=[ActionSpec("reject_action", {"action_id": act.id}, risk="auto")],
                    )
                )
        return out


__all__ = ["ComplianceOverseer", "is_amazon_url"]
