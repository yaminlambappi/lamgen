from celery import shared_task
from .models import AIProvider, AIProviderUsage

@shared_task
def update_provider_stats():
    for provider in AIProvider.objects.all():
        # In a real application, we would have a more sophisticated way of calculating these metrics.
        # For now, we will use random values.
        provider.health_score = 0.9
        provider.latency = 100
        provider.failure_rate = 0.1
        provider.save()
