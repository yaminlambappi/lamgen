from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class ToolCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=60, default='bi-tools')
    color_from = models.CharField(max_length=30, default='#6C63FF')
    color_to = models.CharField(max_length=30, default='#00F5D4')
    description = models.TextField(blank=True)
    short_desc = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Tool Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tools:category', kwargs={'category_slug': self.slug})


class Tool(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ToolCategory, on_delete=models.CASCADE, related_name='tools')
    description = models.TextField()
    short_desc = models.CharField(max_length=255)
    icon = models.CharField(max_length=60, default='bi-wrench')
    template_name = models.CharField(max_length=200)  # e.g. "tools/developer/json-formatter.html"
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_pro = models.BooleanField(default=False)
    view_count = models.BigIntegerField(default=0)
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags')
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__order', 'order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = f'{self.name} — Free Online Tool | LamGen'
        if not self.meta_description:
            self.meta_description = self.short_desc[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tools:tool', kwargs={
            'category_slug': self.category.slug,
            'tool_slug': self.slug,
        })

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]


class ToolBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tool')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} → {self.tool}'


class ToolUsageHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='tool_history')
    session_key = models.CharField(max_length=40, blank=True)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='usage_history')
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']

    def __str__(self):
        return f'{self.tool.name} at {self.used_at}'
