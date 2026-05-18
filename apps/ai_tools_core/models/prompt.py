from django.db import models

class PromptTemplate(models.Model):
    tool_slug = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=50, default="default")
    prompt_type = models.CharField(max_length=50, default="text")
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.tool_slug
