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
