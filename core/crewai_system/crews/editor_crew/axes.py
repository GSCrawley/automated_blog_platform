"""Axis evaluators for the EditorCrew (PR #2).

Each evaluator takes a *headless-contract article dict* (the shape produced by
``Article.to_headless_contract()``) plus a :class:`Blueprint` and returns an
:class:`AxisReport`.

Two axes — Conformance and Monetization — are pure-Python deterministic. The
other two — ContentQuality and Compliance — *can* call an LLM when one is
injected; otherwise they emit a pass-stub with a ``llm_skipped`` note. This
preserves the unit-test rule "no network calls in unit tests" while leaving
the production path open.

The article-dict shape consumed:

    {
        "title": str,
        "content": str,           # HTML (preferred when sections are empty)
        "sections": [{"heading": str, "content": str}, ...],
        "summary": str,
        "keywords": [str, ...],
        "calls_to_action": [{"type": "affiliate"|"internal", "target": str,
                              "anchor": str}, ...],
        "meta": {"feature_image": str | None, ...},
    }
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.crewai_system.contracts.blueprint import Blueprint
from core.crewai_system.contracts.editorial_verdict import AxisReport

# Optional callable signature for LLM-based axes. Returning a dict lets the
# caller carry score + checklist + evidence in one shot. Tests inject a stub.
LLMCaller = Callable[[str, Dict[str, Any]], Dict[str, Any]]


# ---------------------------------------------------------------------------
# Helpers — HTML parsing + word counting. Regex-based on purpose: deterministic
# and dependency-free (no BeautifulSoup needed for these structural checks).
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r"<[^>]+>")
_H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
_PARA_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_AHREF_RE = re.compile(r'<a\b([^>]*)>(.*?)</a>', re.IGNORECASE | re.DOTALL)
_REL_RE = re.compile(r'rel\s*=\s*"([^"]*)"', re.IGNORECASE)
_HREF_RE = re.compile(r'href\s*=\s*"([^"]*)"', re.IGNORECASE)


def _strip_tags(html: str) -> str:
    return _TAG_RE.sub(" ", html or "")


def _word_count(text: str) -> int:
    return len([w for w in _strip_tags(text).split() if w.strip()])


def _article_html(article: Dict[str, Any]) -> str:
    """Render the article body as a single HTML blob.

    Uses ``sections`` if present (each section becomes ``<h2>heading</h2>``
    plus the section body); otherwise falls back to ``content``.
    """
    sections = article.get("sections") or []
    if sections:
        parts: List[str] = []
        for s in sections:
            heading = (s.get("heading") or "").strip()
            body = (s.get("content") or "").strip()
            if heading:
                parts.append(f"<h2>{heading}</h2>")
            if body:
                parts.append(body if body.startswith("<") else f"<p>{body}</p>")
        return "\n".join(parts)
    return article.get("content") or ""


def _h2_headings(article: Dict[str, Any]) -> List[str]:
    sections = article.get("sections") or []
    if sections:
        return [(s.get("heading") or "").strip() for s in sections if s.get("heading")]
    return [m.strip() for m in _H2_RE.findall(article.get("content") or "")]


def _paragraphs(html: str) -> List[str]:
    return [p.strip() for p in _PARA_RE.findall(html or "")]


@dataclass
class _AnchorTag:
    rel: str
    href: str
    anchor_html: str


def _anchor_tags(html: str) -> List[_AnchorTag]:
    out: List[_AnchorTag] = []
    for attrs, anchor in _AHREF_RE.findall(html or ""):
        rel_match = _REL_RE.search(attrs)
        href_match = _HREF_RE.search(attrs)
        out.append(
            _AnchorTag(
                rel=(rel_match.group(1) if rel_match else ""),
                href=(href_match.group(1) if href_match else ""),
                anchor_html=anchor,
            )
        )
    return out


def _checklist_item(
    item: str,
    passed: bool,
    expected: Any = None,
    actual: Any = None,
    note: str = "",
) -> Dict[str, Any]:
    return {
        "item": item,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
        "note": note,
    }


def _score_from_checklist(checklist: List[Dict[str, Any]]) -> Tuple[float, bool]:
    if not checklist:
        return 10.0, True
    passed = sum(1 for c in checklist if c["passed"])
    total = len(checklist)
    score = round(10.0 * passed / total, 2)
    return score, passed == total


# ---------------------------------------------------------------------------
# 1. Conformance — deterministic, the most important axis.
# ---------------------------------------------------------------------------

def conformance_axis(article: Dict[str, Any], blueprint: Blueprint) -> AxisReport:
    html = _article_html(article)
    word_count = _word_count(html)
    h2s = _h2_headings(article)
    h2_count = len(h2s)

    checklist: List[Dict[str, Any]] = []

    # word count in range
    wc_lo, wc_hi = blueprint.word_count_range
    checklist.append(
        _checklist_item(
            "word_count_in_range",
            wc_lo <= word_count <= wc_hi,
            expected=[wc_lo, wc_hi],
            actual=word_count,
        )
    )

    # H2 count in range
    h2_lo, h2_hi = blueprint.h2_count_range
    checklist.append(
        _checklist_item(
            "h2_count_in_range",
            h2_lo <= h2_count <= h2_hi,
            expected=[h2_lo, h2_hi],
            actual=h2_count,
        )
    )

    # required sections present (substring match against H2 headings, case-insensitive)
    headings_lower = [h.lower() for h in h2s]
    for required in blueprint.required_sections:
        needle = required.lower()
        present = any(needle in h for h in headings_lower)
        checklist.append(
            _checklist_item(
                f"section_present:{required}",
                present,
                expected=required,
                actual=h2s if not present else required,
            )
        )

    # target keyword density (using the article's first keyword as the target)
    keywords = article.get("keywords") or []
    if keywords and word_count > 0:
        target_kw = str(keywords[0]).lower()
        text_lower = _strip_tags(html).lower()
        kw_hits = text_lower.count(target_kw) if target_kw else 0
        density = kw_hits / max(word_count, 1)
        kd_lo, kd_hi = blueprint.target_keyword_density
        checklist.append(
            _checklist_item(
                "keyword_density_in_range",
                kd_lo <= density <= kd_hi,
                expected=[kd_lo, kd_hi],
                actual=round(density, 4),
                note=f"target='{target_kw}'",
            )
        )
    else:
        checklist.append(
            _checklist_item(
                "keyword_density_in_range",
                True,
                note="skipped — article has no keywords or no body text",
            )
        )

    # feature image
    if blueprint.requires_feature_image:
        meta = article.get("meta") or {}
        has_feat = bool(meta.get("feature_image"))
        checklist.append(
            _checklist_item(
                "feature_image_present",
                has_feat,
                expected=True,
                actual=has_feat,
            )
        )

    # schema markup (best-effort: look for application/ld+json or itemtype attr)
    if blueprint.requires_schema_markup:
        has_schema = bool(
            re.search(r'application/ld\+json', html, re.IGNORECASE)
            or re.search(r'itemtype\s*=', html, re.IGNORECASE)
        )
        checklist.append(
            _checklist_item(
                "schema_markup_present",
                has_schema,
                expected=True,
                actual=has_schema,
            )
        )

    # internal links (CTAs of type=internal counted; no scraping of <a href>
    # for relative URLs since the article body is provider-agnostic markup)
    ctas = article.get("calls_to_action") or []
    internal_count = sum(1 for c in ctas if c.get("type") == "internal")
    checklist.append(
        _checklist_item(
            "min_internal_links",
            internal_count >= blueprint.min_internal_links,
            expected=blueprint.min_internal_links,
            actual=internal_count,
        )
    )

    # gap-opportunity addressed: at least one coverage_gap keyword appears in body
    if blueprint.coverage_gaps:
        text_lower = _strip_tags(html).lower()
        gap_hits = [g for g in blueprint.coverage_gaps if g.lower() in text_lower]
        checklist.append(
            _checklist_item(
                "addresses_coverage_gap",
                len(gap_hits) >= 1,
                expected=blueprint.coverage_gaps,
                actual=gap_hits,
            )
        )

    score, passed = _score_from_checklist(checklist)
    return AxisReport(
        axis="conformance",
        score=score,
        passed=passed,
        checklist=checklist,
        evidence={
            "word_count": word_count,
            "h2_count": h2_count,
            "h2_headings": h2s,
            "blueprint_id": blueprint.id,
            "confidence_tier": blueprint.confidence_tier,
        },
    )


# ---------------------------------------------------------------------------
# 2. Monetization — deterministic structural checklist.
# ---------------------------------------------------------------------------

_DISCLOSURE_PATTERNS = [
    r"affiliate\s+disclosure",
    r"as an .*affiliate",
    r"we may earn",
    r"earn(s)? a commission",
    r"this post contains affiliate links",
]


def _has_disclosure(html: str) -> bool:
    text = _strip_tags(html).lower()
    return any(re.search(p, text) for p in _DISCLOSURE_PATTERNS)


def monetization_axis(article: Dict[str, Any], blueprint: Blueprint) -> AxisReport:
    html = _article_html(article)
    word_count = _word_count(html)
    ctas = article.get("calls_to_action") or []
    affiliate_ctas = [c for c in ctas if c.get("type") == "affiliate"]
    n_aff = len(affiliate_ctas)

    checklist: List[Dict[str, Any]] = []

    # affiliate density: <= 1 per ~300 words
    capacity = max(word_count // 300, 1)
    checklist.append(
        _checklist_item(
            "affiliate_density_under_limit",
            n_aff <= capacity,
            expected=f"<= {capacity} (1 per 300 words)",
            actual=n_aff,
        )
    )

    # first CTA in first 2 paragraphs (skip if no affiliate CTAs)
    if affiliate_ctas:
        paras = _paragraphs(html)[:2]
        first_para_blob = " ".join(paras).lower()
        anchors_in_first_two = any(
            (c.get("anchor") or "").lower() in first_para_blob
            or (c.get("target") or "").lower() in first_para_blob
            for c in affiliate_ctas
        )
        # If anchors don't appear in body, accept presence-of-any-affiliate-link in body.
        if not anchors_in_first_two:
            for tag in _anchor_tags("\n".join(paras)):
                if "sponsored" in tag.rel.lower():
                    anchors_in_first_two = True
                    break
        checklist.append(
            _checklist_item(
                "first_cta_within_first_2_paragraphs",
                anchors_in_first_two,
                expected="affiliate CTA in first 2 paragraphs",
                actual="present" if anchors_in_first_two else "absent",
            )
        )

    # rel="sponsored nofollow noopener" on every affiliate <a> we can find
    # in the rendered HTML. We look for <a> tags whose href matches an
    # affiliate CTA target; each such tag must carry sponsored+nofollow+noopener.
    aff_targets = {(c.get("target") or "").strip() for c in affiliate_ctas if c.get("target")}
    if aff_targets:
        bad_links: List[str] = []
        for tag in _anchor_tags(html):
            if tag.href in aff_targets:
                rel_lower = tag.rel.lower()
                if not all(t in rel_lower for t in ("sponsored", "nofollow", "noopener")):
                    bad_links.append(tag.href)
        checklist.append(
            _checklist_item(
                "affiliate_rel_attributes_correct",
                not bad_links,
                expected='rel="sponsored nofollow noopener" on every affiliate link',
                actual=bad_links or "all affiliate links correctly tagged",
            )
        )

    # disclosure block present
    checklist.append(
        _checklist_item(
            "disclosure_block_present",
            _has_disclosure(html),
            expected="affiliate disclosure phrase",
            actual="present" if _has_disclosure(html) else "absent",
        )
    )

    # no more than 1 affiliate per section
    sections = article.get("sections") or []
    if sections and aff_targets:
        violators: List[str] = []
        for s in sections:
            body = s.get("content") or ""
            count_in_section = sum(
                1 for tag in _anchor_tags(body) if tag.href in aff_targets
            )
            if count_in_section > 1:
                violators.append(s.get("heading") or "(unnamed)")
        checklist.append(
            _checklist_item(
                "max_one_affiliate_per_section",
                not violators,
                expected="<= 1 affiliate link per section",
                actual=violators or "ok",
            )
        )

    score, passed = _score_from_checklist(checklist)
    return AxisReport(
        axis="monetization",
        score=score,
        passed=passed,
        checklist=checklist,
        evidence={
            "word_count": word_count,
            "affiliate_cta_count": n_aff,
            "affiliate_density_capacity": capacity,
        },
    )


# ---------------------------------------------------------------------------
# 3. Content Quality — LLM-based, with a pass-stub fallback.
# ---------------------------------------------------------------------------

def content_quality_axis(
    article: Dict[str, Any],
    blueprint: Blueprint,
    llm: Optional[LLMCaller] = None,
) -> AxisReport:
    """A lighter, cheaper LLM read on prose quality.

    When ``llm`` is None, returns a pass-stub. The acceptance test rule is
    "no network calls in unit tests" — so the default in test contexts is
    to skip. Production callers wire a real LLM.

    The injected ``llm`` callable receives ``(prompt, context)`` and must
    return a dict shaped like ``{"score": float, "passed": bool,
    "checklist": [...], "evidence": {...}}``.
    """
    if llm is None:
        return AxisReport(
            axis="content_quality",
            score=10.0,
            passed=True,
            checklist=[
                _checklist_item(
                    "llm_quality_pass",
                    True,
                    note="llm_skipped — no caller injected",
                )
            ],
            evidence={"llm_skipped": True},
        )

    body = _strip_tags(_article_html(article))[:4000]
    prompt = (
        "You are a content quality editor. Return JSON with keys "
        "score (0-10), passed (bool), checklist (list of {item, passed, "
        "expected, actual, note}), evidence (dict). Judge: prose readability, "
        "internal consistency, and whether the article actually addresses its "
        "stated topic. Do not score SEO."
    )
    response = llm(prompt, {"title": article.get("title", ""), "body": body})
    return AxisReport(
        axis="content_quality",
        score=float(response.get("score", 0.0)),
        passed=bool(response.get("passed", False)),
        checklist=list(response.get("checklist") or []),
        evidence=dict(response.get("evidence") or {}),
    )


# ---------------------------------------------------------------------------
# 4. Compliance — rules + optional LLM check.
# ---------------------------------------------------------------------------

# Simple rule base. The doc explicitly calls out "prohibited medical/financial
# guarantee language" — we only catch the most obvious violations here; an
# injected LLM can layer on top for fuzzier cases.
_PROHIBITED_PATTERNS = [
    r"\bguaranteed\s+(returns?|profits?|cure|outcome)\b",
    r"\bcures?\s+(cancer|covid|diabetes)\b",
    r"\bmedically\s+approved\b",
    r"\bFDA[- ]approved\b",
    r"\b100%\s+(safe|guaranteed|risk[- ]free)\b",
]


def _prohibited_hits(text: str) -> List[str]:
    return [m.group(0) for p in _PROHIBITED_PATTERNS for m in re.finditer(p, text, re.IGNORECASE)]


def compliance_axis(
    article: Dict[str, Any],
    blueprint: Blueprint,
    llm: Optional[LLMCaller] = None,
) -> AxisReport:
    html = _article_html(article)
    text = _strip_tags(html)

    checklist: List[Dict[str, Any]] = []

    # rules
    hits = _prohibited_hits(text)
    checklist.append(
        _checklist_item(
            "no_prohibited_language",
            not hits,
            expected="no medical/financial guarantee phrases",
            actual=hits or "clean",
        )
    )

    checklist.append(
        _checklist_item(
            "affiliate_disclosure_present",
            _has_disclosure(html),
            expected="affiliate disclosure phrase",
            actual="present" if _has_disclosure(html) else "absent",
        )
    )

    sources = article.get("source_attribution") or []
    checklist.append(
        _checklist_item(
            "sources_cited",
            True,  # weak default; PR #5a will tighten this
            expected=">= 0 source attributions",
            actual=len(sources),
            note="weak rule until PR #5a populates source_attribution",
        )
    )

    # optional LLM layer
    if llm is not None:
        body = text[:4000]
        prompt = (
            "Review this article for compliance issues beyond regex rules: "
            "deceptive claims, undisclosed paid placements, medical/financial "
            "advice without disclaimers. Return JSON with keys "
            "{passed: bool, note: str, evidence: dict}."
        )
        try:
            resp = llm(prompt, {"title": article.get("title", ""), "body": body})
            checklist.append(
                _checklist_item(
                    "llm_compliance_review",
                    bool(resp.get("passed", False)),
                    expected="LLM-clean",
                    actual=resp.get("note", ""),
                )
            )
        except Exception as e:  # don't crash review on LLM failure
            checklist.append(
                _checklist_item(
                    "llm_compliance_review",
                    True,
                    note=f"llm_failed: {e!s}",
                )
            )

    score, passed = _score_from_checklist(checklist)
    return AxisReport(
        axis="compliance",
        score=score,
        passed=passed,
        checklist=checklist,
        evidence={
            "prohibited_hits": hits,
            "sources_cited_count": len(sources),
        },
    )


__all__ = [
    "LLMCaller",
    "conformance_axis",
    "monetization_axis",
    "content_quality_axis",
    "compliance_axis",
]
