# System Patterns — automated_blog_platform

> Updated 2026-06-01. Reflects the current Ghost / PR-based architecture.

## High-Level Architecture

```
React Dashboard (Vite, :5173)
        │ REST
Flask API (:5000)  /api/blog /api/automation /api/agents
                   /api/publisher /api/review /api/budget
   ├── SQLite (dev) / Postgres (prod-ready)  — SQLAlchemy + Alembic
   ├── Redis pub/sub  — OPTIONAL legacy agent framework
   ├── CrewAI BlogCreationFlow  — stages 0→1→2→2.5→3→4
   └── GhostService (Admin API v5)  — the only publish target
```

## Key Components

- **CrewAI BlogCreationFlow** (`core/crewai_system/`): typed 5-stage
  pipeline. Terminal state is always `awaiting_human_review`.
- **EditorCrew** (`core/crewai_system/crews/editor_crew/`): pure-Python
  orchestrator over four axis evaluators. Emits `EditorialVerdict`
  (`PUBLISH` | `REJECT`). No automated revision loop — the human reviewer
  is the revision engine.
- **Pattern Library / SERP Forensics** (`serp_forensics.py`, blueprints +
  serp_profiles tables): the system's moat. Blueprints define the target
  shape (word count, H2 count, required sections, keyword density, schema).
- **LanceDB retrieval** (PR #5b): unified vector retrieval, replacing the
  old naive token retrieval in `knowledge_base.py`.
- **Custom Redis agent framework** (`core/agents/`): Orchestrator +
  Market Analytics live; Author/Editor/Product Scout/Affiliate Ops
  scaffolded. Optional — `create_app()` runs fine without Redis.
- **GhostService** (`automated-blog-system/src/services/ghost_service.py`):
  publishes via Ghost Admin API v5; exposed through `/api/publisher/*` and
  the PR #6 `/api/review/<id>/publish` path.

## Important Design Decisions

- **Binary verdict, no REVISE.** Given PR #6 puts a human in the loop,
  automated revision is redundant and expensive.
- **All stage handoffs go through the Flask API**, never a filesystem path
  (fixes a class of handoff errors seen in the prior Paperclip run).
- **Durable state machine** with `BlogCreationFlow.resume(article_id)` and
  a per-article budget circuit breaker (PR #3).
- **Idempotent Alembic migrations** in `automated-blog-system/migrations/`.
- **No network calls in unit tests** — `responses` for HTTP, in-memory
  SQLite for models.

## Data Model Highlights

- `Product`: `affiliate_url`, `tracking_id` (Amazon tag), keywords, price.
- `Article`: `ghost_post_id`, `published_url`, `editorial_verdict`,
  `last_verdict_json`, `blueprint_id`, `current_stage`, `stage_status`.
- `CallToAction.build_target()`: appends `tag=<tracking_id>` for Amazon.
- Observability: `cost_events`, `budgets`, `editorial_reports` (PR #3).
- Pattern Library: `blueprints`, `serp_profiles` (PR #5a).

## Migrations (Alembic)

- `0001` baseline · `0002` observability (drops `wordpress_post_id`) ·
  `0003` pattern library · `0004` review UI ·
  `65ce81a88136` affiliate_url + tracking_id on products.
