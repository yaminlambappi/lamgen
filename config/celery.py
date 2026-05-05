import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('lamgen')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-old-uploads-hourly': {
        'task': 'thesis.tasks.cleanup_old_uploads',
        'schedule': crontab(minute=0),  # every hour
    },
    'cleanup-old-generation-uploads-hourly': {
        'task': 'generation.tasks.cleanup_old_generation_uploads',
        'schedule': crontab(minute=0),  # every hour
    },
    'cleanup-tools-uploads-every-30min': {
        'task': 'tools.tasks.cleanup_uploaded_files',
        'schedule': crontab(minute='*/30'),  # every 30 minutes
    },
}
