from django.db import models
from django.conf import settings

class ToolUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tool_slug = models.CharField(max_length=100)
    provider = models.CharField(max_length=50)
    latency = models.PositiveIntegerField()
    cost = models.DecimalField(max_digits=10, decimal_places=4)
    is_successful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.tool_slug} - {self.created_at}"
