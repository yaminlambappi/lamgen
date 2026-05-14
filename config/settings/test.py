"""
Test / pytest settings.

- Isolated from local and production
- Plain static storage (no collectstatic)
- In-memory SQLite database
- LocMem cache (no Redis dependency)
- AI calls always mocked
- Passwords hashed with MD5 for speed
"""

import os

os.environ.setdefault("DJANGO_ENV", "test")

from .base import *  # noqa: F401, F403, E402

DEBUG = False

# Fast in-memory database for tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# No Redis needed in tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# No collectstatic in tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Disable Celery task execution in tests (tasks run synchronously if called)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Fast password hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Always mock AI in tests
CLAUDE_MOCK_MODE = True

# Silence logging noise during test runs
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "CRITICAL"},
}
