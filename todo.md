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

## PR #4 — CRUD completion + dashboard with cost/verdict visibility  ✅ SHIPPED

**Goal:** every PR-#3 column the system already writes becomes visible in
the dashboard, and the API surface is rounded out with PATCH + filters +
pagination + soft-delete + a stage-outputs read endpoint.

- [x] `routes/blog.py` — `GET /articles` filters by `status`,
      `editorial_verdict`, `current_stage`, `niche_id`; pagination via
      `?limit` (cap 500) + `?offset`; archived rows hidden by default
      (`?include_archived=1` opt-in); response carries `total`, `limit`,
      `offset`.
- [x] `PATCH` added to `/articles/<id>`, `/products/<id>`, `/niches/<id>`;
      shares the PUT handler; only writes fields present in the body.
- [x] `DELETE /articles/<id>` is now a soft-archive (sets
      `status='archived'`); pass `?hard=1` for true delete.
- [x] `GET /articles/<id>/stage-outputs` returns the four PR #3 stage JSON
      columns parsed + cost / verdict / blueprint_id metadata.
- [x] `GET /dashboard/stats` extended with `by_stage`, `by_verdict`,
      `awaiting_review`, and a `cost` panel for the current month
      (uses `CostMeter.current_month()`, exposed via PR #4).
- [x] `blog-frontend/src/services/api.js` — JSDoc wrappers for every new
      endpoint plus typedefs for `ArticleListFilters`, `StageOutputs`,
      `DashboardStats`. New `budgetApi` and `publisherApi` namespaces.
- [x] `Dashboard.jsx` rewritten: real-data stats only — counts by stage and
      verdict, `awaiting_human_review` queue, monthly cost vs cap progress
      bar. The previous mock "views/revenue" tiles were retired (PR #7
      replaces them with real GSC + affiliate data).
- [x] `ArticlesSimple.jsx` — added `Stage` / `Verdict` / `Cost` /
      `Published` columns plus a "Details" link to the new view.
- [x] `ArticleDetail.jsx` (new, route `/articles/:id`) — tabs for Research /
      Strategy / Draft / Monetization / Editorial Report. Editorial Report
      tab renders per-axis pass/fail checklists with expected vs actual.
- [x] No inline editing — that's PR #6.
- [x] `test_article_crud.py` — 14 acceptance tests covering create/list,
      filters (status / verdict / stage / niche), pagination, PUT + PATCH
      partial updates, keyword JSON round-trip, soft-delete + hard-delete
      escape hatch, stage-outputs payload shape, dashboard stats
      breakdowns, and Niche/Product PATCH preserves untouched fields.

**Acceptance:**
`pytest -q test_ghost_publisher.py test_editor_verdict.py
test_observability.py test_article_crud.py` → 28 passed, 1 skipped.
Frontend `npm run build` clean.

---

## (User task) Stand up Ghost  ⬜

Ghost on the Hostinger VPS via docker-compose alongside Paperclip's traefik,
or Ghost Pro at ~$9/mo. Set `GHOST_API_URL` + `GHOST_ADMIN_KEY`. Run
`pytest -q test_ghost_publisher.py -k live` to verify.

---

## PR #5a — SERP Forensics + Pattern Library  ✅ SHIPPED

**The one where the agents become smart.** Editor now grades against an
empirically-derived Blueprint, not a hand-written stub.

- [x] Alembic migration `0003_pr5a_pattern_library.py` adds the
      `blueprints` and `serp_profiles` tables. Both tables drop cleanly on
      downgrade.
- [x] `models/pattern_library.py` — `BlueprintRow` (versioned, with
      `parent_blueprint_id` for audit) and `SerpProfile` (cached per
      `(url, query)`). `BlueprintRow.to_blueprint()` /
      `from_blueprint()` round-trip the in-memory contract losslessly.
- [x] `services/serp_forensics.py` — `SerpForensics` class with
      `pull_serp` (Serper), `fetch_html` (Firecrawl with plain-GET
      fallback), `profile_url` (HTML→`ArticleProfile`), `aggregate` (per-
      field median/IQR + confidence tiers), `identify_gaps`. HTML parsing
      is regex-only — deterministic, dependency-free.
- [x] `services/blueprint_repo.py` — `get_blueprint_for_niche` (DB →
      refresh → stub fallback), `persist_blueprint` (versioned write),
      `refresh_blueprint` (pull SERP → profile → aggregate → persist).
      `allow_refresh=False` keeps unit tests network-free.
- [x] Stage 0.5 — Blueprint Selection — wired into `BlogCreationFlow`
      between Research and Strategy via
      `stage_persistence.select_blueprint_for_article`. Sets
      `Article.blueprint_id` and flips `current_stage` to
      `stage_0_5_blueprint_selected`.
- [x] `editorial_review` now pulls the active Blueprint via
      `blueprint_repo.get_blueprint_for_niche(allow_refresh=False)`
      instead of the PR #2 stub. The stub remains as the bottom fallback
      for niches the Pattern Library hasn't covered yet.
- [x] Freshness policy — default 30 days
      (`DEFAULT_BLUEPRINT_TTL_DAYS`); per-niche override deferred to a
      future PR per the doc's "When stuck" guidance.
- [x] `test_serp_forensics.py` — 7 cases: deterministic profile
      extraction (HTML fixture), confidence tiers (tight/spread/mixed),
      gap identification with planted gaps, BlueprintRow persistence +
      version bump + parent linkage, Stage 0.5 with fresh DB row, Stage
      0.5 stub fallback, Stage 0.5 stale → refresh path with injected
      profiles.

**Acceptance:**
`pytest -q test_ghost_publisher.py test_editor_verdict.py
test_observability.py test_article_crud.py test_serp_forensics.py` →
35 passed, 1 skipped.

---

## PR #5b — LanceDB retrieval unification  ✅ SHIPPED

**Goal:** retire token-overlap, route every retrieval call through one
LanceDB-backed hybrid (vector + BM25) interface, and ship an eval harness
that lets us measure quality before merging future retrieval changes.

- [x] `services/retrieval.py` — single `retrieve(query, collection, k,
      filters)` surface backed by LanceDB. Hybrid merge is reciprocal-
      rank fusion (constant 60) with the doc-spec 0.7/0.3 vector/lexical
      weights. Embedder is injectable: `make_hash_embedder()` for tests
      (deterministic, network-free), `make_openai_embedder()` for prod
      (auto-records cost via PR #3's CostMeter).
- [x] Four collections: `docs`, `profiles`, `research_harvest`,
      `own_articles`. One LanceDB table per collection, lazily created
      on first ingest. FTS index on `text` lazily created on first
      query; falls back to vector-only if the LanceDB build doesn't
      support FTS.
- [x] Chunker: split markdown on H2 boundaries, ~400-800 word target with
      50-token overlap; sliding window for over-target sections; HTML
      input gets tags stripped first.
- [x] Ingestion API: `ingest_doc(path, text)` / `reindex_docs(root)` /
      `ingest_profile(profile, query)` / `ingest_research(article_id,
      harvest)` / `ingest_own_article(article_id, title, body)`. Insert-
      or-replace by stable id so re-ingesting the same source doesn't
      duplicate.
- [x] `knowledge_base.py` is now a thin shim over `retrieval` —
      `KnowledgeBase.retrieve()` delegates to `retrieve(..., "docs",
      ...)`. The token-overlap code is gone; the public surface is
      preserved so existing CrewAI agents don't break.
- [x] `eval/retrieval_eval.py` — token-overlap baseline (kept inline so
      the eval is the single source of truth for "the old behavior"),
      `compare_baseline_vs_hybrid` runner, nDCG@8 + Recall@8 metrics.
      Designed to run two ways: in-test with the hash embedder for
      structural CI, or `python -m eval.retrieval_eval` against the real
      `/docs` corpus with OpenAI embeddings for the human's
      pre-merge review.
- [x] `test_retrieval.py` — 8 cases: chunker round-trips H2-split content,
      huge-section sliding window, ingest + exact-text retrieval, ingest
      replaces (no duplicates), filter narrowing by `niche_id`, eval
      hybrid ≥ baseline assertion, plus standalone metric/baseline sanity.

**Acceptance:**
`pytest -q test_ghost_publisher.py test_editor_verdict.py
test_observability.py test_article_crud.py test_serp_forensics.py
test_retrieval.py test_knowledge_base.py` → 44 passed, 1 skipped.

---

## PR #6 — Human-in-the-loop review + publish UI  ✅ SHIPPED

**Goal:** the only path from `awaiting_human_review` to a live Ghost
post is a human clicking Publish in the UI. PR #6 builds that surface,
plus the local-vs-Ghost drift detection that lets reviewers spot edits
made in Ghost Admin.

- [x] Alembic `0004_pr6_review_ui.py` adds `ghost_updated_at`,
      `last_ghost_sync_hash`, `has_unpushed_changes` to `articles` and
      creates `article_revisions` (append-only pre-pull/pre-push
      snapshots).
- [x] `GhostService.fetch_post(post_id, *, use_cache)` and
      `set_status(post_id, status)`. 60-second in-process cache keyed by
      `(api_url, post_id)` so dashboard fan-out doesn't hammer Ghost.
      `compute_content_hash()`, `extract_ghost_payload()`, and
      `diff_payloads()` form the drift toolkit.
- [x] `routes/publisher.py` factors out `publish_article_now(article)`
      which `routes/review.py` reuses — single source of truth for the
      publish-to-Ghost code path.
- [x] `routes/review.py` ships eight endpoints under `/api/review`:
      `queue`, `<id>` (GET + PATCH), `publish`, `unpublish`, `ghost`,
      `pull-from-ghost`, `push-to-ghost`. PATCH validates
      `meta_description ≤ 160 chars`, `keywords ≤ 10`, CTA URLs.
      Per-article `threading.Lock` (keyed by id) serializes mutating
      operations.
- [x] Frontend: `services/api.js` gains `reviewApi.*` with JSDoc
      typedefs; `ReviewQueue.jsx` (dedicated review screen with verdict
      filter + sort + per-axis scores), `ArticleReview.jsx` (two-column
      editor + Editorial Report panel + Ghost Preview iframe + footer
      actions + 30-second autosave + confirm-publish modal),
      `PublishedArticles.jsx` (drift indicator per row, sequential
      drift fan-out, Pull / Push / Review actions). Layout sidebar adds
      "Review Queue" + "Published" entries. ArticlesSimple gets a
      "Review & Publish" link for `verdict==='PUBLISH'` rows.
- [x] `test_review_routes.py` — 11 cases: verdict gate (publish + push),
      PATCH round-trip, PATCH validation (meta length, CTA URLs),
      publish path with mocked Ghost (asserts the request body),
      pull-from-Ghost overwrites local + records revision,
      drift detection on divergent Ghost HTML, push-to-Ghost sends edits
      + records pre-push revision, push refuses without `ghost_post_id`,
      push refuses non-PUBLISH verdict, plus the "no autonomous publish"
      grep guard scanning the repo for forbidden call sites outside
      `routes/review.py` / `routes/publisher.py` / the Ghost service.
- [x] Frontend RTL tests: skipped per the doc's "manual QA checklist
      acceptable" allowance — see the manual E2E recipe in `RUN.md`.

**Acceptance:**
`pytest -q test_ghost_publisher.py test_editor_verdict.py
test_observability.py test_article_crud.py test_serp_forensics.py
test_retrieval.py test_knowledge_base.py test_review_routes.py` →
55 passed, 1 skipped.
Frontend `npm run build` clean.

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
