"""Amazon Associates CSV report import (PR #21).

Why this exists: new Associates accounts cannot get programmatic access
until they have 10 qualifying sales in 30 days (Creators API prerequisite),
and the legacy ``AmazonAssociatesProvider`` endpoint is not a documented
Amazon API. Associates Central *does* let you download reports as CSV, so
this importer turns a downloaded "Tracking ID Summary" / earnings CSV into
``article_analytics_daily`` rows (source='affiliate').

Header matching is alias-based and case-insensitive because Amazon's
column labels vary by report and marketplace. Leading title lines before
the header row are skipped.
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

ALIASES = {
    "tracking_id": ("tracking id", "trackingid", "tag", "tracking_id"),
    "clicks": ("clicks",),
    "conversions": ("items shipped", "shipped items", "items ordered", "ordered items", "orders", "qualifying purchases"),
    "revenue": ("ad fees", "total earnings", "earnings", "advertising fees", "commission income", "commission"),
    "date": ("date", "day"),
}


def _num(v: str) -> Decimal:
    try:
        return Decimal((v or "0").replace("$", "").replace(",", "").strip() or "0")
    except InvalidOperation:
        return Decimal("0")


def _find_header(lines: List[str]) -> int:
    for i, line in enumerate(lines[:20]):
        low = line.lower()
        if any(a in low for a in ALIASES["tracking_id"]) and "click" in low:
            return i
    raise ValueError("Could not find a header row with a Tracking ID and Clicks column")


def parse_associates_csv(text: str) -> List[Dict]:
    lines = text.splitlines()
    start = _find_header(lines)
    reader = csv.DictReader(io.StringIO("\n".join(lines[start:])))
    # Alias order is priority order (e.g. shipped items beat ordered items,
    # because Amazon pays on shipped qualifying purchases).
    headers = {(h or "").strip().lower(): h for h in (reader.fieldnames or [])}
    cols = {key: next((headers[n] for n in names if n in headers), None) for key, names in ALIASES.items()}
    if not cols["tracking_id"]:
        raise ValueError("No Tracking ID column")
    rows = []
    for r in reader:
        tag = (r.get(cols["tracking_id"]) or "").strip()
        if not tag or tag.lower() in ("total", "totals"):
            continue
        rows.append(
            {
                "tracking_id": tag,
                "clicks": int(_num(r.get(cols["clicks"]) or "0")) if cols["clicks"] else 0,
                "conversions": int(_num(r.get(cols["conversions"]) or "0")) if cols["conversions"] else 0,
                "revenue_usd": _num(r.get(cols["revenue"]) or "0") if cols["revenue"] else Decimal("0"),
                "date": (r.get(cols["date"]) or "").strip() if cols["date"] else "",
            }
        )
    return rows


def _parse_date(v: str) -> Optional[date]:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(v, fmt).date()
        except (TypeError, ValueError):
            continue
    return None


def import_associates_csv(text: str, *, for_date: date, tracking_id_map: Optional[Dict[str, int]] = None) -> Dict:
    """Parse + upsert. Returns counts and any unmatched tracking IDs."""
    from src.models.product import Article
    from src.services.analytics.ingest import _upsert_analytics_rows, refresh_performance

    if tracking_id_map is None:
        tracking_id_map = {}
        for a in Article.query.filter(Article.status == "published").all():
            if a.product and a.product.tracking_id:
                tracking_id_map.setdefault(a.product.tracking_id, a.id)

    parsed = parse_associates_csv(text)
    out_rows, unmatched = [], []
    for r in parsed:
        aid = tracking_id_map.get(r["tracking_id"])
        if aid is None:
            unmatched.append(r["tracking_id"])
            continue
        out_rows.append(
            {
                "article_id": aid,
                "date": _parse_date(r["date"]) or for_date,
                "source": "affiliate",
                "impressions": 0,
                "clicks": r["clicks"],
                "ctr": Decimal("0"),
                "avg_position": None,
                "conversions": r["conversions"],
                "revenue_usd": r["revenue_usd"],
            }
        )
    written = _upsert_analytics_rows(out_rows)
    refreshed = refresh_performance()
    return {"parsed": len(parsed), "written": written, "unmatched_tracking_ids": sorted(set(unmatched)), "performance_refreshed": refreshed}


__all__ = ["parse_associates_csv", "import_associates_csv"]
