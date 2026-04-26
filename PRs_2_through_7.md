# Handoff Plan: PRs #2 through #7 (for Claude Code)

## North Star

Build a content system that makes decisions from real-time data, not priors.
The agents' job is not "write good articles" — it is:

1. Look at what is currently winning in the target SERP.
2. Extract the structural pattern of the winners and the coverage gaps in
   their content.
3. Produce articles that conform to the winning pattern AND exploit at
   least one identified gap.
4. Measure real post-publish outcomes (GSC, affiliate dashboards) and
   update the pattern weights based on what actually drove traffic and
   revenue for our niches.

The system's moat is the Pattern Library + Performance Feedback Loop, not
the prose-writing ability of any one agent. The prose is cheap; the
blueprint is the product.

Everything in this document serves that north star.

## Context Claude Code should load before starting

Read these, in this order:

1. `GOALS.md`
2. `README.md`
3. `todo.md`
4. This document
5. `core/crewai_system/blog_creation_flow.py` and the `crews/` subdir
6. `automated-blog-system/src/models/product.py` (Article has Ghost
   columns + `to_headless_contract()` from PR #1)
7. `automated-blog-system/src/routes/publisher.py`
8. `automated-blog-system/src/services/knowledge_base.py` (naive token
   retrieval — replaced in PR #5b)

## Working rules

- **Branch per PR**, named `pr2-verdict-schema`, `pr3-observability`,
  `pr4-crud-dashboard`, `pr5a-serp-forensics`, `pr5b-lancedb`,
  `pr6-review-ui`, `pr7-feedback-loop`.
- **Back up rewritten files** to `.prN-backup/` preserving path (matches
  the PR #1 `.pr1-backup/` convention).
- **Idempotent migrations.** Until Alembic lands in PR #3, one-shot
  scripts only, guarded by `if column in inspector.get_columns(...)`.
- **Green means green.** A PR is not done until its own acceptance tests
  pass AND every prior PR's tests still pass.
- **No autonomous publish, ever.** The pipeline's terminal state is
  always `awaiting_human_review`. Only a user click triggers Ghost.
- **No network calls in unit tests.** `responses` for HTTP, in-memory
  SQLite for models.
- **Surface, don't decide.** When a design question arises that this
  document doesn't cover, stop and ask the user with two or three
  concrete options.
- **No account-level operations.** Don't create Hostinger/Ghost/
  OpenAI/etc. accounts on the user's behalf, don't change billing
  settings, don't modify DNS. Those are user-performed.

---

# PR #2 — Structured EditorialVerdict with conformance-to-blueprint scoring

## Why this PR exists

The Editor's job is no longer "is this article good" — it is "does this
article conform to the empirically-winning blueprint for its target
query?" That's a deterministic, measurable question. Prose quality becomes
a side-check, not the main rubric.

This PR introduces the verdict schema and wires it into the existing
EditorCrew. It assumes the blueprint will come from PR #5a; until then,
use a stub blueprint derived from the article's own metadata so the
plumbing is testable.

## Scope

### 2.1 Verdict schema

`core/crewai_system/contracts/editorial_verdict.py`:
```python
from dataclasses import dataclass, field
from typing import Literal

Axis = Literal["conformance", "content_quality", "monetization", "compliance"]
Verdict = Literal["PUBLISH", "REJECT"]   # no REVISE — see §2.2

@dataclass
class AxisReport:
    axis: Axis
    score: float                    # 0.0 – 10.0
    passed: bool
    checklist: list[dict]           # [{item, passed, expected, actual, note}]
    evidence: dict                  # machine-readable diagnostic data

@dataclass
class EditorialVerdict:
    verdict: Verdict
    axis_reports: list[AxisReport]
    blocking_axes: list[Axis] = field(default_factory=list)
    article_id: int | None = None
    blueprint_id: str | None = None   # which Pattern Library blueprint was used

    def to_json(self) -> dict: ...
    @classmethod
    def from_json(cls, data: dict) -> "EditorialVerdict": ...
```

### 2.2 No automated revision loop (deliberate)

The Editor does **not** send articles back for rewrite. Verdict is binary:
`PUBLISH` (goes to human review queue) or `REJECT` (drops to human review
queue with a "rejected by editor" flag and the full axis report).

Rationale: given PR #6 puts the human in the loop anyway, automated
revision is redundant and expensive. The human reviewer with Claude Code
is the revision engine. Later — after 20+ published articles give us
empirical data on what fixes actually work — we can revisit automated
revision as a separate PR.

This dramatically simplifies the EditorCrew and eliminates the need for
a ThirdCycleResolver, axis-scoped revision routing, or retry-budget state.

### 2.3 Axis implementations

Four sub-agents inside EditorCrew, each emitting an `AxisReport`:

**Conformance (most important axis).** Compares the article to the active
Blueprint (from PR #5a; stub until then). Checklist items:
- word_count within blueprint target range
- H2 count within blueprint target range
- required section types present (comparison table, FAQ, intro hook,
  etc., per blueprint)
- target keyword density within range
- feature image present if blueprint specifies
- schema markup present if blueprint specifies
- internal link count ≥ blueprint minimum
- gap-opportunity addressed (article covers at least one
  `coverage_gap` from the blueprint)

Each item is deterministic and returns pass/fail with the actual vs.
expected value. The LLM is only consulted for fuzzy checks (e.g. "is the
FAQ answering a real buyer question?"); structural checks are pure code.

**Content Quality.** A lighter, cheaper LLM pass — does the article read
well, is it internally consistent, does it actually address the stated
topic. Deliberately not trying to measure "is this SEO-optimized" (the
Conformance axis does that via real data).

**Monetization.** Structural checklist only (no LLM judgment):
- affiliate link density (≤ 1 per ~300 words)
- first CTA within first 2 paragraphs
- `rel="sponsored nofollow noopener"` on every affiliate link
- disclosure block present
- no more than 1 affiliate per section

**Compliance.** LLM + rules:
- no prohibited medical/financial guarantee language
- affiliate disclosure present
- sources cited for factual claims

### 2.4 Flow integration

In `core/crewai_system/blog_creation_flow.py`:

- After EditorCrew runs, parse `EditorialVerdict`.
- Persist: `Article.editorial_verdict` = `"PUBLISH"` or `"REJECT"`.
- Write the full report to `editorial_reports` table (created in PR #3;
  until then write to `Article.last_verdict_json` as a TEXT column).
- Set `Article.current_stage = "awaiting_human_review"` regardless of
  verdict — the human always sees it.
- Flow terminates. No loop.

### 2.5 Blueprint stub (until PR #5a)

Create `core/crewai_system/contracts/blueprint.py` with the target shape,
and a stub loader that returns a hand-written blueprint keyed by niche.
This keeps PR #2 standalone and unblocks PR #6 to build the UI before
PR #5a is done.
```python
@dataclass
class Blueprint:
    id: str
    niche_id: int
    target_query_cluster: list[str]
    word_count_range: tuple[int, int]
    h2_count_range: tuple[int, int]
    required_sections: list[str]      # e.g. ["intro_hook","comparison_table","faq","verdict"]
    target_keyword_density: tuple[float, float]
    min_internal_links: int
    coverage_gaps: list[str]          # topics the winners don't address well
    source_urls: list[str]            # empty in stub; filled by PR #5a
    confidence_tier: Literal["high", "medium", "low"]
```

## Acceptance tests

`automated-blog-system/test_editor_verdict.py`:

1. **Verdict schema round-trip.** `EditorialVerdict.to_json()` ↔
   `from_json()` is lossless.
2. **Conformance axis is deterministic.** Given a fixture article and a
   stub blueprint, Conformance axis returns identical `AxisReport` on
   two successive runs (no LLM involved in structural checks).
3. **PUBLISH gate.** An article that passes all axes gets
   `editorial_verdict == "PUBLISH"` persisted.
4. **REJECT gate.** An article missing a required section gets
   `editorial_verdict == "REJECT"` + populated `blocking_axes`.
5. **Terminal state.** After EditorCrew,
   `Article.current_stage == "awaiting_human_review"` regardless of
   verdict.

Green: `pytest -q test_editor_verdict.py && pytest -q test_ghost_publisher.py -k "not live"`.

---

# PR #3 — Cost metering + stage observability + Alembic

## Why this PR exists

Observability and cost control. This is not about restart-after-crash —
CrewAI flows are synchronous function calls; if a run dies, you re-run.
This is about:

- Knowing what each article cost in dollars, down to the stage.
- Persisting every stage's output so the human reviewer (and future
  feedback loop) can see research evidence, strategy decisions, etc.
- Introducing Alembic so schema evolution stops being one-shot scripts.

## Scope

### 3.1 Introduce Alembic

- Add to `automated-blog-system/requirements.txt`:
```
  Flask-Migrate>=4.0.0
  alembic>=1.13.0
```
- `flask db init` from the venv with `FLASK_APP=src.main`.
- Generate baseline migration matching current schema (including PR #1's
  Ghost columns). Edit by hand if autogen gets it wrong.
- Convert `scripts/migrate_add_ghost_columns.py` to a no-op shim that
  prints "Use `flask db upgrade` instead."

### 3.2 Cost metering

`automated-blog-system/src/services/cost_meter.py`:
```python
class CostMeter:
    def record(article_id: int, stage: str, model: str,
               prompt_tokens: int, completion_tokens: int) -> Decimal: ...
    def total_for_article(article_id: int) -> Decimal: ...
    def total_for_month(month: str) -> Decimal: ...  # "YYYY-MM"
```

- Rate card in `services/model_rates.py` (cents per 1K tokens, per
  model). Start with gpt-4o-mini, text-embedding-3-small, and whatever
  else the pipeline uses.
- Writes to a new `cost_events` table: `(id, article_id, stage, model,
  prompt_tokens, completion_tokens, cost_usd, created_at)`.
- Wrap every LLM call site in CrewAI crews with a `with CostMeter.track(article_id, stage):`
  context manager that parses the `usage` field from the OpenAI response.

### 3.3 Budget cap

- Per-article default budget: `Article.cost_budget_usd = 5.00`.
- Monthly cap from `GOALS.md`: $100. Stored in a `budgets` table:
  `(month, cap_usd, spent_usd)`.
- New endpoint `GET /api/budget/status` returns monthly spent vs. cap +
  per-niche breakdown.
- Before starting any new flow, check monthly cap. If reached, refuse to
  start; log and notify (in-app only for now).
- Per-article: a `before_stage` hook halts the article (sets
  `current_stage = "halted_budget"`) if `cost_usd > cost_budget_usd`.
  The article goes to the human review queue with a budget-halt flag.

### 3.4 Stage output persistence

New Alembic migration adds to `articles`:
```
current_stage          String(30)   default 'stage_0'
stage_status           String(20)   default 'pending'
cost_usd               Numeric(10,4) default 0
cost_budget_usd        Numeric(10,4) default 5.00
research_report_json   Text         nullable
strategy_json          Text         nullable
draft_sections_json    Text         nullable
monetization_map_json  Text         nullable
last_verdict_json      Text         nullable
blueprint_id           String(64)   nullable    # FK to Blueprint (PR #5a)
last_error             Text         nullable
last_transition_at     DateTime
```

Also drop the dead `wordpress_post_id` column in the same migration.

New `editorial_reports` table:
```
id          Integer PK
article_id  Integer FK -> articles.id
verdict     String(20)
report_json Text
blueprint_id String(64) nullable
created_at  DateTime
```

### 3.5 Flow writes state on every transition

In `BlogCreationFlow`, each stage:
- Loads the current Article row.
- Calls the crew.
- Writes the stage output to its JSON column + sets `current_stage` +
  `stage_status` + bumps `cost_usd` via the CostMeter.
- Commits.

## Acceptance tests

`automated-blog-system/test_observability.py`:

1. **Alembic round-trip.** `flask db upgrade` from empty produces the
   current schema. `flask db downgrade -1` reverses the most recent
   migration.
2. **Cost metering.** Seed a fake LLM call with known token counts;
   assert `cost_events` row created, `Article.cost_usd` incremented
   correctly per the rate card.
3. **Per-article budget halt.** Set `cost_budget_usd = 0.01`; run a
   single stage; assert the flow halts and
   `current_stage == "halted_budget"`.
4. **Monthly cap refusal.** Pre-populate `budgets` row for the current
   month at cap; attempt to start a new flow; assert refusal.
5. **Stage outputs persist.** Run a full pipeline (crews mocked);
   inspect Article row — `research_report_json`, `strategy_json`,
   `draft_sections_json`, `last_verdict_json` all populated.

Green: all prior + `pytest -q test_observability.py`.

---

# PR #4 — CRUD completion + dashboard with pattern/cost visibility

## Why this PR exists

Without a real dashboard showing `editorial_verdict`, `cost_usd`,
`current_stage`, and the growing Pattern Library (coming in PR #5a), none
of the preceding work is usable. This PR finishes CRUD and builds the
minimum viable dashboard that exposes the system's state.

## Scope

### 4.1 Backend CRUD

- Complete `POST/PUT/PATCH/DELETE` for Article, Niche, Product.
- Soft-delete Article (set `status = "archived"`).
- List endpoints accept `?status=`, `?editorial_verdict=`,
  `?current_stage=`, `?niche_id=`, `?limit=`, `?offset=`.
- `GET /api/articles/<id>/stage-outputs` returns the four JSON stage
  columns so the dashboard can render them.

### 4.2 Frontend

Update `blog-frontend/src/components/`:

- **Dashboard.jsx:** counts by `current_stage` and `editorial_verdict`;
  monthly cost vs. cap bar; list of articles in `awaiting_human_review`.
- **ArticlesSimple.jsx:** add columns `current_stage`, `editorial_verdict`,
  `cost_usd`, `published_url` (link when present).
- **ArticleDetail.jsx (new):** tabs for Research, Strategy, Draft,
  Monetization Map, Editorial Report. Each tab pretty-prints the
  corresponding `*_json` column.

No inline editing yet — that's PR #6.

### 4.3 API client

`blog-frontend/src/services/api.js` gets typed wrappers (JSDoc) for all
new endpoints. Remove scattered `fetch` calls from components.

## Acceptance tests

Backend: `test_article_crud.py` covers create/list/update/archive/filter.

Frontend: at minimum one RTL test per new component rendering mocked
data. If heavier test infra feels premature, a manual QA checklist in
the PR description is acceptable — but backend CRUD tests are mandatory.

Green: all prior + `pytest -q test_article_crud.py`.

---

# PR #5a — SERP Forensics + Pattern Library

## Why this PR exists

This is the heart of the system — the thing that makes it distinctive
and defensible. Everything before this PR has been plumbing; this is the
first PR that makes the agents genuinely smart.

## Scope

### 5a.1 SERP Forensics service

`automated-blog-system/src/services/serp_forensics.py`:
```python
class SerpForensics:
    def pull_serp(self, query: str, k: int = 10) -> list[SerpResult]:
        """Serper API call. Returns top-k organic URLs + metadata."""

    def profile_url(self, url: str) -> ArticleProfile:
        """Firecrawl → structured extraction → profile dict."""

    def aggregate(self, profiles: list[ArticleProfile]) -> Blueprint:
        """Per-field aggregates (median, IQR, modal) + confidence tiers."""

    def identify_gaps(
        self, profiles: list[ArticleProfile], query_cluster: list[str]
    ) -> list[CoverageGap]:
        """Find questions/sub-topics under-addressed in the top 10."""
```

`ArticleProfile` fields (pure structure, no judgment):
```
url, title, word_count, h1, h2_headings[], h3_headings[],
section_count, first_h2_position, has_comparison_table,
has_faq, has_tldr, has_schema_markup, schema_types[],
internal_link_count, external_link_count, affiliate_link_count,
affiliate_link_positions[], image_count, first_image_position,
meta_description, target_keyword, keyword_density,
last_updated_at, reading_grade_level, intro_pattern_type,
cta_positions[], source_attribution_count
```

Profile extraction is a mix of:
- Firecrawl structured extraction (markdown + metadata).
- BeautifulSoup parsing for structural features.
- A small LLM call per URL for fuzzy classification (intro_pattern_type,
  section type labels) — keep tight and cached.

### 5a.2 Confidence tiering

The aggregator classifies each Blueprint field:

- **high** — ≥ 80% of top-10 agree within tight bounds (e.g. all have
  comparison tables, all have FAQ). Emulate strictly.
- **medium** — clustered but with variance (e.g. word count 1800–2800).
  Use as a target range, not a hard constraint.
- **low** — no clear pattern. Do not emulate; leave to Creation's
  judgment.

Confidence gets reported to Editorial, which weights the Conformance
axis accordingly — missing a high-confidence feature is a fail; missing
a low-confidence one is not.

### 5a.3 Pattern Library data model

New Alembic migration:
```
blueprints
  id                    String(64) PK
  niche_id              Integer FK -> niches.id
  target_query_cluster  Text (JSON list)
  profile_aggregate     Text (JSON) — the full aggregate
  coverage_gaps         Text (JSON list)
  source_urls           Text (JSON list)
  confidence_tiers      Text (JSON field→tier mapping)
  generated_at          DateTime
  generated_cost_usd    Numeric(10,4)
  version               Integer default 1
  parent_blueprint_id   String(64) nullable   # previous version

serp_profiles
  id                    Integer PK
  url                   String(500)
  query                 String(500)
  profile_json          Text
  fetched_at            DateTime
  # dedupe by (url, query) within a freshness window
```

### 5a.4 Integration

- New stage **Stage 0.5 — Blueprint Selection** runs between Research
  and Strategy. Inputs: niche, product, target query cluster. Looks up
  the freshest matching Blueprint; if stale or missing, triggers
  `SerpForensics` to build a new one. Attaches `blueprint_id` to the
  Article row.
- `ContentStrategyCrew` reads the Blueprint and produces a concrete
  article outline that hits the high-confidence patterns and addresses
  at least one `coverage_gap`.
- `ContentCreationCrew` writes to that outline.
- `EditorCrew`'s Conformance axis (from PR #2) now has a real blueprint
  to check against — the stub from PR #2 is replaced.

### 5a.5 Freshness policy

Blueprints expire after 30 days (configurable per niche, because
trending niches move faster than evergreen). Stale Blueprint → refresh
before use. Log cost of refresh to the parent Article's `cost_usd`.

## Acceptance tests

`test_serp_forensics.py`:

1. **Profile extraction is deterministic** for a given HTML snapshot
   (fixture file, Firecrawl mocked).
2. **Aggregation produces expected confidence tiers** for a crafted set
   of 10 profiles with known distributions.
3. **Gap identification** finds planted gaps in a fixture set.
4. **Blueprint persists and rehydrates correctly** via Alembic.
5. **Stage 0.5 integration:** flow correctly loads fresh Blueprint,
   triggers refresh when stale, and attaches `blueprint_id` to Article.

Green: all prior + `pytest -q test_serp_forensics.py`.

## Out of scope for PR #5a

- Embedding-based retrieval over profile contents (PR #5b).
- Cross-niche pattern transfer learning (future).
- Competitor backlink analysis (would need Ahrefs/SEMrush; future).

---

# PR #5b — LanceDB retrieval unification

## Why this PR exists

With the Pattern Library populated, the existing naive token-overlap
retrieval in `knowledge_base.py` becomes a bottleneck for everything:
Research agents can't efficiently query profile corpuses, Editorial can't
efficiently find similar past articles for conformance comparison. This
PR replaces it with LanceDB and unifies everything behind one retrieval
interface.

## Scope

### 5b.1 Single retrieval interface

`automated-blog-system/src/services/retrieval.py`:
```python
def retrieve(
    query: str,
    collection: Literal["docs", "profiles", "research_harvest", "own_articles"],
    k: int = 8,
    filters: dict | None = None,
) -> list[RetrievedChunk]
```

Hybrid search: LanceDB vector + BM25 lexical, weighted merge (start
0.7/0.3). Collections:

- `docs` — `/docs` folder content (static seed).
- `profiles` — serialized `ArticleProfile` fields from SERP forensics.
- `research_harvest` — dynamic research outputs from Research crew.
- `own_articles` — our own published articles for self-retrieval.

### 5b.2 Indexing

- `reindex_docs()` on startup if `/docs` hash changed.
- `ingest_profile(profile)` called by SERP forensics for each profiled URL.
- `ingest_research(harvest)` called by Research crew post-stage-0.
- `ingest_own_article(article)` called on publish.

Chunking: 400–800 tokens, 50-token overlap, split on H2 for markdown.
Embed with `text-embedding-3-small`, cost tracked via PR #3's CostMeter.

### 5b.3 Consumers

- Research crew uses `retrieve(q, "profiles")` to find structural
  patterns in prior SERPs.
- Editor's Conformance axis uses `retrieve(profile_summary, "own_articles")`
  to compare against our own published winners.
- Remove `knowledge_base.py`'s token-overlap code entirely.

### 5b.4 Retrieval eval harness

`automated-blog-system/eval/retrieval_eval.py`:

20 hand-crafted queries with ground-truth source URLs. Metrics: nDCG@8,
Recall@8. Before/after comparison against the token-overlap baseline
(capture baseline once before the switch).

## Acceptance tests

`test_retrieval.py`:

1. Chunking round-trip.
2. Index ingest + retrieve returns seeded chunks for exact queries.
3. Agent-scope filters work.
4. Retrieval eval shows nDCG@8 and Recall@8 improvement over baseline
   — if not, stop and ask user before merging.

Green: all prior + `pytest -q test_retrieval.py`.

---

# PR #6 — Human-in-the-loop review and publish/edit UI

## Why this PR exists

Every article passes through the human, always. The pipeline's terminal
state is `awaiting_human_review`. This PR is the UI surface that turns
reviewer intent into Ghost writes.

## Scope

### 6.1 Backend routes

New file `automated-blog-system/src/routes/review.py`, registered at
`/api/review` in `main.py` following the same try/except pattern used
for the other blueprints.

#### Route list
```
GET    /api/review/queue
GET    /api/review/<article_id>
PATCH  /api/review/<article_id>
POST   /api/review/<article_id>/publish
POST   /api/review/<article_id>/unpublish
GET    /api/review/<article_id>/ghost
POST   /api/review/<article_id>/pull-from-ghost
POST   /api/review/<article_id>/push-to-ghost
```

#### `GET /api/review/queue`

Returns articles awaiting human review. Filter:
`current_stage == "awaiting_human_review"` AND `status != "published"`.

Response shape per article:
```json
{
  "id": 42,
  "title": "...",
  "niche_id": 3,
  "niche_name": "SMB Cybersecurity",
  "editorial_verdict": "PUBLISH",
  "current_stage": "awaiting_human_review",
  "word_count": 2387,
  "section_count": 8,
  "cost_usd": "0.47",
  "updated_at": "2026-04-24T10:22:00Z",
  "editorial_report_summary": {
    "verdict": "PUBLISH",
    "axis_scores": {
      "conformance": 8.4,
      "content_quality": 7.9,
      "monetization": 7.1,
      "compliance": 10.0
    },
    "blueprint_id": "bp_smb_cybersec_v3"
  }
}
```

Query params: `?niche_id=`, `?editorial_verdict=` (PUBLISH | REJECT),
`?limit=`, `?offset=`, `?sort=updated_at|cost_usd`.

#### `GET /api/review/<article_id>`

Returns the full article payload plus everything the review UI needs to
render the editor and the right-hand panels without a second round trip:
```json
{
  "article": { /* full Article.to_dict() */ },
  "headless_contract": { /* Article.to_headless_contract() */ },
  "ghost_preview": {
    "title": "...",
    "html": "<p>...</p>",
    "status": "published",
    "tags": [{"name": "vpn"}],
    "meta_title": "...",
    "meta_description": "...",
    "feature_image": null
  },
  "editorial_report": { /* full EditorialVerdict JSON from editorial_reports */ },
  "blueprint": {
    "id": "bp_smb_cybersec_v3",
    "profile_aggregate": { /* ... */ },
    "confidence_tiers": { /* field -> tier mapping */ },
    "coverage_gaps": ["..."]
  },
  "stage_outputs": {
    "research_report": { /* from research_report_json */ },
    "strategy": { /* from strategy_json */ },
    "draft_sections": { /* from draft_sections_json */ },
    "monetization_map": { /* from monetization_map_json */ }
  },
  "cost_breakdown": [
    {"stage": "stage_0_research", "cost_usd": "0.08"},
    {"stage": "stage_1_strategy", "cost_usd": "0.04"},
    {"stage": "stage_2_creation", "cost_usd": "0.29"},
    {"stage": "stage_3_editorial", "cost_usd": "0.06"}
  ],
  "ghost_sync": {
    "post_id": null,
    "published_url": null,
    "last_sync_hash": null,
    "drift_detected": false
  }
}
```

`ghost_preview` is produced server-side by calling
`GhostService._article_to_post(article.to_headless_contract(), status="published")`
so the UI renders the exact HTML Ghost will receive.

404 if article not found. 403 if article is not in a reviewable state
(e.g. `current_stage == "stage_2_in_progress"`).

#### `PATCH /api/review/<article_id>`

User edits before publish. Accepts any subset of these fields:

- `title` (string)
- `slug` (string)
- `content` (HTML string, for simple-editor mode)
- `sections` (array of `{heading, content}` for structured-editor mode)
- `summary` (string)
- `meta_description` (string, max 160 chars — validate)
- `keywords` (array of strings, max 10 — validate)
- `calls_to_action` (array of `{type, target, anchor}`)
- `meta.feature_image` (URL)
- `meta.meta_title` (string)

Validation rules:
- `meta_description` ≤ 160 chars; warn but don't reject < 120.
- `keywords` ≤ 10 items.
- CTA targets must be valid URLs.
- If `sections` is provided, it replaces `content` (the app uses
  `sections` when present and falls back to `content` otherwise —
  matches `GhostService._sections_to_html` behavior).

On success: write to the Article row, bump `updated_at`, return the
updated `/api/review/<id>` payload (same shape as GET). Do NOT write to
Ghost. This is a local-only edit.

If the article already has a `ghost_post_id`, set a local
`has_unpushed_changes` flag (backed by comparing `last_ghost_sync_hash`
to the current content hash — no extra column needed).

#### `POST /api/review/<article_id>/publish`

**The only human-triggered publish path.** Preconditions:

1. `editorial_verdict == "PUBLISH"` — else return 409 with the PR #1
   standard error shape.
2. No uncommitted in-flight PATCH (server-side: reject if request
   arrived while a PATCH is mid-write; use a simple per-article lock).
3. `GHOST_API_URL` + `GHOST_ADMIN_KEY` env vars are set — else 502.

Internally just calls the existing
`POST /api/publisher/publish/<id>` logic (don't duplicate code; import
the function or refactor publisher into a `publish_article_now(article)`
helper that both routes call).

On success, response:
```json
{
  "success": true,
  "article_id": 42,
  "post_id": "661a...",
  "url": "https://your-ghost.example.com/best-vpn-smb-2026/",
  "ghost_status": "published",
  "last_sync_hash": "sha256:..."
}
```

Also updates on the Article row:
- `status = "published"`
- `ghost_post_id`, `published_url`
- `ghost_updated_at` (new DateTime column — add in PR #6's small
  Alembic migration)
- `last_ghost_sync_hash` (new String column — add in the same
  migration)
- `current_stage = "published"`

#### `POST /api/review/<article_id>/unpublish`

Calls `GhostService.update_article(post_id, payload_with_status_draft)`
to set the Ghost post to `status="draft"`. Locally sets
`Article.status = "draft"` and keeps `ghost_post_id` / `published_url`
so re-publishing uses the same post.

Returns:
```json
{"success": true, "ghost_status": "draft"}
```

409 if article has no `ghost_post_id`.

#### `GET /api/review/<article_id>/ghost`

Pulls the live post from Ghost via a new `GhostService.fetch_post()`
method and returns it alongside drift analysis:
```json
{
  "local": { /* headless_contract from local DB */ },
  "ghost": {
    "title": "...",
    "html": "<p>...</p>",
    "updated_at": "2026-04-23T14:00:00Z",
    "tags": [...],
    "meta_description": "..."
  },
  "drift_detected": true,
  "diverging_fields": ["title", "html"],
  "local_hash": "sha256:...",
  "ghost_hash": "sha256:...",
  "last_sync_hash": "sha256:..."
}
```

Drift logic: compute `sha256(title + "\n" + html + "\n" +
meta_description + "\n" + sorted_tags_joined)` for both sides and
compare. `diverging_fields` does a field-by-field comparison (exact
match for strings, set-equality for tags).

Cache the Ghost fetch for 60 seconds per `post_id` to avoid hammering
the API during dashboard fan-out.

409 if article has no `ghost_post_id`.

#### `POST /api/review/<article_id>/pull-from-ghost`

Overwrites the local Article row with Ghost's current version. Before
overwriting, snapshots the current local state to an
`article_revisions` table:
```
id           Integer PK
article_id   Integer FK -> articles.id
source       String(20)    # "pre_pull_from_ghost" | "pre_manual_edit" | ...
snapshot_json Text          # full to_dict() at time of snapshot
created_at   DateTime
```

(If PR #3 didn't create this table, PR #6 creates it via a small
Alembic migration.)

After pull:
- `Article.title`, `content` (or `sections`), `meta_description`,
  `keywords`, `feature_image` = Ghost values.
- `last_ghost_sync_hash` = fresh Ghost hash.
- `ghost_updated_at` = Ghost's `updated_at`.

Response:
```json
{
  "success": true,
  "revision_id": 17,
  "pulled_fields": ["title", "html", "tags"]
}
```

#### `POST /api/review/<article_id>/push-to-ghost`

Pushes local edits to Ghost via `GhostService.update_article(post_id,
article.to_headless_contract())`. Same verdict gate as `/publish` —
refuses unless `editorial_verdict == "PUBLISH"`.

Before push, snapshots current Ghost state to `article_revisions` with
`source = "pre_push_to_ghost"`, in case the user wants to revert.

Response:
```json
{
  "success": true,
  "article_id": 42,
  "post_id": "661a...",
  "url": "https://your-ghost.example.com/...",
  "ghost_status": "published",
  "last_sync_hash": "sha256:...",
  "revision_id": 18
}
```

409 if no `ghost_post_id`. 502 if Ghost returns an error (surface
Ghost's message in the `error` field).

#### Errors — standard shape

All error responses follow PR #1's convention:
```json
{"success": false, "error": "human-readable message"}
```

Status codes:
- 400 — validation failure on PATCH.
- 403 — article not in a reviewable state.
- 404 — article not found.
- 409 — verdict gate failure or missing `ghost_post_id` where required.
- 502 — upstream Ghost API failure (surface Ghost's message).

#### Concurrency

Use a simple in-process per-article lock (`threading.Lock` keyed by
`article_id`) around PATCH, publish, pull-from-Ghost, and push-to-Ghost.
Good enough for single-instance Flask; PR #7+ can revisit if we move to
a multi-process WSGI server.

#### New `GhostService` methods

Add to `automated-blog-system/src/services/ghost_service.py`:
```python
def fetch_post(self, post_id: str) -> dict:
    """Return the full Ghost post JSON for post_id."""
    return self._get(f"/ghost/api/admin/posts/{post_id}/")["posts"][0]

def set_status(self, post_id: str, status: str) -> PublishResult:
    """Flip status (published | draft | scheduled) without changing content."""
    current = self.fetch_post(post_id)
    body = {
        "posts": [{
            "status": status,
            "updated_at": current["updated_at"],
        }]
    }
    return self._send("PUT", f"/ghost/api/admin/posts/{post_id}/", body)
```

#### Small Alembic migration for PR #6
```
article:
  + ghost_updated_at       DateTime nullable
  + last_ghost_sync_hash   String(128) nullable
  + has_unpushed_changes   Boolean default False    # optional convenience

article_revisions:
  id            Integer PK
  article_id    Integer FK -> articles.id
  source        String(40)
  snapshot_json Text
  created_at    DateTime
```

### 6.2 Pre-publish review screen

`blog-frontend/src/components/ArticleReview.jsx`:

- Left column (55%): tabbed editor — Rich text (Tiptap), Sections
  (drag-reorderable), CTAs (table), SEO (meta + tags).
- Right column (45%): Editorial Report with axis pass/fail checklists;
  **Blueprint Conformance** panel showing expected vs. actual per field;
  **Ghost Preview** iframe with the final HTML payload; cost-so-far
  indicator.
- Footer: [Save Draft] [Publish to Ghost] [Unpublish] [Discard].
- Publish → confirm modal showing exact Ghost payload → POST to
  `/api/review/<id>/publish` → toast with live URL.
- Autosave PATCH every 30s while tab focused.
- Publish button disabled if verdict ≠ PUBLISH or unsaved edits.

### 6.3 Post-publish edit screen

`PublishedArticles.jsx` — list of `status='published'` articles with
drift indicator (● green / yellow / red).

Clicking a row reuses `ArticleReview.jsx` with:
- **Pull from Ghost** button.
- Primary action becomes **Push to Ghost**.
- Drift panel if Ghost diverges: Keep Local / Keep Ghost / Manual Merge
  (side-by-side diff via `react-diff-viewer-continued`).

### 6.4 Drift detection

Hash normalized (title + html + meta_description + tags) from both
sides, store on Article as `last_ghost_sync_hash`. Background refresh on
dashboard load (rate-limited, cap 4 parallel).

### 6.5 Remove direct-publish

The "Publish to Ghost" button from PR #4 becomes "Review & Publish" and
routes to `ArticleReview.jsx`. No one-click publish from list.

## Acceptance tests (PR #6 continued)

`test_review_routes.py`:

1. **Verdict gate on publish.** `POST /api/review/<id>/publish` returns
   409 for articles with `editorial_verdict != "PUBLISH"`.
2. **PATCH round-trip.** PATCH updates title + sections; subsequent GET
   reflects the change; `Article.to_headless_contract()` returns the
   updated payload.
3. **Publish path.** With Ghost mocked via `responses`, a PUBLISH-verdict
   article PATCHed and then published sends the edited content to Ghost
   (assert the request body).
4. **Pull-from-Ghost.** Mock Ghost returning a post with a changed title;
   pull-from-Ghost overwrites local title and records the prior state as
   a revision row.
5. **Drift.** Mock Ghost returning divergent HTML → `drift_detected: true`
   + non-empty diff summary.
6. **Push-to-Ghost.** Local edits since last sync are pushed via
   `GhostService.update_article`; `last_ghost_sync_hash` updates.
7. **No autonomous publish.** Grep check: the string `publish_article(`
   and the path `/api/publisher/publish/` may only appear inside
   `routes/review.py` and `routes/publisher.py`. Add a test that fails
   if any new call site appears elsewhere.

Frontend (RTL, one per flow):

1. Open review queue → open article → edit title → Save → persisted.
2. Attempt publish without saving → button disabled, warning shown.
3. Confirm-publish modal shows exact Ghost payload.
4. Published list shows drift indicator when Ghost returns divergent
   data (mocked).

Manual end-to-end (document in PR description):

1. Generate an article via the pipeline → lands in Review Queue.
2. Inline-edit the monetization CTA → Save → Publish.
3. Live Ghost URL opens with the edit visible.
4. Edit the Ghost post directly in Ghost Admin (title change).
5. Dashboard shows red drift indicator on that row.
6. Pull from Ghost → local matches; Push a new local edit → Ghost
   reflects it.

Green: all prior + `pytest -q test_review_routes.py` + the frontend suite.

## Out of scope for PR #6

- Real-time collaboration / multiplayer editing.
- Scheduled publish (easy later — Ghost supports `status=scheduled`).
- Rich media upload to Ghost (images still by URL; PR #8 if needed).
- Role-based permissions (TODO marker only).

## Library suggestions

- Rich text editor: **Tiptap** (headless, HTML in/out, ~80KB).
- Diff: **react-diff-viewer-continued**.
- Toasts: whatever the existing dashboard uses (check `package.json`).

---

# PR #7 — Performance Feedback Loop

## Why this PR exists

This is the PR that makes the system compound. Without it, every
article is a one-shot guess. With it, the Pattern Library's weights
shift based on what actually drove traffic and revenue *for your
niches, your audience, your affiliate programs.*

Short of this PR, you are emulating someone else's winners. After this
PR, you are learning from your own.

This PR should not start until at least ~20 articles have been
published (enough data for weak signal). Note that in `todo.md` so
Claude Code doesn't start it prematurely.

## Scope

### 7.1 Analytics ingestion

`automated-blog-system/src/services/analytics/` module with providers:

**`gsc_provider.py`** — Google Search Console API.
- OAuth flow for connecting a GSC property (user-initiated, one-time).
- Pull per-URL metrics (impressions, clicks, CTR, avg_position) daily
  for the trailing 28 days.
- Respect quota (1200 queries/min/user by default; we'll use <100).
- Store in `article_analytics_daily` table:
  `(id, article_id, date, source, impressions, clicks, ctr, avg_position,
    conversions, revenue_usd)`.

**`affiliate_provider.py`** — a pluggable base class with concrete
implementations per affiliate network. Start with Amazon Associates
and one other (user's choice — ShareASale, Impact, or CJ).
- Pull click-through and earnings data per tracking ID per day.
- Map tracking IDs back to `Article` rows.

**Daily ingest job** (cron or a simple APScheduler task inside the
Flask app) at 6 AM local time. Idempotent: re-running a day overwrites,
doesn't duplicate.

### 7.2 Per-article performance record

`article_performance` materialized view or rolled-up table, refreshed
after each ingest:
```
article_id
first_published_at
days_live
total_impressions_28d
total_clicks_28d
avg_ctr_28d
avg_position_28d
total_epc_28d              # earnings per click
total_revenue_28d
cost_usd                   # from PR #3's CostMeter
roi                        # revenue_28d / cost_usd
performance_tier           # 'winner' | 'mid' | 'loser' | 'tbd'
```

Tier thresholds are niche-configurable. Default: winner = top 20% by
ROI *within the same niche*, loser = bottom 20%, tbd = <14 days live.

### 7.3 Blueprint attribution

When an article is published, snapshot the Blueprint used (not just the
id — the full aggregate and confidence tiers). Store in
`article_blueprint_snapshot` table. This is the audit trail: "article X
was published against blueprint Y at version Z" is forever resolvable,
even if the Blueprint has since been regenerated.

### 7.4 Feedback correlation engine

`automated-blog-system/src/services/feedback_engine.py`:
```python
def compute_blueprint_effectiveness(niche_id: int, min_n: int = 10) -> dict:
    """For each Blueprint version used in this niche, compute the
    distribution of performance tiers of articles published against it.
    Returns per-field effect sizes: for each field in the Blueprint
    (word_count_range, has_comparison_table, etc.), compare performance
    of articles that conformed vs. articles that didn't.
    """

def propose_blueprint_updates(niche_id: int) -> list[BlueprintProposal]:
    """Based on effectiveness analysis, propose adjustments to field
    target ranges and confidence tiers. A 'proposal' is not auto-applied
    — it goes to a human-review queue (see 7.5)."""
```

Methodology (keep it simple and honest for v1):
- Group articles by which Blueprint version they were published against.
- For each field, bucket articles by conformance (yes/no or
  in-range/out-of-range).
- Compare median ROI per bucket. Effect size = (median_roi_in_bucket -
  median_roi_out) / median_roi_overall.
- Require `min_n = 10` articles per bucket before reporting — below
  that, signal is noise.
- Surface effects with confidence intervals (bootstrap with 1000
  resamples), not point estimates.

This is deliberately frequentist and simple. Fancier causal inference
(uplift modeling, propensity matching) comes only if the simple version
proves useful.

### 7.5 Proposals, not auto-updates

Effectiveness findings produce **BlueprintProposal** rows, never direct
Blueprint mutations. Each proposal has:
```
proposal_id
niche_id
blueprint_field            # e.g. 'word_count_range'
current_value              # e.g. (1800, 2800)
proposed_value             # e.g. (2200, 3200)
evidence                   # JSON: sample size, effect size, CI, articles used
generated_at
status                     # 'pending' | 'accepted' | 'rejected'
reviewed_by                # user id
reviewed_at
```

A new dashboard view `FeedbackProposals.jsx` surfaces pending
proposals with full evidence. User accepts or rejects; accepted
proposals create a new Blueprint version via the PR #5a machinery.

This is the loop: articles published → performance measured → effects
computed → proposals surfaced → user accepts → new Blueprint version →
future articles use the updated Blueprint → performance measured →
repeat.

### 7.6 Dashboard additions

Extend `Dashboard.jsx`:

- Revenue-this-month and cost-this-month KPI cards.
- ROI leaderboard of top 10 articles.
- "Proposals Awaiting Review" badge with count.
- Per-niche ROI sparkline.

## Acceptance tests

`test_feedback_engine.py`:

1. **GSC ingest round-trip** (API mocked). Pulling a day's data creates
   `article_analytics_daily` rows; re-running upserts, doesn't duplicate.
2. **Performance tier assignment.** Seeded articles with known revenue
   distributions receive correct tiers per niche.
3. **Effectiveness calculation.** Fixture dataset with a known effect
   (articles with comparison tables outperform 2x in ROI) produces
   an effect-size value within expected bounds + CI that excludes zero.
4. **Min-n gating.** With fewer than 10 articles per bucket, the engine
   returns no proposals for that field (but still reports the data).
5. **Proposal lifecycle.** Creating a proposal, accepting it, verifying
   a new Blueprint version is created with the proposed value, and the
   original Blueprint is retained for historical attribution.

Green: all prior + `pytest -q test_feedback_engine.py`.

## Out of scope for PR #7

- Auto-accepting proposals. Never.
- Cross-niche pattern transfer (if comparison tables win in Niche A,
  does that predict wins in Niche B?) — future work.
- Multi-armed bandit experimentation (A/B'ing blueprints on purpose).
- LLM-driven proposal generation (use statistics, not vibes).

---

# Cross-cutting conventions

## Logging

`log = logging.getLogger(__name__)` pattern already in `ghost_service.py`.
No `print()` outside startup banners in `main.py`.

## Error handling

Routes return `{"success": bool, "error": str}` at 4xx/5xx (matches
existing `blog.py`). Internal raises are typed exceptions
(`GhostPublishError`, `BudgetExceeded`, `BlueprintStale`, etc.).

## Secrets

Read env vars lazily inside service `__init__`, never at import time.
Pytest must run with no secrets set.

## Git hygiene

- One logical change per commit within a PR.
- Commit message: `pr<N>: <short imperative summary>`.
- Final commit of each PR updates `todo.md` marking shipped.

## When stuck

Don't invent architectural decisions. Stop and ask the user with two or
three concrete options. Examples worth surfacing rather than deciding:

- Exact rate-card values in PR #3 (use published prices or empirical
  averages).
- Which second affiliate network to integrate first in PR #7.
- How aggressive to be about Blueprint freshness (30 days? 14 for
  volatile niches?).
- Whether to split Article into its own module (deferred; propose in
  PR #3 if the file grows painful).

## Done means done

A PR is complete only when:

1. Its acceptance tests are green.
2. All prior PRs' tests are still green.
3. `todo.md` is updated.
4. `README.md` architecture section reflects any new service/route.
5. A short CHANGELOG-style summary prints at the end of the Claude Code
   session.

---

# The system, complete

After PR #7, the full loop looks like this:
```
  Niche declared + target query cluster
            │
            ▼
   ┌──────────────────┐
   │ SERP Forensics   │  (PR #5a)
   │ profile top 10   │
   │ aggregate + gaps │
   └────────┬─────────┘
            │  Blueprint (high/med/low confidence fields)
            ▼
   ┌──────────────────┐
   │ Content Strategy │  reads Blueprint, hits high-conf patterns,
   │                  │  exploits at least one coverage gap
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Content Creation │  writes to the outline, per Blueprint
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Editorial (PR#2) │  Conformance (vs. Blueprint) + Content Quality
   │                  │  + Monetization + Compliance
   │                  │  → EditorialVerdict: PUBLISH | REJECT
   └────────┬─────────┘
            │
            ▼
  ┌────────────────────┐
  │ awaiting_human     │  terminal state — always
  │ _review            │
  └────────┬───────────┘
           │  (human clicks Publish)
           ▼
   ┌──────────────────┐
   │ Ghost CMS        │  (PR #1 + PR #6)
   │ live URL         │
   └────────┬─────────┘
            │
            ▼  daily
   ┌──────────────────┐
   │ Analytics Ingest │  GSC + affiliate networks  (PR #7)
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │ Feedback Engine  │  per-Blueprint-field effect sizes
   │                  │  → BlueprintProposals
   └────────┬─────────┘
            │  (human reviews proposals)
            ▼
    New Blueprint version → informs next article → loop
```

The system's intelligence lives in the data flywheel between the
Blueprint, the published article, the performance record, and the
feedback engine. Each turn of the wheel makes the Blueprint a little
sharper — not because the agents got smarter, but because the system's
empirical model of your niches got richer.

Everything before PR #7 is infrastructure. PR #7 is where compounding
starts.

---

# Recommended order of operations

1. **PR #2** — verdict schema + Conformance-axis stub. ~1–2 days.
2. **PR #3** — cost metering + stage observability + Alembic. ~2–3 days.
3. **PR #4** — CRUD + dashboard. ~2 days.
4. **Stand up Ghost** (user task, not Claude Code): spin up Ghost on the
   existing Hostinger VPS via docker-compose alongside Paperclip's
   traefik, OR use Ghost Pro at ~$9/mo. Set `GHOST_API_URL` +
   `GHOST_ADMIN_KEY`. Run `pytest -q test_ghost_publisher.py -k live`
   to verify.
5. **PR #5a** — SERP Forensics + Pattern Library. ~4–6 days. This is
   the big one.
6. **PR #5b** — LanceDB retrieval unification. ~2 days.
7. **PR #6** — Review + publish UI. ~3–4 days.
8. **Publish 20+ articles.** Real ones. Use the pipeline + review UI.
   This is the dataset PR #7 needs.
9. **PR #7** — Feedback Loop. ~4–5 days.

Total: ~3–4 focused weeks of build + however long it takes to
accumulate 20 published articles. Call it 6–8 weeks end-to-end if you're
working on this part-time.

Good luck.