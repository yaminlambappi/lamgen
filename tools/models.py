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
    
    # SEO and topical authority fields
    seo_title = models.CharField(max_length=70, blank=True, help_text='Category page SEO title')
    seo_description = models.CharField(max_length=160, blank=True, help_text='Category page meta description')
    category_intro = models.TextField(blank=True, help_text='Category introduction for SEO landing page')
    featured_tools = models.JSONField(default=list, blank=True, help_text='List of featured tool slugs')
    best_use_cases = models.JSONField(default=list, blank=True, help_text='Category-level use cases')
    related_guides = models.JSONField(default=list, blank=True, help_text='Related guide URLs')
    related_subcategories = models.JSONField(default=list, blank=True, help_text='Related subcategory slugs')
    keyword_variations = models.JSONField(default=list, blank=True, help_text='Keyword variations for the category')
    category_faq = models.JSONField(default=list, blank=True, help_text='Category-level FAQ items')
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Analytics and performance tracking
    total_views = models.BigIntegerField(default=0)
    avg_session_duration = models.FloatField(default=0.0, help_text='Average session duration in seconds')
    bounce_rate = models.FloatField(default=0.0, help_text='Bounce rate percentage')
    last_analytics_update = models.DateTimeField(auto_now=True)

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

    @property
    def active_tools_count(self):
        return self.tools.filter(is_active=True).count()
    
    def get_featured_tools_objects(self):
        """Get actual Tool objects for featured tools."""
        if not self.featured_tools:
            return self.tools.filter(is_active=True, is_featured=True)[:4]
        
        featured_slugs = [slug for slug in self.featured_tools if slug]
        return self.tools.filter(slug__in=featured_slugs, is_active=True)[:4]
    
    def get_trending_tools(self, limit=6):
        """Get trending tools in this category."""
        return self.tools.filter(is_active=True).order_by('-view_count')[:limit]
    
    def get_newest_tools(self, limit=4):
        """Get newest tools in this category."""
        return self.tools.filter(is_active=True, is_new=True).order_by('-created_at')[:limit]
    
    def get_seo_metadata(self):
        """Generate SEO metadata for category page."""
        tool_count = self.active_tools_count
        
        if not self.seo_title:
            title = f'{self.name} — {tool_count} Free Online Tools | LamGen'
        else:
            title = self.seo_title
            
        if not self.seo_description:
            desc = self.description[:157] + '...' if self.description and len(self.description) > 160 else self.description or f'Free {self.name.lower()} online. {tool_count} tools — no download, no signup, instant results.'
        else:
            desc = self.seo_description
            
        return {
            'title': title[:70],
            'description': desc[:160],
            'keyword_count': len(self.keyword_variations or []),
            'tool_count': tool_count
        }


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
    usage_count = models.BigIntegerField(default=0)
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags')
    
    # SEO fields
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    seo_intro = models.TextField(blank=True, help_text='Unique 200-300 word intro for tool page')
    use_cases = models.JSONField(default=list, blank=True, help_text='List of use case descriptions')
    faq_items = models.JSONField(default=list, blank=True, help_text='List of {"q": question, "a": answer} dicts')
    
    # Enhanced SEO fields for topical authority
    keywords = models.JSONField(default=list, blank=True, help_text='List of target keywords')
    examples = models.JSONField(default=list, blank=True, help_text='List of tool usage examples')
    content_blocks = models.JSONField(default=list, blank=True, help_text='Dynamic content blocks for the page')
    schema_type = models.CharField(max_length=30, default='SoftwareApplication', 
                                  choices=[('SoftwareApplication', 'SoftwareApplication'), 
                                          ('WebPage', 'WebPage'), 
                                          ('Service', 'Service')])
    og_image = models.CharField(max_length=255, blank=True, help_text='Custom OG image path')
    canonical_url = models.CharField(max_length=255, blank=True, help_text='Custom canonical URL')
    searchable_tags = models.JSONField(default=list, blank=True, help_text='Enhanced searchable tags')
    word_count_target = models.IntegerField(default=1200, help_text='Target word count for SEO content')
    last_content_update = models.DateTimeField(auto_now=True, help_text='Track when SEO content was last updated')
    
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
            self.meta_title = f'{self.name} — Free Online Tool | LamGen'[:70]
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
    
    def get_all_keywords(self):
        """Combine tags, keywords, and searchable_tags for comprehensive SEO coverage."""
        all_keywords = set(self.get_tags_list())
        all_keywords.update(self.keywords or [])
        all_keywords.update(self.searchable_tags or [])
        return list(all_keywords)
    
    def get_related_tools_by_keywords(self, limit=8):
        """Find related tools based on keyword overlap."""
        from django.db.models import Q
        my_keywords = set(self.get_all_keywords())
        if not my_keywords:
            return []
        
        related = Tool.objects.filter(
            is_active=True,
            category=self.category
        ).exclude(id=self.id)
        
        # Score by keyword overlap
        scored_tools = []
        for tool in related:
            tool_keywords = set(tool.get_all_keywords())
            overlap = len(my_keywords.intersection(tool_keywords))
            if overlap > 0:
                tool.keyword_score = overlap
                scored_tools.append(tool)
        
        # Sort by overlap and return top results
        scored_tools.sort(key=lambda t: t.keyword_score, reverse=True)
        return scored_tools[:limit]
    
    def get_seo_score(self):
        """Calculate SEO completeness score."""
        score = 0
        max_score = 10
        
        # Basic SEO elements
        if self.meta_title: score += 1
        if self.meta_description: score += 1
        if self.seo_intro: score += 1
        if self.use_cases: score += 1
        if self.faq_items: score += 1
        if self.keywords: score += 1
        if self.examples: score += 1
        if self.content_blocks: score += 1
        if self.searchable_tags: score += 1
        if self.og_image: score += 1
        
        return min(score, max_score)


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
    used_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-used_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tool'],
                condition=models.Q(user__isnull=False),
                name='unique_user_tool_history',
            )
        ]

    def __str__(self):
        return f'{self.tool.name} at {self.used_at}'
