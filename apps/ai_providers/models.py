from django.db import models

class AIProvider(models.Model):
    name = models.CharField(max_length=50, unique=True)
    health_score = models.FloatField(default=1.0)
    latency = models.PositiveIntegerField(default=0)
    failure_rate = models.FloatField(default=0.0)

    def __str__(self):
        return self.name

class AIProviderUsage(models.Model):
    provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, default=1)
    # provider_name is deprecated and will be removed in a future version.
    # provider_name = models.CharField(max_length=50)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider.name} - {self.created_at}"
