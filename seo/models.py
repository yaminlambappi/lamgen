from django.db import models
from django.utils.text import slugify


class SEOCategory(models.Model):
    """Top-level programmatic SEO content category (e.g. 'captions', 'quotes')"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    title_template = models.CharField(
        max_length=200,
        help_text='Use {topic} placeholder. E.g. "{topic} Instagram Captions — 100+ Ideas"',
        default='{topic} Ideas'
    )
    meta_desc_template = models.CharField(
        max_length=300,
        default='Browse {count}+ {topic} ideas. Free, curated, and ready to use.',
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'SEO Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('seo:category', kwargs={'category_slug': self.slug})


class SEOPage(models.Model):
    """Individual programmatic SEO page (e.g. 'birthday-captions', 'python-interview-questions')"""
    category = models.ForeignKey(SEOCategory, on_delete=models.CASCADE, related_name='pages')
    topic = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    content_intro = models.TextField(blank=True)
    items = models.JSONField(default=list, help_text='Array of content items')
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    view_count = models.BigIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'topic']

    def __str__(self):
        return f'{self.category.name}: {self.topic}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.category.slug}-{self.topic}')
        if not self.meta_title:
            self.meta_title = self.category.title_template.replace('{topic}', self.topic)[:70]
        if not self.meta_description:
            self.meta_description = self.category.meta_desc_template.replace(
                '{topic}', self.topic
            ).replace('{count}', str(len(self.items)))[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('seo:page', kwargs={
            'category_slug': self.category.slug,
            'page_slug': self.slug,
        })
