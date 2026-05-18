"""
Celery application for LamGen.

Celery must use the same DJANGO_SETTINGS_MODULE as the web process.
The variable must be set in the container/process environment — there
is no fallback to a bare 'config.settings'.
"""

import os
import sys

from celery import Celery
from celery.schedules import crontab

_dsm = os.environ.get("DJANGO_SETTINGS_MODULE", "")
if not _dsm:
    print(
        "[LamGen] FATAL: DJANGO_SETTINGS_MODULE is not set for Celery. "
        "Set it to the same value used by the web process "
        "(e.g. 'config.settings.production').",
        file=sys.stderr,
    )
    sys.exit(1)

app = Celery("lamgen")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "cleanup-old-uploads-hourly": {
        "task": "thesis.tasks.cleanup_old_uploads",
        "schedule": crontab(minute=0),
    },
    "cleanup-old-generation-uploads-hourly": {
        "task": "generation.tasks.cleanup_old_generation_uploads",
        "schedule": crontab(minute=0),
    },
    "cleanup-tools-uploads-every-30min": {
        "task": "tools.tasks.cleanup_uploaded_files",
        "schedule": crontab(minute="*/30"),
    },
    "update-provider-stats-hourly": {
        "task": "apps.ai_providers.tasks.update_provider_stats",
        "schedule": crontab(minute=0, hour="*/1"),
    },
}
