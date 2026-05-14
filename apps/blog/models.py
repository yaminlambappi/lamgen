from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import markdown as md


class ContentArticle(models.Model):
    CONTENT_TYPES = [
        ("tutorial", "Tutorial"),
        ("comparison", "Comparison"),
        ("use-case", "Use-Case Guide"),
        ("troubleshooting", "Troubleshooting Guide"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    body = models.TextField(help_text="Markdown content")
    related_tools = models.ManyToManyField("tools.Tool", blank=True, related_name="articles")
    author = models.CharField(max_length=100, default="LamGen Team")
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.meta_title:
            self.meta_title = self.title[:70]
        if not self.meta_description:
            self.meta_description = self.title[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:article", kwargs={
            "content_type": self.content_type,
            "slug": self.slug,
        })

    def body_html(self):
        return md.markdown(self.body, extensions=["extra", "codehilite", "toc"])
