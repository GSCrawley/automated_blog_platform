"""pytest fixtures + .env loader for the automated-blog-system backend.

Loading .env here means tests work whether you run pytest from the repo root
or from automated-blog-system/, with no `set -a; source ../.env` ritual.
"""
from pathlib import Path

try:
    from dotenv import load_dotenv

    _PROJECT_ROOT = Path(__file__).resolve().parent.parent
    _ENV_PATH = _PROJECT_ROOT / ".env"
    if _ENV_PATH.is_file():
        load_dotenv(_ENV_PATH, override=False)
except ImportError:
    pass
