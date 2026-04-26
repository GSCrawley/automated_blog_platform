# todo.md — Ordered build plan

The order is deliberate. Each PR unblocks the next. Detailed scope and
acceptance tests for PRs #2–#7 live in [`PRs_2_through_7.md`](PRs_2_through_7.md).
Do not reorder without writing down a reason.

The system's moat is the **Pattern Library + Performance Feedback Loop**, not
the prose-writing ability of any one agent. PR #2 is verdict plumbing; PR #5a
is where the agents start being genuinely smart; PR #7 is where the system
starts compounding.

---

## PR #1 — Ghost Headless CMS publisher  ✅ SHIPPED

- [x] `services/ghost_service.py` (JWT auth + HTML serializer)
- [x] `routes/publisher.py` (`/health`, `/publish/<id>`, `/draft/<id>`)
- [x] Article Ghost columns + `to_headless_contract()`
- [x] Publisher refuses unless `editorial_verdict == "PUBLISH"`
- [x] One-shot `migrate_add_ghost_columns.py`
- [x] `pytest -q test_ghost_publisher.py -k "not live"` — 3 passed

---

## PR #2 — Structured EditorialVerdict + Blueprint stub  ✅ SHIPPED

**Goal:** the Editor stops grading prose and starts grading conformance to a
target Blueprint. Verdict is binary; every article ends at
`awaiting_human_review`.

- [x] `core/crewai_system/contracts/editorial_verdict.py` — `AxisReport`,
      `EditorialVerdict`, lossless JSON round-trip.
- [x] `core/crewai_system/contracts/blueprint.py` — `Blueprint` dataclass +
      `load_stub_blueprint(niche_name)` (replaced by PR #5a).
- [x] `core/crewai_system/crews/editor_crew/axes.py` — four axis evaluators:
      Conformance + Monetization deterministic; ContentQuality + Compliance
      LLM-injectable with pass-stub default (no network in unit tests).
- [x] `core/crewai_system/crews/editor_crew/editor_crew.py` rewritten as a
      pure-Python orchestrator (CrewAI dropped from the editor; legacy crew
      preserved at `.pr2-backup/`).
- [x] `automated-blog-system/src/services/editorial_review.py` —
      `run_editorial_review(article_id)` loads Article, runs review, persists
      verdict + report JSON, sets `current_stage = "awaiting_human_review"`.
- [x] `Article` columns added: `last_verdict_json`, `blueprint_id`,
      `current_stage`. Idempotent migration:
      `scripts/migrate_add_verdict_columns.py`.
- [x] `BlogCreationFlow` rewritten: revision router removed, terminal state is
      `awaiting_human_review` regardless of verdict.
- [x] `test_editor_verdict.py` — 6 tests covering schema round-trip,
      Conformance determinism, PUBLISH/REJECT gates, terminal-state, and a
      direct EditorCrew sanity check.

**Acceptance:**
`pytest -q test_editor_verdict.py && pytest -q test_ghost_publisher.py -k "not live"`
→ 9 passed.

---

## PR #3 — Cost metering + stage observability + Alembic  ✅ SHIPPED

**Goal:** know what each article costs in dollars per stage, persist every
stage's output, and stop one-shot migration scripts.

- [x] Added `Flask-Migrate>=4.0.0` + `alembic>=1.13.0` to
      `automated-blog-system/requirements.txt`. Flask-Migrate registered in
      `src/main.py`; migrations directory pinned to `automated-blog-system/migrations/`.
- [x] Baseline migration `0001_baseline.py` captures the post-PR-#2 schema
      (every model, including PR #1 Ghost columns and PR #2 verdict columns).
- [x] PR #3 migration `0002_pr3_observability.py` adds the new columns to
      `articles`, drops `wordpress_post_id`, and creates `cost_events`,
      `budgets`, and `editorial_reports`.
- [x] `services/cost_meter.py` + `services/model_rates.py` — `CostMeter.record`,
      `total_for_article`, `total_for_month`, `assert_can_start_flow`,
      `track(article_id, stage)` context manager. Rate card covers gpt-4o-mini,
      gpt-4o, gpt-4-turbo, gpt-3.5-turbo, text-embedding-3-small/large.
- [x] Per-article budget halt via `services/stage_persistence.check_and_halt_if_over_budget`
      (sets `current_stage="halted_budget"`, `stage_status="halted"`).
      Monthly cap from `GOALS.md` ($100) enforced by
      `CostMeter.assert_can_start_flow`.
- [x] Stage output JSON columns persisted via `persist_stage_output` —
      `research_report_json`, `strategy_json`, `draft_sections_json`,
      `monetization_map_json`. `last_verdict_json` retained for PR #2 back-compat;
      `editorial_reports` rows written in parallel for PR #6/#7 join targets.
- [x] `wordpress_post_id` dropped via `op.batch_alter_table` (SQLite-safe).
- [x] `routes/budget.py` exposes `GET /api/budget/status`.
- [x] `BlogCreationFlow` — pre-flow monthly-cap refusal; per-stage persistence;
      per-stage budget halt that short-circuits subsequent stages.
- [x] `migrate_add_ghost_columns.py` + `migrate_add_verdict_columns.py` are
      no-op shims pointing at `flask db upgrade`.
- [x] `test_observability.py` — 5 acceptance tests (Alembic round-trip in a
      fresh subprocess, cost metering, per-article halt, monthly cap refusal,
      stage outputs persist through all four stages).

**Acceptance:**
`pytest -q test_ghost_publisher.py test_editor_verdict.py test_observability.py`
→ 14 passed, 1 skipped (the live Ghost test).

---

## PR #4 — CRUD completion + dashboard with cost/verdict visibility  ⬜

- [ ] Backend: complete POST/PUT/PATCH/DELETE on Article/Niche/Product;
      soft-delete; filter by `status`/`editorial_verdict`/`current_stage`/
      `niche_id`; `GET /api/articles/<id>/stage-outputs`.
- [ ] Frontend: Dashboard counts by stage + verdict; monthly cost vs cap bar;
      `awaiting_human_review` queue; ArticlesSimple shows new columns;
      ArticleDetail tabs for research/strategy/draft/monetization/verdict.
- [ ] No inline editing yet — that's PR #6.
- [ ] `test_article_crud.py` mandatory; frontend RTL or QA checklist.

---

## (User task) Stand up Ghost  ⬜

Ghost on the Hostinger VPS via docker-compose alongside Paperclip's traefik,
or Ghost Pro at ~$9/mo. Set `GHOST_API_URL` + `GHOST_ADMIN_KEY`. Run
`pytest -q test_ghost_publisher.py -k live` to verify.

---

## PR #5a — SERP Forensics + Pattern Library  ⬜

**The big one — this is where the agents become smart.**

- [ ] `services/serp_forensics.py` — Serper SERP pull, Firecrawl profile
      extraction, aggregator with confidence tiers, gap identification.
- [ ] `blueprints` + `serp_profiles` tables (Alembic).
- [ ] Stage 0.5 — Blueprint Selection — between Research and Strategy.
- [ ] Stub blueprint loader from PR #2 replaced with Pattern-Library lookup.
- [ ] Freshness policy (default 30 days, niche-overridable).
- [ ] `test_serp_forensics.py` — deterministic profile extraction, expected
      confidence tiers, gap identification, Blueprint persistence,
      Stage 0.5 integration.

---

## PR #5b — LanceDB retrieval unification  ⬜

- [ ] `services/retrieval.py` — single `retrieve(query, collection, k, filters)`
      surface backed by LanceDB + BM25 hybrid.
- [ ] Collections: `docs`, `profiles`, `research_harvest`, `own_articles`.
- [ ] Remove naive token-overlap retrieval from `knowledge_base.py`.
- [ ] `eval/retrieval_eval.py` — 20-query nDCG@8 / Recall@8 vs baseline.
      If retrieval doesn't beat baseline, stop and ask before merging.

---

## PR #6 — Human-in-the-loop review + publish UI  ⬜

- [ ] `routes/review.py` — queue, get, PATCH, publish, unpublish, ghost-fetch,
      pull-from-ghost, push-to-ghost.
- [ ] `GhostService.fetch_post()` + `set_status()`.
- [ ] `article_revisions` table for snapshots before pull/push.
- [ ] React: `ArticleReview.jsx` (Tiptap + Sections + CTAs + SEO tabs +
      Editorial Report + Blueprint Conformance + Ghost Preview iframe);
      `PublishedArticles.jsx` with drift indicators and side-by-side diff.
- [ ] Per-article in-process lock (`threading.Lock`).
- [ ] `test_review_routes.py` + frontend RTL flows + a documented manual E2E.
- [ ] Grep guard test: `/api/publisher/publish/` only callable from
      `routes/review.py` and `routes/publisher.py`.

---

## (User task) Publish 20+ articles  ⬜

PR #7 needs at least ~20 published articles to have signal. Don't start it
sooner.

---

## PR #7 — Performance Feedback Loop  ⬜

**Where the system starts compounding.**

- [ ] `services/analytics/gsc_provider.py` — daily GSC ingest into
      `article_analytics_daily`.
- [ ] `services/analytics/affiliate_provider.py` — Amazon Associates + one
      other (user choice — surface as a question).
- [ ] `article_performance` roll-up; `article_blueprint_snapshot` for audit.
- [ ] `services/feedback_engine.py` — per-Blueprint-field effect sizes,
      bootstrap CIs, min-n=10 gating; `BlueprintProposal` rows (never
      auto-applied).
- [ ] `FeedbackProposals.jsx` review screen; Dashboard ROI leaderboard.
- [ ] `test_feedback_engine.py` — GSC ingest round-trip, tier assignment,
      effect-size bounds, min-n gating, proposal lifecycle creates a new
      Blueprint version on accept and retains the old one.

---

## After PR #7

Multi-niche calibration, Ghost newsletter/member flows, multi-blog fan-out,
SaaS multi-tenant, social repurposing — only after the feedback loop has
shown it actually moves the needle.
