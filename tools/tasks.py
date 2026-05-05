"""Celery tasks for the tools app."""
import os
import shutil
import logging
from datetime import timedelta
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='tools.tasks.cleanup_uploaded_files', ignore_result=True)
def cleanup_uploaded_files() -> dict:
    """
    Delete upload directories under MEDIA_ROOT/uploads/ that are older than 1 hour.
    Runs every 30 minutes via Celery Beat.
    """
    upload_root = Path(settings.MEDIA_ROOT) / 'uploads'
    if not upload_root.exists():
        return {'deleted': 0, 'errors': 0}

    cutoff = timezone.now() - timedelta(hours=1)
    deleted = errors = 0

    for entry in upload_root.iterdir():
        if not entry.is_dir():
            continue
        try:
            mtime = timezone.datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                shutil.rmtree(entry, ignore_errors=True)
                deleted += 1
                logger.debug('Deleted upload dir: %s', entry)
        except Exception as exc:
            errors += 1
            logger.warning('Failed to delete upload dir %s: %s', entry, exc)

    logger.info('cleanup_uploaded_files: deleted=%d errors=%d', deleted, errors)
    return {'deleted': deleted, 'errors': errors}
