# automated_blog_platform

A headless, multi-agent content automation platform that turns a declared
niche into SEO-optimized, monetized affiliate articles and publishes them
to a **Ghost Headless CMS** with minimal human intervention.

Product goal, scope, and operating constraints live in [`GOALS.md`](GOALS.md).
Ordered build plan lives in [`todo.md`](todo.md). Commands live in
[`RUN.md`](RUN.md).

---

## What's in the box

**CrewAI BlogCreationFlow** (`core/crewai_system/`) — a 5-stage typed
pipeline: Research → Strategy → Creation → Editorial → `awaiting_human_review`.
Real-time research uses Tavily, SerperDev, and Firecrawl. The Editor
(rewritten in PR #2 as a pure-Python orchestrator over four axis evaluators —
Conformance / Content Quality / Monetization / Compliance) emits a binary
`EditorialVerdict` (`PUBLISH` | `REJECT`) measured against a target
`Blueprint` from the Pattern Library (PR #5a; stubbed in PR #2). There is no
automated revision loop — every article ends in the human review queue (PR #6).
Only verdict=`PUBLISH` articles ever reach the Publisher.

**Custom Redis-backed agent framework** (`core/agents/`) — Orchestrator and
Market Analytics agents are live; Author, Editor, Product Scout, and
Affiliate Ops are scaffolded. Used for autonomous coordination, monitoring,
and cross-pipeline tasks.

**Flask + SQLAlchemy backend** (`automated-blog-system/`) — REST API for
articles, products, niches, agent state, and publishing to Ghost.

**React 19 + Vite frontend** (`blog-frontend/`) — Dashboard, article/product
management, approval UI, and (forthcoming) live agent monitoring.

---

## Why Ghost (and why not WordPress)

WordPress is intentionally deprecated. The system is CMS-agnostic by design,
but Ghost is the primary publishing target because:

- A real Admin API (no XML-RPC, no plugin maze).
- Built-in newsletter/member tooling that directly supports the KPI
  *Newsletter Opt-in Rate* in `GOALS.md`.
- Headless-friendly: posts are HTML/Lexical, easy to render anywhere.

The publisher service lives at
`automated-blog-system/src/services/ghost_service.py` and is exposed via
the `POST /api/publisher/publish/<article_id>` endpoint.

---

## System architecture
```
                    ┌─────────────────────────────────┐
                    │   React Dashboard (Vite, 5173)  │
                    └─────────────┬───────────────────┘
                                  │ REST
                    ┌─────────────▼───────────────────┐
                    │   Flask API (5001)              │
                    │   /api/blog  /api/automation    │
                    │   /api/agents  /api/publisher   │
                    └──┬───────┬──────────┬───────────┘
                       │       │          │
              ┌────────▼─┐ ┌───▼────┐ ┌───▼─────────┐
              │ SQLite/  │ │ Redis  │ │ GhostService│
              │ Postgres │ │ pub/sub│ │ (Admin API) │
              └────┬─────┘ └───┬────┘ └───┬─────────┘
                   │           │          │
                   │     ┌─────▼─────┐    │
                   │     │ CrewAI    │    │
                   │     │ BlogFlow  │    │
                   │     │ 0→1→2→2.5 │    │
                   │     │ →3→4      │    │
                   │     └───────────┘    │
                   │                      ▼
                   │              ┌──────────────┐
                   └─────────────►│ Ghost CMS    │
                                  │ (live blog)  │
                                  └──────────────┘
```

---

## The PR roadmap

The full plan lives in [`PRs_2_through_7.md`](PRs_2_through_7.md); `todo.md`
mirrors the high-level checklist. The system's moat is the Pattern Library
plus the Performance Feedback Loop (PR #5a + PR #7), not any one agent's
prose ability.

| PR   | Title                                                       | Status         |
|------|-------------------------------------------------------------|----------------|
| #1   | Ghost Headless CMS publisher + Article verdict gating       | ✅ Shipped     |
| #2   | Structured EditorialVerdict + Blueprint stub + 4 axes       | ✅ Shipped     |
| #3   | Cost metering + stage observability + Alembic               | ✅ Shipped     |
| #4   | CRUD completion + dashboard with cost/verdict visibility    | ✅ Shipped     |
| #5a  | SERP Forensics + Pattern Library (the heart of the system)  | ✅ Shipped     |
| #5b  | LanceDB retrieval unification                               | ⬜ Planned     |
| #6   | Human-in-the-loop review + publish UI (only publish path)   | ⬜ Planned     |
| #7   | Performance Feedback Loop (after ≥20 published articles)    | ⬜ Planned     |

---

## Quick start

See [`RUN.md`](RUN.md) for the full runbook. TL;DR:
```bash
cd automated-blog-system
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
FLASK_APP=src.main:create_app flask db upgrade
pytest -q test_ghost_publisher.py test_editor_verdict.py test_observability.py test_article_crud.py test_serp_forensics.py -k "not live"
```

---

## Headless Article Contract

Produced by the CrewAI pipeline, consumed by `GhostService`:
```json
{
  "id": 123,
  "title": "Best VPN for SMBs in 2026",
  "slug": "best-vpn-for-smbs-2026",
  "summary": "Concise abstract",
  "sections": [{"heading": "H2 text", "content": "Markdown or HTML-safe"}],
  "keywords": ["primary", "secondary"],
  "entities": ["BrandX", "ConceptY"],
  "calls_to_action": [
    {"type": "affiliate", "target": "https://vendor/ref", "anchor": "Buy Now"}
  ],
  "meta": {"meta_title": "...", "meta_description": "...",
           "feature_image": "https://...", "read_time_minutes": 7},
  "source_attribution": [{"url": "https://...", "confidence": 0.74}]
}
```

`Article.to_headless_contract()` produces this shape from the current DB row.
Today it populates `content`, `summary`, `keywords`, and `meta`; sections
and CTAs will be filled in by PR #2.

---

## External Integrations

| Service                                    | Purpose                            | Status          |
|--------------------------------------------|------------------------------------|-----------------|
| OpenAI (gpt-4o-mini, text-embedding-3-small) | Content gen, embeddings, planning | ✅ Integrated   |
| Tavily Search API                          | ResearchCrew real-time queries     | ✅ Integrated   |
| SerperDev API                              | SEO/search intelligence            | ✅ Integrated   |
| Firecrawl                                  | Web scraping/content extraction    | ✅ Integrated   |
| **Ghost Admin API v5**                     | **Article publishing**             | ✅ PR #1        |
| Redis                                      | Agent pub/sub + task queues        | ✅ Integrated   |
| LanceDB                                    | Vector retrieval                   | 🟡 PR #5        |

---

## Lessons baked into this design (from the Paperclip 'Apex Affiliates' run)

The system incorporates concrete failure modes observed during a prior
Paperclip-based attempt at the same goal:

- **"Third-cycle QA rejection" stalls** → deterministic ThirdCycleResolver
  (retire vs. offer-swap), not human escalation (PR #2).
- **QA rejecting the same axis three times in a row** → structured verdict
  with `blocking_axes` + axis-scoped revision routing (PR #2).
- **Stage-handoff filesystem path errors** → every stage writes through
  the Flask API, not a workspace path (PR #3).
- **Agents in error state after restart** → durable pipeline state machine
  with `BlogCreationFlow.resume(article_id)` (PR #3).
- **"Credit balance too low" runaway cost** → per-article budget circuit
  breaker (PR #3).
- **Publisher emitting non-passing articles** → `editorial_verdict` gate at
  the API layer (shipped in PR #1).

---

## Repository layout
```
automated_blog_platform/
├── GOALS.md                   # Product mission, KPIs, constraints
├── README.md                  # You are here
├── RUN.md                     # Commands
├── todo.md                    # Ordered build plan
├── automated-blog-system/     # Flask backend + REST API
│   ├── src/
│   │   ├── main.py
│   │   ├── models/            # Product, Article, Niche, agent_models
│   │   ├── routes/            # blog, automation, agent_routes,
│   │   │                      # user, publisher (NEW in PR #1)
│   │   └── services/          # content_generator, seo_optimizer,
│   │                          # knowledge_base, trend_analyzer,
│   │                          # ghost_service (NEW in PR #1)
│   ├── scripts/               # One-shot migrations
│   ├── test_ghost_publisher.py
│   └── requirements.txt
├── core/                      # Agent layer
│   ├── agents/                # Redis pub/sub framework
│   ├── crewai_system/         # 5-stage BlogCreationFlow + crews
│   ├── infrastructure/
│   ├── scrapers/
│   └── data/
├── blog-frontend/             # React 19 + Vite
├── docs/                      # Agent rulebooks, architecture notes
└── memory-bank/               # Development context
```

---

## Legacy WordPress

`wordpress_service.py` remains as a migration stub that raises a clear error
pointing callers to `GhostService`. WordPress-specific Article columns
(`wordpress_post_id`) are retained for now but are no longer written; they
will be dropped in PR #3 alongside the Alembic introduction.
