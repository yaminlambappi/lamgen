"""
WSGI config for LamGen.

DJANGO_SETTINGS_MODULE must be set explicitly in the container/process
environment before this module is imported. There is no fallback — an
unset or wrong value will cause an immediate startup failure.
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

_dsm = os.environ.get("DJANGO_SETTINGS_MODULE", "")
if not _dsm:
    print(
        "[LamGen] FATAL: DJANGO_SETTINGS_MODULE is not set. "
        "Set it to 'config.settings.production' (or the appropriate environment) "
        "before starting Gunicorn.",
        file=sys.stderr,
    )
    sys.exit(1)

application = get_wsgi_application()
