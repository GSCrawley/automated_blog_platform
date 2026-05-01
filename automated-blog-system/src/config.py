import os
from pathlib import Path

# Load project-root .env BEFORE any module reads os.getenv at import time.
# .env lives at the repo root, two parents up from this file:
#   <repo_root>/automated-blog-system/src/config.py  →  <repo_root>/.env
try:
    from dotenv import load_dotenv  # type: ignore

    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    _ENV_PATH = _PROJECT_ROOT / ".env"
    if _ENV_PATH.is_file():
        load_dotenv(_ENV_PATH, override=False)
except ImportError:
    # python-dotenv is optional in CI / production where vars come from the env.
    pass


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Persistent SQLite location (PR #6.4). Was tempfile.gettempdir() before,
    # which macOS could nuke on cleanup. Auto-creates the directory on first run.
    _BACKEND_DIR = Path(__file__).resolve().parents[1]  # automated-blog-system/
    _DATA_DIR = _BACKEND_DIR / "data"
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = str(_DATA_DIR / "automated_blog_system.db")

    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    USE_MOCK_DATA = True  # development default

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    WORDPRESS_URL = os.getenv('WORDPRESS_URL')
    WORDPRESS_USERNAME = os.getenv('WORDPRESS_USERNAME')
    WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD')

    # CrewAI
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    SERPER_API_KEY = os.getenv('SERPER_API_KEY')
    CREWAI_STORAGE_DIR = os.getenv('CREWAI_STORAGE_DIR', './data/crewai_memory')

    # GCS
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    # Ghost (PR #6.4 — surfaced for debug/health endpoints; ghost_service.py
    # still reads via os.getenv directly so it works without Config.)
    GHOST_API_URL = os.getenv('GHOST_API_URL')
    GHOST_ADMIN_KEY = os.getenv('GHOST_ADMIN_KEY')
    GHOST_CONTENT_API_KEY = os.getenv('GHOST_CONTENT_API_KEY')

    # PR #6.4 feature flag: when False (default), the dummy template-based
    # product discovery path raises instead of silently seeding off-niche
    # products. Set PIPELINE_ALLOW_TEMPLATE_FALLBACK=true in .env to opt back in.
    PIPELINE_ALLOW_TEMPLATE_FALLBACK = (
        os.getenv('PIPELINE_ALLOW_TEMPLATE_FALLBACK', 'false').lower() == 'true'
    )

    @classmethod
    def init_app(cls, app):
        print(f"Database will be created at: {cls.DB_PATH}")
        if cls.GHOST_API_URL and cls.GHOST_ADMIN_KEY:
            print(f"Ghost configured for: {cls.GHOST_API_URL}")
        else:
            print("⚠️  Ghost env vars missing — publisher will not work.")
