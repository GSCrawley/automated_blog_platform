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


def _secret(name: str, env_fallback: str | None = None) -> str | None:
    """Fetch a secret from GCP Secret Manager when USE_SECRET_MANAGER=true.

    Falls back to the env var ``env_fallback`` (or ``name`` itself) when
    Secret Manager is disabled or the secret is not found.  This lets the
    app work locally with .env values and switch to managed secrets in
    production by setting a single flag.
    """
    use_sm = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
    if not use_sm:
        return os.getenv(env_fallback or name)

    try:
        from google.cloud import secretmanager  # type: ignore

        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            return os.getenv(env_fallback or name)

        client = secretmanager.SecretManagerServiceClient()
        secret_id = (env_fallback or name).lower().replace("_", "-")
        resource = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": resource})
        return response.payload.data.decode("utf-8")
    except Exception:
        # Gracefully fall back to env var so local dev is never broken.
        return os.getenv(env_fallback or name)


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

    OPENAI_API_KEY = _secret("OPENAI_API_KEY")
    WORDPRESS_URL = os.getenv('WORDPRESS_URL')
    WORDPRESS_USERNAME = os.getenv('WORDPRESS_USERNAME')
    WORDPRESS_PASSWORD = os.getenv('WORDPRESS_PASSWORD')

    # CrewAI
    TAVILY_API_KEY = _secret("TAVILY_API_KEY")
    SERPER_API_KEY = _secret("SERPER_API_KEY")
    CREWAI_STORAGE_DIR = os.getenv('CREWAI_STORAGE_DIR', './data/crewai_memory')

    # Google Cloud Platform
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    GCP_REGION = os.getenv('GCP_REGION', 'us-central1')
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    # Ghost (PR #6.4 — surfaced for debug/health endpoints; ghost_service.py
    # still reads via os.getenv directly so it works without Config.)
    GHOST_API_URL = os.getenv('GHOST_API_URL')
    GHOST_ADMIN_KEY = _secret("GHOST_ADMIN_KEY")
    GHOST_CONTENT_API_KEY = _secret("GHOST_CONTENT_API_KEY")

    # Amazon Associates — the affiliate store/tracking ID appended to every
    # product CTA as ?tag=<id> (see Product.tracking_id and
    # CallToAction.build_target()). Defaults to the deskcred store.
    AMAZON_ASSOCIATES_TAG = os.getenv('AMAZON_ASSOCIATES_TAG', 'deskcred-20')
    AMAZON_MARKETPLACE_DOMAIN = os.getenv('AMAZON_MARKETPLACE_DOMAIN', 'www.amazon.com')

    # PR #6.4 feature flag: when False (default), the dummy template-based
    # product discovery path raises instead of silently seeding off-niche
    # products. Set PIPELINE_ALLOW_TEMPLATE_FALLBACK=true in .env to opt back in.
    PIPELINE_ALLOW_TEMPLATE_FALLBACK = (
        os.getenv('PIPELINE_ALLOW_TEMPLATE_FALLBACK', 'false').lower() == 'true'
    )

    @classmethod
    def init_app(cls, app):
        print(f"Database will be created at: {cls.DB_PATH}")
        if cls.GCP_PROJECT_ID:
            use_sm = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
            sm_status = "Secret Manager ON" if use_sm else "Secret Manager OFF (using .env)"
            print(f"☁️  GCP project: {cls.GCP_PROJECT_ID} — {sm_status}")
        if cls.GCS_BUCKET_NAME:
            print(f"☁️  GCS bucket: gs://{cls.GCS_BUCKET_NAME}")
        if cls.GHOST_API_URL and cls.GHOST_ADMIN_KEY:
            print(f"Ghost configured for: {cls.GHOST_API_URL}")
        else:
            print("⚠️  Ghost env vars missing — publisher will not work.")


# Hook point for all test-only overrides: mock Ghost, mock OpenAI, etc.
# Add future test-only settings here rather than scattering them across
# individual test fixtures.
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True
    OPENAI_API_KEY = None
    # Allow the template fallback path by default so pipeline tests run without
    # a real API key; individual tests can flip this on the live Config if needed.
    PIPELINE_ALLOW_TEMPLATE_FALLBACK = True
