# Product Context — automated_blog_platform

> Updated 2026-06-01. Reflects the current Ghost / PR-based system.

## Why This Project Exists

Successful affiliate blogs need continuous market research, high-quality
SEO content, strategic product placement, and disciplined editorial QA.
Doing this by hand caps output and quality. This system automates the
pipeline end-to-end up to a human approval gate, then learns from what
actually earns.

## What Makes It Different

Most "AI blog" tools optimize prose. This system optimizes **conformance
to an empirically-winning blueprint** for the target query. The Editor
asks "does this article match the blueprint that wins this SERP?" — a
deterministic, measurable question — and prose quality is a side-check,
not the main rubric.

## How It Should Work (happy path)

1. User declares a niche (name, description, target keywords, monetization).
2. The pipeline discovers Amazon products for that niche and drafts an
   article per product through the 5-stage CrewAI flow.
3. SERP Forensics (PR #5a) builds/refreshes a Blueprint for the target
   query; the Editor scores the draft against it on four axes
   (Conformance / Content Quality / Monetization / Compliance) and emits a
   binary `EditorialVerdict` (`PUBLISH` | `REJECT`).
4. Every article lands in the **human review queue** (PR #6). A human edits
   and clicks Publish; only then does it reach Ghost.
5. After ≥20 published articles, the Performance Feedback Loop (PR #7,
   planned) correlates real GSC + affiliate performance back to blueprint
   fields and surfaces blueprint-update *proposals* (never auto-applied).

## Monetization

Amazon Associates. Each `Product` carries an `affiliate_url` and a
`tracking_id` (e.g. `deskcred-20`); `CallToAction.build_target()` appends
`tag=<tracking_id>` to the destination URL so every affiliate link is
correctly attributed.

## KPIs

Tracked in `GOALS.md` — organic impressions/clicks, affiliate EPC/revenue,
newsletter opt-in rate (Ghost's built-in member tooling), and per-article
ROI (revenue vs. CostMeter spend from PR #3).
