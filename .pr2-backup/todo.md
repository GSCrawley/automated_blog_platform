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
