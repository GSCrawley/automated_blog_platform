# Progress — automated_blog_platform

> Updated 2026-06-01. Authoritative status lives in `todo.md` /
> `README.md`; this is the memory-bank mirror.

## PR Roadmap Status

| PR  | Title                                                  | Status   |
|-----|--------------------------------------------------------|----------|
| #1  | Ghost publisher + Article verdict gating               | Shipped  |
| #2  | Structured EditorialVerdict + Blueprint stub + 4 axes  | Shipped  |
| #3  | Cost metering + stage observability + Alembic          | Shipped  |
| #4  | CRUD completion + dashboard (cost/verdict visibility)   | Shipped  |
| #5a | SERP Forensics + Pattern Library                       | Shipped  |
| #5b | LanceDB retrieval unification                          | Shipped  |
| #6  | Human-in-the-loop review + publish UI                  | Shipped  |
| #6.4| Foundation fix (persistent SQLite, affiliate columns)   | Shipped  |
| #7  | Performance Feedback Loop (after ≥20 published)        | Planned  |

## What Works

- 5-stage CrewAI pipeline ending in `awaiting_human_review`.
- Four-axis Editor → binary `EditorialVerdict`.
- Ghost publishing via Admin API v5; review queue + publish UI (PR #6).
- Pattern Library (blueprints / serp_profiles) + LanceDB retrieval.
- Cost metering, per-article budget breaker, stage observability.
- Alembic migrations `0001`→`0004` + affiliate-column migration.
- Amazon affiliate plumbing: `Product.affiliate_url` / `tracking_id`,
  `CallToAction.build_target()` appends `tag=<tracking_id>`.

## In Progress (branch `chore/cleanup-and-amazon-deploy`)

- Repo hygiene: `redis`/`openai` added to requirements; untracking
  `.DS_Store`/`dump.rdb`; removing `repomix-output.xml`; ignoring `.kilo/`.
- Memory-bank rewritten to current reality; `WARP.md` deleted.
- First live Amazon blog deployment (niche → article → review → publish).

## Known Gaps / To Do

- AI product-discovery prompt does not yet request `affiliate_url` /
  `tracking_id`; discovered products need the `deskcred-20` tag wired in.
- `FIRECRAWL_API_KEY` not set (optional; requests.get fallback in use).
- PR #7 not started; needs ≥20 published articles for signal.
- WordPress paths remain as deprecated stubs (intended).

## Definition of Done (per GOALS.md)

One niche → one article through all 5 stages → published to Ghost → live
URL stored → affiliate links attributed → (after 7 days) GSC impressions
recorded. PR #7 then closes the learning loop.
