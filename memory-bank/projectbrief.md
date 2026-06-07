# Project Brief — automated_blog_platform

> Memory-bank root. Updated 2026-06-01 to reflect the current Ghost /
> PR-based architecture. The previous WordPress → JAMstack/Strapi vision
> is obsolete; `GOALS.md`, `README.md`, and `todo.md` at the repo root are
> the authoritative source of truth.

## Core Mission

A headless, multi-agent content automation platform that turns a declared
niche into SEO-optimized, monetized affiliate articles and publishes them
to a **Ghost Headless CMS** with a human-in-the-loop approval gate.

The system's moat is the **Pattern Library + Performance Feedback Loop**,
not the prose ability of any one agent. The prose is cheap; the empirically
winning blueprint is the product.

## Primary Goals

1. Niche-agnostic core that adapts to any profitable niche.
2. Typed, 5-stage CrewAI pipeline (Research → Strategy → Creation →
   Editorial → `awaiting_human_review`).
3. Deterministic, measurable editorial gating against a target Blueprint —
   not subjective "is this good" judgments.
4. Affiliate revenue, currently via Amazon Associates (store `deskcred-20`).
5. A compounding feedback loop: published article performance reshapes the
   Pattern Library over time.

## Operating Constraints

- **No autonomous publish, ever.** The pipeline's terminal state is always
  `awaiting_human_review`. Only a human click triggers Ghost.
- **Ghost, not WordPress.** WordPress is deprecated; `wordpress_service.py`
  is a stub that raises and points callers at `GhostService`.
- **Surface, don't decide.** Open design questions go to the user with
  concrete options, not silent assumptions.

## Current Niche (first live blog)

High-ticket home-office / home-based-business products and programs sold on
Amazon, tagged with Associates store ID `deskcred-20`. Ghost site:
`https://deskcred-com.ghost.io`.

## Authoritative Documents

- `GOALS.md` — product mission, KPIs, constraints
- `README.md` — architecture overview + PR roadmap status
- `todo.md` — ordered build plan
- `PRs_2_through_7.md` — detailed PR specs
- `RUN.md` — commands / runbook
