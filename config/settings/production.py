"""
Production settings.

All safety guards are enforced at import time. The process will exit
immediately if any required secret or configuration is missing or invalid.
"""

import os

os.environ.setdefault("DJANGO_ENV", "production")

from config.env import assert_production_safety  # noqa: E402

assert_production_safety()

from .base import *  # noqa: F401, F403, E402

DEBUG = False

# Manifest-based static storage — collectstatic must run before deployment
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Strict security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
