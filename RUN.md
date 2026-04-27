# Runbook

Common commands for local development. Paths assume you are in the repo
root unless noted. Last verified end-to-end on the `foundation-cleanup`
branch — see *Foundation smoke test* below.

## First-time setup

```bash
cd automated-blog-system
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
FLASK_APP=src.main:create_app flask db upgrade   # 0001 → 0002 → 0003
```

The migrations directory is `automated-blog-system/migrations/`. Three
revisions are applied:

- `0001` — baseline (PR #1 + PR #2 columns)
- `0002` — PR #3 observability (cost_events, budgets, editorial_reports,
  drops `wordpress_post_id`)
- `0003` — PR #5a Pattern Library (blueprints, serp_profiles)

PR #2's old one-shot `migrate_add_ghost_columns.py` and
`migrate_add_verdict_columns.py` are now no-op shims that point at
`flask db upgrade`.

## Running the system

The agent system + Redis are **optional** — `create_app()` logs a
warning and continues without them. None of PR #2–#5b depends on Redis.

```bash
# Terminal 1 — Flask backend on :5000
cd automated-blog-system
source venv/bin/activate
python src/main.py

# Terminal 2 — React frontend on :5173 (Vite dev server)
cd blog-frontend
npm install   # first time only
npm run dev

# (Optional) Terminal 3 — Redis if you want the legacy agent framework
redis-server
pip install redis      # the package isn't in requirements.txt yet
python start_agents.py
```

Backend listens on `0.0.0.0:5000`. Frontend dev server listens on `:5173`
and proxies `/api/*` to the backend via `VITE_API_BASE_URL` (defaults to
`http://127.0.0.1:5000/api`).

## Tests

```bash
cd automated-blog-system
source venv/bin/activate

# Full suite (PR #1 → PR #5b)
pytest -q test_ghost_publisher.py test_editor_verdict.py \
          test_observability.py test_article_crud.py \
          test_serp_forensics.py test_retrieval.py \
          test_knowledge_base.py -k "not live"

# Live Ghost smoke (creates a draft on a real Ghost instance)
export GHOST_API_URL="https://your-ghost.example.com"
export GHOST_ADMIN_KEY="<id>:<hex-secret>"
export GHOST_LIVE_TEST=1
pytest -q test_ghost_publisher.py -k live
```

## Foundation smoke test

A working setup should respond to all of these:

```bash
# Backend health
curl -s http://127.0.0.1:5000/api/blog/dashboard/stats | python -m json.tool
curl -s http://127.0.0.1:5000/api/budget/status | python -m json.tool

# Create a niche → auto-triggers the legacy NichePipelineService which
# scaffolds 5 mock products + articles in the background
curl -s -X POST http://127.0.0.1:5000/api/blog/niches \
  -H "Content-Type: application/json" \
  -d '{"name":"Cybersecurity SMB","description":"smoke","target_keywords":"vpn,smb"}'

# List articles (filter + pagination)
curl -s "http://127.0.0.1:5000/api/blog/articles?current_stage=awaiting_human_review&limit=20"

# PATCH partial update
curl -s -X PATCH http://127.0.0.1:5000/api/blog/articles/1 \
  -H "Content-Type: application/json" \
  -d '{"meta_description":"updated"}'

# Stage outputs (after the editor has run)
curl -s http://127.0.0.1:5000/api/blog/articles/1/stage-outputs | python -m json.tool

# Soft-delete (sets status='archived'; ?hard=1 for true delete)
curl -s -X DELETE http://127.0.0.1:5000/api/blog/articles/1
```

### Run the editor on a stored article

The four-axis editor isn't an HTTP endpoint yet (PR #6 is the review UI
that exposes it). Drive it from a Python shell against the running app:

```bash
python -c "
from src.main import create_app
from src.services.editorial_review import run_editorial_review
app = create_app()
with app.app_context():
    v = run_editorial_review(<article_id>)
    print(v.verdict, v.blocking_axes)
"
```

Expected side-effects on the Article row:

- `editorial_verdict` = `PUBLISH` or `REJECT`
- `current_stage` = `awaiting_human_review`
- `stage_status` = `complete`
- `last_verdict_json` populated
- `blueprint_id` set (DB blueprint if one exists for the niche, else PR #2 stub)
- An `editorial_reports` row written

## Publishing an article (manual)

PR #6 made the UI the only practical publish path; the legacy curl
recipe stays for scripts and live tests.

### UI flow (PR #6)

1. From `Articles`, find a row with verdict=`PUBLISH` → click
   **✅ Review & Publish**, or browse **Review Queue** in the sidebar.
2. The review screen shows the editor on the left (Content / SEO /
   Preview tabs) and the Editorial Report + cost panel on the right.
   Edit anything; **Save Draft** PATCHes locally without touching Ghost.
   Autosave runs every 30 s while the tab is focused.
3. Click **Publish to Ghost** → confirm modal shows the exact payload
   Ghost will receive (title, slug, tags, meta description, first 500
   chars of HTML) → confirm → the article moves to **Published**.
4. After publish, the **Published** screen shows a drift indicator per
   row. **Pull** overwrites the local copy with whatever's on Ghost
   (after snapshotting local). **Push** sends local edits back to Ghost
   (after snapshotting Ghost).

### CLI / scripted path

```bash
# Health check (verifies Ghost auth without publishing)
curl -X GET http://127.0.0.1:5000/api/publisher/health

# UI-equivalent publish path (PR #6 — same code as the UI uses)
curl -X POST http://127.0.0.1:5000/api/review/<article_id>/publish

# Direct PR #1 path — left in for scripted live tests; the dashboard no
# longer surfaces it
curl -X POST http://127.0.0.1:5000/api/publisher/publish/<article_id>

# Save as a draft instead (no review-route equivalent)
curl -X POST http://127.0.0.1:5000/api/publisher/draft/<article_id>
```

### Manual end-to-end (PR #6 acceptance)

The doc's PR #6 §6.7 manual E2E. Run with a real Ghost instance:

1. Generate (or hand-craft) an article that ends with verdict=`PUBLISH`
   and `current_stage='awaiting_human_review'`. Verify it shows up at
   `/review`.
2. Open it. Edit the Meta description in the SEO tab. Save. Reload —
   confirm the edit persisted.
3. Click Publish to Ghost → confirm. Live URL appears in the toast and
   on the article row.
4. In Ghost Admin, edit the post's title directly. Reload `/published`
   in the dashboard — the row's drift indicator turns red.
5. Click the row → in the review screen, the drift badge is visible.
   Click **Pull** on the Published page → confirm. Local now matches
   Ghost.
6. Make a local title edit + Save. Click **Push** on the Published page
   → confirm. Ghost reflects the local title; drift indicator returns
   to green.

## Useful env vars

| Var                 | What it unlocks                                                                                              |
|---------------------|--------------------------------------------------------------------------------------------------------------|
| `GHOST_API_URL`     | Base URL of the Ghost blog                                                                                   |
| `GHOST_ADMIN_KEY`   | Admin API key in `id:hexsecret` form                                                                         |
| `GHOST_LIVE_TEST`   | `1` to enable the live-Ghost pytest                                                                          |
| `OPENAI_API_KEY`    | Real CrewAI generation; LLM-injectable Editor axes; OpenAI embeddings via `make_openai_embedder()`           |
| `TAVILY_API_KEY`    | ResearchCrew tools                                                                                           |
| `SERPER_API_KEY`    | PR #5a SERP forensics. Without it, Stage 0.5 falls back to the most-recent DB blueprint or the PR #2 stub.   |
| `FIRECRAWL_API_KEY` | Cleaner HTML extraction during Blueprint refresh; plain `requests.get` is the fallback                       |
| `LANCEDB_PATH`      | Where PR #5b's LanceDB tables live (default `./data/lancedb`)                                                |
| `REDIS_HOST`        | Optional — only the legacy agent framework needs it                                                          |
| `REDIS_PORT`        | Defaults to 6379                                                                                             |

## Rolling back a PR

Every PR backs up its rewritten files to `.prN-backup/` preserving the
original path. To revert PR N's local changes (e.g. `pr3-observability`):

```bash
cp -r .pr3-backup/* .
FLASK_APP=src.main:create_app flask db downgrade <prev-revision>
```

## Known foundation gotchas

- **`redis` package not in `requirements.txt`.** `create_app()` logs
  `⚠️ Agent Manager initialization failed: No module named 'redis'` and
  serves requests fine. PR #2–#5b doesn't use the agent framework. Add
  `pip install redis` if you want it.
- **Niche creation auto-fires `NichePipelineService`.** `POST /api/blog/niches`
  scaffolds 5 mock products + 5 articles in the background (legacy
  behavior, predates this PR series). Tests use isolated in-memory DBs
  so it's hermetic for them, but a clean dev DB will not stay clean.
- **The editorial_review path isn't an HTTP endpoint yet.** PR #6 wires
  it. Today, drive it from a Python shell (recipe above).
- **`USE_MOCK_DATA = True`** in `src/config.py`. Trend analyzer + content
  generator return canned strings without real API calls. Flip to `False`
  with the appropriate keys set when you want real generation.
