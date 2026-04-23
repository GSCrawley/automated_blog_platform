# PR #1 — Ghost Publisher: install, migrate, test
```bash
# 1. Install new deps
cd automated-blog-system
pip install -r requirements.txt

# 2. Run the one-shot migration to add ghost_post_id / published_url /
#    editorial_verdict columns to the `articles` table.
python -m scripts.migrate_add_ghost_columns

# 3. Run the mocked unit tests (no Ghost instance required)
pytest -q test_ghost_publisher.py -k "not live"

# 4. (Optional, once you have a Ghost instance)
export GHOST_API_URL="https://your-ghost.example.com"
export GHOST_ADMIN_KEY="<id>:<hex-secret>"
export GHOST_LIVE_TEST=1
pytest -q test_ghost_publisher.py -k live

# 5. Manual end-to-end (once Ghost is configured + an Article exists with
#    editorial_verdict='PUBLISH'):
bash start_backend.sh
curl -X POST http://localhost:5001/api/publisher/health
curl -X POST http://localhost:5001/api/publisher/publish/<article_id>
```