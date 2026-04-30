from django.conf import settings
from django.db import models


class StatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'


class ThesisRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='thesis_requests',
    )
    title = models.CharField(max_length=500)
    input_file = models.FileField(upload_to='uploads/', null=True, blank=True)
    output_file = models.FileField(upload_to='outputs/', null=True, blank=True)
    generated_thesis = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.status})'


class ThesisChunk(models.Model):
    thesis_request = models.ForeignKey(
        ThesisRequest,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    order = models.PositiveIntegerField()
    content = models.TextField()
    token_count = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = [('thesis_request', 'order')]

    def __str__(self):
        return f'Chunk {self.order} of {self.thesis_request_id}'
