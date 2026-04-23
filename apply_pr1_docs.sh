#!/usr/bin/env bash
# apply_pr1_docs.sh — PR #1 documentation drop (README, todo, GOALS, RUN).
# Picks up where apply_pr1.sh left off. Idempotent: re-running backs up once.
#
# Usage (from repo root):
#   chmod +x apply_pr1_docs.sh
#   ./apply_pr1_docs.sh

set -euo pipefail

if [[ ! -d "automated-blog-system/src" || ! -d "core/crewai_system" ]]; then
  echo "❌ Run from the automated_blog_platform repo root."
  exit 1
fi

BACKUP_DIR=".pr1-backup"
mkdir -p "$BACKUP_DIR"

backup() {
  local src="$1"
  if [[ -f "$src" ]]; then
    local dest="$BACKUP_DIR/$src"
    mkdir -p "$(dirname "$dest")"
    if [[ ! -f "$dest" ]]; then
      cp "$src" "$dest"
      echo "  📦 backed up $src -> $dest"
    fi
  fi
}

write_file() {
  local path="$1"
  mkdir -p "$(dirname "$path")"
  cat > "$path"
  echo "  ✍️  wrote $path"
}

echo "=== PR #1 docs drop: GOALS, RUN, README, todo ==="

# ---------- GOALS.md ------------------------------------------------------
echo "[1/4] Writing GOALS.md"
backup "GOALS.md"
write_file "GOALS.md" <<'MDEOF'
# Product Goal — automated_blog_platform

## Mission
Establish and scale a network of high-ticket affiliate media properties
to maximize Monthly Recurring Revenue (MRR) and owned-audience growth,
using an autonomous content flywheel.

## Scope of Autonomy
The system is authorized to:

1. Research trending products with MSRP ≥ $500 using real-time market data
   (Tavily, SerperDev, Firecrawl).
2. Publish SEO-optimized, long-form articles via **Ghost Headless CMS API**,
   prioritizing Buyer-Intent keywords.
3. Execute a multi-channel distribution routine per post (X, LinkedIn, Email).
4. Continuously audit published content for freshness, broken links, and
   conversion performance, using Google Search Console and affiliate
   dashboard analytics as the feedback signal.

## Primary KPIs
- **Organic Traffic Growth** — GSC impressions + clicks, 28-day trailing.
- **Newsletter Opt-in Rate** — % of sessions that convert to subscribers.
- **Earnings Per Click (EPC)** — by offer, per article.

## Operating Constraints (hard rules for the flow)
- **Monthly API + hosting budget: $100 hard cap**, enforced per-article
  via a token/cost circuit breaker in `BlogCreationFlow` (PR #3).
- **Per-article retry budget: 2 cycles**, then automated disposition
  (retire if monetization-blocked on a low-EPC offer; otherwise swap the
  affiliate offer and restart Stage 1).
- **Editorial axes are independent** — Content, SEO/UX, Monetization,
  Compliance. Rejection on one axis only re-invokes the crew responsible
  for that axis; never a blanket rewrite (PR #2).
- **Stage handoff is by database record, never by filesystem path**
  (PR #3).
- **Publisher refuses to publish unless `editorial_verdict == "PUBLISH"`**
  — enforced at the API layer in `routes/publisher.py` (shipped in PR #1).

## Definition of Done — First Blog
One niche selected. One article generated end-to-end through all 5 stages.
Published to Ghost. Live URL stored on the Article record. Distribution
routine fires at least once. GSC impressions recorded after 7 days.

## Non-goals (for now)
- WordPress publishing (deprecated).
- Multi-tenant SaaS (deferred to post-first-revenue).
- Video/TikTok distribution (deferred).
MDEOF

# ---------- RUN.md --------------------------------------------------------
echo "[2/4] Writing RUN.md"
backup "RUN.md"
write_file "RUN.md" <<'MDEOF'
# Runbook

Common commands for local development. Paths assume you are in the repo root
unless noted.

## First-time setup
```bash
cd automated-blog-system
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m scripts.migrate_add_ghost_columns
```

## Running the system
```bash
# Terminal 1 — Redis (required for agent pub/sub)
redis-server

# Terminal 2 — Flask backend on :5001
cd automated-blog-system
source venv/bin/activate
bash ../start_backend.sh

# Terminal 3 — React frontend on :5173
cd blog-frontend
npm install   # first time only
bash ../start_frontend.sh

# Terminal 4 — agent system
source automated-blog-system/venv/bin/activate
python start_agents.py
```

## Tests
```bash
cd automated-blog-system
source venv/bin/activate

# Publisher (PR #1) — mocked, no Ghost needed
pytest -q test_ghost_publisher.py -k "not live"

# Publisher — LIVE against a real Ghost instance (creates a draft only)
export GHOST_API_URL="https://your-ghost.example.com"
export GHOST_ADMIN_KEY="<id>:<hex-secret>"
export GHOST_LIVE_TEST=1
pytest -q test_ghost_publisher.py -k live
```

## Publishing an article manually (end-to-end smoke)

Assumes (a) a Ghost instance is configured, (b) an Article exists in the DB
with `editorial_verdict = 'PUBLISH'`.
```bash
# Health check (verifies Ghost auth without publishing)
curl -X GET http://localhost:5001/api/publisher/health

# Publish
curl -X POST http://localhost:5001/api/publisher/publish/<article_id>

# Save as a draft instead
curl -X POST http://localhost:5001/api/publisher/draft/<article_id>
```

Successful publish returns:
```json
{
  "success": true,
  "article_id": 1,
  "post_id": "abc123",
  "url": "https://your-ghost.example.com/best-vpn/",
  "ghost_status": "published"
}
```

The Article row will also have `ghost_post_id`, `published_url`, and
`status='published'` persisted.

## Useful env vars

| Var                | Purpose                                 |
|--------------------|-----------------------------------------|
| `GHOST_API_URL`    | Base URL of the Ghost blog              |
| `GHOST_ADMIN_KEY`  | Admin API key in `id:hexsecret` form    |
| `GHOST_LIVE_TEST`  | `1` to enable the live smoke test       |
| `OPENAI_API_KEY`   | Content generator + embeddings          |
| `TAVILY_API_KEY`   | ResearchCrew                            |
| `SERPER_API_KEY`   | ResearchCrew                            |
| `FIRECRAWL_API_KEY`| ResearchCrew                            |
| `REDIS_HOST`       | Agent pub/sub (defaults to localhost)   |
| `REDIS_PORT`       | Defaults to 6379                        |

## Rolling back a PR

Every apply script backs up modified files to `.pr1-backup/` (or `.prN-backup/`)
preserving the original path. To revert:
```bash
cp -r .pr1-backup/* .
```
MDEOF

# ---------- README.md (root) ---------------------------------------------
echo "[3/4] Writing README.md"
backup "README.md"
write_file "README.md" <<'MDEOF'
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
pipeline: Research → Strategy → Creation → Editorial → Revision. Real-time
research uses Tavily, SerperDev, and Firecrawl. Editorial returns a
structured verdict (`PUBLISH` / `REVISE` / `REJECT`) per axis (Content,
SEO/UX, Monetization, Compliance). Only `PUBLISH` articles ever reach the
Publisher.

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

## The 5 PRs that get us to a first published, revenue-capable article

The roadmap is explicit and narrow — finish these five in order and one blog
ships end-to-end. Larger roadmap items (multi-blog, SaaS, TikTok) wait.

| PR  | Title                                                       | Status         |
|-----|-------------------------------------------------------------|----------------|
| #1  | Ghost Headless CMS publisher + Article verdict gating       | ✅ Shipped     |
| #2  | Structured editor verdict + axis-scoped revision routing    | 🟡 Next        |
| #3  | Durable pipeline state + resumability + budget breaker      | ⬜ Planned     |
| #4  | Article CRUD completion + minimal approval UI               | ⬜ Planned     |
| #5  | LanceDB embedding-backed retrieval (replace token-overlap)  | ⬜ Planned     |

See `todo.md` for sub-tasks and acceptance criteria per PR.

---

## Quick start

See [`RUN.md`](RUN.md) for the full runbook. TL;DR:
```bash
cd automated-blog-system
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m scripts.migrate_add_ghost_columns
pytest -q test_ghost_publisher.py -k "not live"
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
MDEOF

# ---------- todo.md -------------------------------------------------------
echo "[4/4] Writing todo.md"
backup "todo.md"
write_file "todo.md" <<'MDEOF'
# todo.md — Ordered build plan

The order is deliberate. Each PR unblocks the next. Do not reorder without
a reason written down. Numbered phases from the prior 17-phase plan are
mapped to these PRs below; the prior plan is archived at
`docs/implementation_plan.md`.

---

## PR #1 — Ghost Headless CMS publisher  ✅ SHIPPED

**Goal:** a generated Article can be pushed to Ghost via a single API call,
and only passing articles get through.

- [x] `services/ghost_service.py` with JWT auth + HTML serializer
- [x] `routes/publisher.py` with `/health`, `/publish/<id>`, `/draft/<id>`
- [x] `Article.ghost_post_id`, `published_url`, `editorial_verdict` columns
- [x] `Article.to_headless_contract()`
- [x] Publisher refuses when `editorial_verdict != 'PUBLISH'` (APE-71 fix)
- [x] `scripts/migrate_add_ghost_columns.py` idempotent migration
- [x] Unit tests (mocked) green + live-test scaffold behind `GHOST_LIVE_TEST=1`
- [x] README / GOALS / RUN / todo docs refreshed

**Acceptance (shipped):** `pytest -q test_ghost_publisher.py -k "not live"`
returns 3 passed.

---

## PR #2 — Structured editor verdict + axis-scoped revision  🟡 NEXT

**Goal:** stop the "third-cycle QA rejection on the same axis" loop we saw
in the Paperclip run (APE-68).

- [ ] EditorCrew returns:
      `{verdict, blocking_axes[], required_changes_by_axis{}, retry_budget_remaining}`
- [ ] BlogCreationFlow revision path reads `blocking_axes` and re-invokes
      *only* the responsible crew (Monetization Specialist for monetization,
      SEO Specialist for SEO/UX, etc.).
- [ ] Monetization Auditor returns a checklist
      (anchor density, offer relevance, placement, disclosure) with per-item
      pass/fail, not a single score.
- [ ] ThirdCycleResolver — deterministic policy:
      - if `blocking_axis == "monetization"` and `retry_budget_remaining == 0`
        → swap affiliate offer and restart Stage 1, OR retire if product EPC
        is below threshold.
      - else → retire article, log postmortem.
- [ ] `EditorCrew` writes `editorial_verdict` on the Article row
      (unlocks the Publisher from PR #1).
- [ ] Tests: a verdict=REVISE on monetization only triggers the
      Monetization crew, not Content or SEO.

**Acceptance:** a rigged test article with a deliberately weak affiliate
offer routes through two monetization-only revisions, then ThirdCycleResolver
retires it — no human intervention, total cost logged.

---

## PR #3 — Durable pipeline state + resumability + budget breaker  ⬜

**Goal:** prevent the "agents in error state after restart" and
"credit balance too low" failure modes. Introduce Alembic.

- [ ] Add `flask-migrate` + `alembic` to requirements; bootstrap
      `automated-blog-system/migrations/`.
- [ ] New columns on `Article`: `current_stage`, `stage_status`,
      `attempts`, `cost_usd`, `cost_budget_usd`, `last_error`.
- [ ] `BlogCreationFlow` persists state on every stage transition.
- [ ] `BlogCreationFlow.resume(article_id)` — picks up mid-flight articles.
- [ ] `before_stage` hook: if `cost_usd > cost_budget_usd`, halt the
      article (not the process), log a postmortem row.
- [ ] Stage handoff by DB record only; remove any filesystem-path handoffs.
- [ ] Drop `wordpress_post_id` column in the same migration.
- [ ] Convert `migrate_add_ghost_columns.py` to a no-op that points at
      Alembic.
- [ ] Tests: kill the process mid-flow, restart, verify resume works and
      no duplicate API calls occur.

**Acceptance:** a forced process crash during Stage 2 resumes cleanly from
Stage 2 on restart, with cost tallied and the budget breaker intact.

---

## PR #4 — Article CRUD completion + minimal approval UI  ⬜

**Goal:** a human can drive an article from generated → published to Ghost
through the React dashboard alone.

- [ ] Finish create/update/delete on Article, Niche, Product in
      `routes/blog.py`.
- [ ] React: Articles list shows `editorial_verdict`, `current_stage`,
      `cost_usd`, `published_url`.
- [ ] Two buttons per article:
      `[Publish to Ghost]` (calls `/api/publisher/publish/<id>`)
      `[Retry Monetization]` (calls new `/api/flow/retry?axis=monetization`)
- [ ] Publish button disabled unless `editorial_verdict == 'PUBLISH'`.
- [ ] Tiny end-to-end script: generate → pass QA → click Publish → URL
      appears on the row.

**Acceptance:** full round trip from React dashboard produces a live Ghost
URL; no CLI/curl needed.

---

## PR #5 — LanceDB embedding-backed retrieval  ⬜

**Goal:** replace the naive token-overlap retrieval in `knowledge_base.py`
with real semantic search. Biggest single quality lever.

- [ ] `services/knowledge_base.py` uses LanceDB with
      `text-embedding-3-small`.
- [ ] Ingestion reindexes `docs/` on startup; dynamic harvest rows indexed
      incrementally.
- [ ] Query surface: `retrieve(query, k=8, agent_filter=None)` returns
      scored chunks with source URLs.
- [ ] ResearchCrew and EditorCrew both consume it.
- [ ] Benchmarks: a 20-query eval set measuring before/after retrieval
      relevance.

**Acceptance:** eval set top-3 relevance improves by a measurable margin
over token-overlap baseline; EditorCrew rejection rate on a fixed
regression set drops.

---

## After PR #5 — revenue loop + scale

Only start once one blog is live and earning. Candidate next areas:

- Multi-niche orchestration + per-niche editorial calibration
- Ghost newsletter/member flows for subscriber KPIs
- GSC + affiliate dashboard ingestion → Performance Analytics Agent
- Multi-blog management (headless fan-out)
- SaaS multi-tenant transformation
- TikTok / Instagram / YouTube repurposing

---

## Mapping to the prior 17-phase plan

| Old phase                                        | Now lives in |
|--------------------------------------------------|--------------|
| Phase 8 — CRUD completion                        | PR #4        |
| Phase 9 — Knowledge Base & RAG                   | PR #5        |
| Phase 10 — Multi-blog management                 | post-PR#5    |
| Phase 11 — Notification & approval system        | PR #4 (min)  |
| Phase 12 — Perf optimization & learning          | post-PR#5    |
| Phase 13 — SEO tools integration                 | post-PR#5    |
| Phase 14 — Advanced features                     | post-PR#5    |
| Phase 15 — SaaS transformation                   | post-revenue |
| Phase 16 — Testing & QA                          | rolling, per-PR |
| Phase 17 — Deployment & scaling                  | post-revenue |
MDEOF

echo
echo "=== Docs drop complete ==="
echo "Files modified/created:"
echo "  GOALS.md"
echo "  RUN.md"
echo "  README.md"
echo "  todo.md"
echo "Backups (if any originals existed) in .pr1-backup/"
echo
echo "Next steps:"
echo "  git status"
echo "  git add -A && git commit -m 'PR #1: Ghost publisher + refreshed docs'"
echo
echo "Then we move on to PR #2 (structured editor verdict)."