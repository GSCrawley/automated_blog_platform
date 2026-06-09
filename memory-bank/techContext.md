# Tech Context — automated_blog_platform

> Updated 2026-06-01. Reflects the current Ghost / PR-based stack.

## Stack

- **Backend**: Python 3, Flask 3.1, SQLAlchemy, Flask-Migrate/Alembic.
  Dev DB is persistent SQLite at `automated-blog-system/data/`; Postgres-
  ready for prod.
- **Pipeline**: CrewAI (>=0.100) + crewai-tools. Research via Tavily,
  SerperDev, Firecrawl.
- **Retrieval**: LanceDB (>=0.18) for vector search.
- **Frontend**: React 19 + Vite, dev server on :5173, proxies `/api/*`
  to the backend.
- **Publishing**: Ghost Headless CMS, Admin API v5.
- **Optional**: Redis for the legacy agent pub/sub framework.

## Environment Variables (.env at repo root)

| Var | Purpose |
|-----|---------|
| `OPENAI_API_KEY` | Content gen, embeddings, AI product discovery |
| `TAVILY_API_KEY` | ResearchCrew real-time queries |
| `SERPER_API_KEY` | PR #5a SERP forensics |
| `FIRECRAWL_API_KEY` | Cleaner HTML extraction (optional; requests.get fallback) |
| `GHOST_API_URL` | Ghost blog base URL (`https://deskcred-com.ghost.io`) |
| `GHOST_ADMIN_KEY` | Ghost Admin API key (`id:hexsecret`) |
| `GHOST_CONTENT_API_KEY` | Ghost Content API key |
| `CREWAI_STORAGE_DIR` | CrewAI memory dir |
| `LANCEDB_PATH` | LanceDB tables (default `./data/lancedb`) |
| `REDIS_HOST` / `REDIS_PORT` | Optional legacy agent framework |
| `PIPELINE_ALLOW_TEMPLATE_FALLBACK` | `true` to allow off-niche template products in dev (default false) |

## Config Flags

- `USE_MOCK_DATA` in `src/config.py` — when `True`, trend analyzer +
  content generator return canned strings (no real API spend). Flip to
  `False` for real generation.
- `PIPELINE_ALLOW_TEMPLATE_FALLBACK` — guards the template product path.

## Dependencies

See `automated-blog-system/requirements.txt`. Notable: `crewai`,
`crewai-tools`, `tavily-python`, `lancedb`, `Flask-Migrate`, `alembic`,
`redis`, `openai`, `responses` (test HTTP mocking), `pytest`.

## Running Locally

See `RUN.md` for the authoritative runbook. TL;DR:

```bash
cd automated-blog-system
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
FLASK_APP=src.main:create_app flask db upgrade
python src/main.py          # backend :5000
# separate terminal:
cd blog-frontend && npm install && npm run dev   # :5173
```

## Tests

```bash
cd automated-blog-system && source venv/bin/activate
pytest -q test_ghost_publisher.py test_editor_verdict.py \
          test_observability.py test_article_crud.py \
          test_serp_forensics.py test_retrieval.py \
          test_review_routes.py -k "not live"
```

Live Ghost smoke (creates a real draft): set `GHOST_LIVE_TEST=1` plus
Ghost env vars, then `pytest -q test_ghost_publisher.py -k live`.

## Known Gotchas

- Niche creation auto-fires `NichePipelineService`, scaffolding products +
  articles in the background. A clean dev DB will not stay clean.
- WordPress columns/services are deprecated stubs.
