"""
ASGI config for LamGen.

DJANGO_SETTINGS_MODULE must be set explicitly in the container/process
environment before this module is imported. There is no fallback.
"""

import os
import sys

from django.core.asgi import get_asgi_application

_dsm = os.environ.get("DJANGO_SETTINGS_MODULE", "")
if not _dsm:
    print(
        "[LamGen] FATAL: DJANGO_SETTINGS_MODULE is not set. "
        "Set it to 'config.settings.production' (or the appropriate environment) "
        "before starting the ASGI server.",
        file=sys.stderr,
    )
    sys.exit(1)

application = get_asgi_application()
