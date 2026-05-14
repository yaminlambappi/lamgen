"""
Staging settings.

Mirrors production but allows slightly relaxed constraints for QA.
All production safety guards still apply.
"""

import os

os.environ.setdefault("DJANGO_ENV", "staging")

from config.env import assert_production_safety  # noqa: E402

assert_production_safety()

from .base import *  # noqa: F401, F403, E402

DEBUG = False

# Manifest-based static storage (same as production)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
