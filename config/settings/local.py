"""
Local development settings.

- DEBUG on
- SQLite or local Postgres (DATABASE_URL from .env)
- Plain static file storage (no collectstatic required)
- Redis cache falls back to LocMem if Redis is unavailable
- Mock AI calls by default
"""

import os

os.environ.setdefault("DJANGO_ENV", "local")

from .base import *  # noqa: F401, F403, E402

DEBUG = True

# Plain storage — no collectstatic needed locally
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Relax ALLOWED_HOSTS for local dev
ALLOWED_HOSTS = ["*"]

# Fall back to LocMem cache when Redis is not running locally
try:
    import redis as _redis
    _r = _redis.from_url(REDIS_URL, socket_connect_timeout=1)  # noqa: F405
    _r.ping()
except Exception:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# Mock AI by default in local dev (override in .env with CLAUDE_MOCK_MODE=False)
CLAUDE_MOCK_MODE = True
