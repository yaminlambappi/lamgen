# Design Document: LamGen Tools Ecosystem

## Overview

The LamGen Tools Ecosystem transforms the existing Django assignment generator into a production-grade multi-tool platform hosting hundreds of browser-side and backend utilities, a programmatic SEO content engine, and a unified discovery/monetisation layer. The platform targets zero-API-cost operation for the vast majority of tools, with the existing Claude-powered generators preserved as a premium "Academic & Writing" category.

The architecture extends the current Django project in-place: the five existing apps (`accounts`, `generation`, `thesis`, `tools`, `seo`) are retained and expanded. No existing URLs, models, or views are removed. New capability is added through new sub-modules, management commands, template partials, and configuration entries.

**Tech stack (existing, unchanged):**
- Django 4.2, PostgreSQL, Redis, Celery Beat
- WhiteNoise + CompressedManifestStaticFilesStorage
- Hypothesis (property-based testing), pytest-django
- PyMuPDF, WeasyPrint, python-magic, Pillow

**New dependencies required:**
- None for browser tools (all JS-only)
- `django-ratelimit==4.1.0` — cache-based rate limiting for search endpoint
- No new Python packages for SEO engine (uses stdlib `hashlib`, `random`, `string`)

---

## Architecture

### Django App Structure

```
config/
  settings.py          # TOOL_CATEGORIES dict, MAX_UPLOAD_SIZE, rate-limit config
  urls.py              # root URL conf — existing + new routes
  celery.py            # Celery app + Beat schedule

accounts/              # CustomUser — unchanged
generation/            # Assignment generator — unchanged
thesis/                # Thesis generator — unchanged

tools/                 # Core platform app
  models.py            # ToolCategory, Tool, ToolBookmark, ToolUsageHistory
  views.py             # index, category_view, tool_view, search_view,
                       # toggle_bookmark, trending_view, record_usage_view
  urls.py              # /tools/* routes
  context_processors.py  # nav_categories, bookmarked_slugs injected globally
  admin.py
  apps.py
  templatetags/
    tools_tags.py      # tool_card, ad_slot, breadcrumb, schema_markup tags
  management/
    commands/
      seed_tools.py    # idempotent fixture loader
  utils/
    __init__.py
    file_validation.py # MIME inspection via python-magic
    slug_utils.py      # slug generation helpers
    metadata.py        # meta title/description truncation helpers
    rate_limit.py      # cache-based rate limiter helper
  developer/           # Browser tool templates live in templates/tools/developer/
  student/
  writing/
  utility/
  social/
  seo_tools/
  image/
  pdf/
  resume/

seo/                   # Programmatic SEO engine
  models.py            # SEOCategory, SEOPage
  views.py             # category_view, page_view
  urls.py              # /content/* routes
  sitemaps.py          # ToolSitemap, CategorySitemap, SEOPageSitemap
  apps.py
  management/
    commands/
      generate_seo_pages.py  # deterministic content seeder
  engine/
    __init__.py
    content_generator.py     # rule-based content generation
    word_lists.py            # curated word lists per content type
    templates.py             # string template definitions

templates/
  base.html                  # global shell, dark/light mode, Command Palette
  home.html                  # homepage: trending, new, recent, categories
  partials/
    ad_slot.html             # <div data-ad-slot="..."></div>
    tool_card.html
    category_card.html
    breadcrumb.html
    tool_action_bar.html     # sticky mobile action bar
    search_result_item.html
    paywall_overlay.html     # is_pro gate
    auth_prompt.html         # non-intrusive login nudge
  tools/
    index.html               # /tools/ — all categories grid
    category.html            # /{category_slug}/
    generic_tool.html        # fallback for tools without a dedicated template
    trending.html            # /tools/trending/
    developer/               # one .html per browser tool
    student/
    writing/
    utility/
    social/
    seo_tools/
    image/
    pdf/
    resume/
  seo/
    category.html
    page.html
  dashboard/
    index.html
```

### Request Flow

```
Browser → Nginx (TLS termination, static files)
       → Gunicorn (Django WSGI)
         → WhiteNoise middleware (static assets, immutable cache headers)
         → Django middleware stack
           → tools.context_processors.tools_context (nav injection)
           → View layer
             → Redis cache check (category pages, tool registry)
             → PostgreSQL query (cache miss)
             → Template render
         → Response (Cache-Control headers set per view)

Async tasks:
  Celery Beat → cleanup_uploaded_files (every 30 min)
              → flush_view_counters (every 5 min, optional)
```

### URL Routing Structure

```
/                                    → tools.views.index (homepage)
/tools/                              → tools.views.tools_index_view
/tools/search/                       → tools.views.search_view
/tools/trending/                     → tools.views.trending_view
/tools/bookmark/toggle/              → tools.views.toggle_bookmark (POST)
/tools/usage/record/                 → tools.views.record_usage_view (POST)
/tools/<category_slug>/              → tools.views.category_view
/tools/<category_slug>/<tool_slug>/  → tools.views.tool_view

/content/<category_slug>/            → seo.views.category_view
/content/<category_slug>/<page_slug>/ → seo.views.page_view

/generation/…                        → generation.urls (unchanged)
/thesis/…                            → thesis.urls (unchanged)
/accounts/…                          → accounts.urls (unchanged)

/robots.txt                          → config.urls.robots_txt
/sitemap.xml                         → django.contrib.sitemaps (index, cached 24h)
/sitemap-<section>.xml               → django.contrib.sitemaps (per-section)
/admin/                              → django.contrib.admin
```

Note: `Tool.get_absolute_url()` returns `/tools/{category_slug}/{tool_slug}/`. The `tools:tool` URL name resolves to this pattern. The `/tools/` prefix is used to avoid slug collisions with top-level routes.

---

## Components and Interfaces

### Tool Registry System

The Tool Registry is the central catalogue. It is database-backed and populated via the `seed_tools` management command. The registry is read-only at runtime (no user-generated tools).

**`seed_tools` management command** (`tools/management/commands/seed_tools.py`):

```python
# Idempotent: uses update_or_create on slug
# Source: TOOL_CATEGORIES dict in settings.py + inline tool definitions
# Execution: python manage.py seed_tools
# Safe to re-run: will not duplicate records

class Command(BaseCommand):
    def handle(self, *args, **options):
        for cat_data in settings.TOOL_CATEGORIES:
            category, _ = ToolCategory.objects.update_or_create(
                slug=cat_data['slug'],
                defaults={k: v for k, v in cat_data.items() if k != 'tools'}
            )
            for tool_data in cat_data.get('tools', []):
                Tool.objects.update_or_create(
                    slug=tool_data['slug'],
                    defaults={**tool_data, 'category': category}
                )
```

**`TOOL_CATEGORIES` in `config/settings.py`**:

```python
TOOL_CATEGORIES = [
    {
        'slug': 'developer-tools',
        'name': 'Developer Tools',
        'icon': 'bi-code-slash',
        'color_from': '#6C63FF',
        'color_to': '#00F5D4',
        'order': 1,
        'tools': [
            {
                'slug': 'json-formatter',
                'name': 'JSON Formatter',
                'short_desc': 'Format, validate and beautify JSON online.',
                'icon': 'bi-braces',
                'template_name': 'tools/developer/json-formatter.html',
                'tags': 'json,format,beautify,validate,developer',
                'order': 1,
            },
            # ... all other tools
        ]
    },
    # ... all other categories
]
```

### Browser-Side Tool Architecture

Each Browser_Tool is a self-contained HTML template. The Django view (`tool_view`) renders the template with the `tool` context object; all processing logic is embedded JavaScript.

**Template structure for a Browser_Tool:**

```html
{% extends "base.html" %}
{% block tool_js %}
<script>
// All processing logic here — no fetch() to server
// Input: read from DOM
// Output: write to DOM
// Download: use Blob + URL.createObjectURL()

document.getElementById('btn-format').addEventListener('click', () => {
    const input = document.getElementById('input').value;
    try {
        const result = JSON.stringify(JSON.parse(input), null, 2);
        document.getElementById('output').textContent = result;
        showSuccess();
    } catch (e) {
        showError(e.message);
    }
});
</script>
{% endblock %}
```

**Lazy loading**: The `{% block tool_js %}` block is placed at the bottom of `base.html` before `</body>`. Tool JS is never loaded on the homepage or category pages — only when the specific tool template is rendered.

**Web Workers** (for CPU-intensive tools like hash generation, image processing):

```html
{% block tool_js %}
<script>
const worker = new Worker("{% static 'js/workers/hash-worker.js' %}");
worker.onmessage = (e) => { document.getElementById('output').value = e.data.result; };
document.getElementById('btn-hash').addEventListener('click', () => {
    worker.postMessage({ input: document.getElementById('input').value, algo: 'SHA-256' });
});
</script>
{% endblock %}
```

Worker files live in `static/js/workers/`. They are loaded lazily (only when the tool page is visited).

**Client-side file download pattern:**

```javascript
function downloadResult(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
}
```

**Image tools** use the Canvas API:

```javascript
// Image compressor example
const canvas = document.createElement('canvas');
canvas.width = img.naturalWidth;
canvas.height = img.naturalHeight;
canvas.getContext('2d').drawImage(img, 0, 0);
canvas.toBlob((blob) => downloadResult(blob, 'compressed.jpg', 'image/jpeg'), 'image/jpeg', 0.7);
```

For WEBP conversion and advanced compression, `squoosh-lib` (WASM-based) is loaded via CDN only on image tool pages.

### Backend Tool Processing Pipeline

Backend_Tools follow a strict request/response pipeline:

```
1. File upload (multipart/form-data POST)
2. Size check: if file.size > MAX_UPLOAD_SIZE → HTTP 413
3. MIME validation: python-magic detects actual MIME → reject if mismatch
4. Save to media/uploads/{uuid}/{filename}
5. Process (PyMuPDF / Pillow / zipfile)
6. Return file as HttpResponse with Content-Disposition: attachment
7. Schedule cleanup: Celery task to delete upload + output after 1 hour
```

**File validation utility** (`tools/utils/file_validation.py`):

```python
import magic

ALLOWED_MIMES = {
    'pdf': ['application/pdf'],
    'image': ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
    'zip': ['application/zip', 'application/x-zip-compressed'],
    'csv': ['text/csv', 'text/plain'],
}

def validate_mime(file_obj, expected_type: str) -> tuple[bool, str]:
    """Returns (is_valid, detected_mime)."""
    header = file_obj.read(2048)
    file_obj.seek(0)
    detected = magic.from_buffer(header, mime=True)
    allowed = ALLOWED_MIMES.get(expected_type, [])
    return detected in allowed, detected
```

**Celery cleanup task** (`tools/tasks.py`):

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import os, shutil

@shared_task
def cleanup_uploaded_files():
    """Delete upload directories older than 1 hour."""
    cutoff = timezone.now() - timedelta(hours=1)
    upload_root = settings.MEDIA_ROOT / 'uploads'
    for entry in upload_root.iterdir():
        if entry.is_dir():
            mtime = timezone.datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                shutil.rmtree(entry, ignore_errors=True)
```

Celery Beat schedule in `config/celery.py`:

```python
app.conf.beat_schedule = {
    'cleanup-uploads-every-30min': {
        'task': 'tools.tasks.cleanup_uploaded_files',
        'schedule': 1800,  # 30 minutes
    },
}
```

### Search and Discovery

**Search endpoint** (`/tools/search/?q=...`):

- Minimum query length: 2 characters (returns `{"results": []}` immediately for shorter)
- Intent expansion: `convert` → adds `converter,transform,to`; `format` → `formatter,beautify,clean`; `validate` → `validator,checker,verify`; `make` → `generator,create,builder`
- Relevance scoring: exact name match = 100pts, name contains = 50pts, desc/tags = 10pts
- Result cap: 15 tools
- Rate limit: 60 req/min per IP (cache-based, returns HTTP 429)

**Command Palette** (JavaScript, `static/js/command-palette.js`):

```javascript
// Triggered by: document.addEventListener('keydown', e => {
//   if (e.key === '/' || (e.ctrlKey && e.key === 'k')) openPalette();
// });
// Debounce: 250ms before firing fetch
// Renders results into overlay within 300ms of debounce firing
// Keyboard navigation: ArrowUp/ArrowDown to move, Enter to navigate
```

**Homepage discovery sections** (rendered in `tools/views.index`):

| Section | Query | Count |
|---|---|---|
| Trending Tools | `order_by('-view_count')` | 8 |
| Recently Used | session `recent_tools` slugs | 5 |
| New Tools | `filter(is_new=True)` | 6 |

### Metadata Engine

The Metadata Engine is implemented as a combination of:
1. Model-level auto-generation (`Tool.save()`, `SEOPage.save()`)
2. View-level context variables (`page_title`, `meta_description`, `canonical_url`, `og_image`, `schema_json`)
3. Base template rendering (`base.html` `<head>` block)

**Base template `<head>` block:**

```html
<title>{{ page_title|default:"LamGen Tools — Free Online Utilities" }}</title>
<meta name="description" content="{{ meta_description|default:'' }}">
<link rel="canonical" href="{{ canonical_url|default:request.build_absolute_uri }}">

<!-- OpenGraph -->
<meta property="og:title" content="{{ page_title }}">
<meta property="og:description" content="{{ meta_description }}">
<meta property="og:url" content="{{ canonical_url|default:request.build_absolute_uri }}">
<meta property="og:type" content="{{ og_type|default:'website' }}">
<meta property="og:image" content="{{ og_image|default:STATIC_URL|add:'img/og-default.png' }}">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ page_title }}">
<meta name="twitter:description" content="{{ meta_description }}">

<!-- JSON-LD -->
{% if schema_json %}
<script type="application/ld+json">{{ schema_json|safe }}</script>
{% endif %}
```

**JSON-LD generation** (`tools/templatetags/tools_tags.py`):

```python
import json
from django import template
register = template.Library()

@register.simple_tag
def software_application_schema(tool, request):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": tool.name,
        "description": tool.short_desc,
        "url": request.build_absolute_uri(tool.get_absolute_url()),
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Web",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    })

@register.simple_tag
def faq_schema(page):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": item['q'], "acceptedAnswer": {"@type": "Answer", "text": item['a']}}
            for item in page.items if 'q' in item and 'a' in item
        ]
    })

@register.simple_tag
def item_list_schema(page, request):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": page.meta_title,
        "url": request.build_absolute_uri(page.get_absolute_url()),
        "numberOfItems": len(page.items),
        "itemListElement": [
            {"@type": "ListItem", "position": i+1, "name": item if isinstance(item, str) else item.get('text', '')}
            for i, item in enumerate(page.items[:20])
        ]
    })
```

### Analytics and Ad System

**Redis-backed view counter** (already implemented in `tools/views.py`, documented here for completeness):

```python
cache_key = f'tool_views_{tool.pk}'
views = cache.get(cache_key, 0) + 1
cache.set(cache_key, views, 300)  # 5-minute TTL
if views % 10 == 0:
    Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + views)
    cache.set(cache_key, 0, 300)
```

**Usage count endpoint** (`/tools/usage/record/` POST):

```python
@require_POST
@csrf_exempt  # AJAX from same origin — CSRF token sent via header
def record_usage_view(request):
    tool_slug = request.POST.get('tool_slug') or json.loads(request.body).get('tool_slug')
    Tool.objects.filter(slug=tool_slug).update(usage_count=F('usage_count') + 1)
    if request.user.is_authenticated:
        ToolUsageHistory.objects.update_or_create(
            user=request.user, tool_id=tool_slug_to_id(tool_slug), defaults={}
        )
    return JsonResponse({'ok': True})
```

**Ad Slot partial** (`templates/partials/ad_slot.html`):

```html
{# Usage: {% include "partials/ad_slot.html" with slot_id="tool-header" %} #}
<div
  class="ad-slot"
  data-ad-slot="{{ slot_id }}"
  aria-hidden="true"
  style="min-height: 90px;"
></div>
```

Ad slots are placed at three positions in `templates/tools/generic_tool.html`:
1. `slot_id="tool-header"` — below the tool title/description
2. `slot_id="tool-mid"` — between tool output and related tools
3. `slot_id="sidebar"` — in the right sidebar panel

### Bookmark and History System

**Session-based (Guest_User):**

```python
# In tool_view — session bookmark check
session_bookmarks = request.session.get('session_bookmarks', [])
is_bookmarked = tool.slug in session_bookmarks

# In toggle_bookmark — guest path
if not request.user.is_authenticated:
    session_bookmarks = request.session.get('session_bookmarks', [])
    if tool_slug in session_bookmarks:
        session_bookmarks.remove(tool_slug)
        bookmarked = False
    elif len(session_bookmarks) < 10:
        session_bookmarks.append(tool_slug)
        bookmarked = True
    else:
        return JsonResponse({'error': 'Session bookmark limit reached (10)'}, status=400)
    request.session['session_bookmarks'] = session_bookmarks
    return JsonResponse({'bookmarked': bookmarked})
```

**Bookmark merge on login** — implemented via a Django signal or in the login view:

```python
# accounts/views.py — after successful login
def merge_session_bookmarks(request, user):
    session_slugs = request.session.pop('session_bookmarks', [])
    if session_slugs:
        tools = Tool.objects.filter(slug__in=session_slugs, is_active=True)
        for tool in tools:
            ToolBookmark.objects.get_or_create(user=user, tool=tool)
        # Invalidate bookmark cache
        cache.delete(f'bookmarks_{user.pk}')
```

**DB-based (Registered_User):**

The `ToolBookmark` model has a `unique_together = ('user', 'tool')` constraint. `toggle_bookmark` uses `get_or_create` + conditional delete. The `ToolUsageHistory` model uses `update_or_create(user=user, tool=tool, defaults={})` so `auto_now=True` on `used_at` updates the timestamp on repeat use.

### Caching Strategy

| Resource | Cache Backend | TTL | Decorator |
|---|---|---|---|
| Tool registry (nav) | Redis | 30 min | `cache.set('tool_categories_nav_v2', ...)` |
| Category page | Redis (HTTP cache) | 10 min | `@cache_control(public=True, max_age=600)` |
| Homepage | Redis (HTTP cache) | 1 min | `@cache_control(public=True, max_age=60)` |
| Tool page | No full-page cache | — | View counter uses Redis |
| SEO page | Redis (full-page) | 24 h | `@cache_page(86400)` |
| Sitemap XML | Redis (full-page) | 24 h | `cache_page(86400)` in urls.py |
| User bookmarks | Redis | 5 min | `cache.set(f'bookmarks_{user.pk}', ...)` |
| Static assets | WhiteNoise | 1 year | `WHITENOISE_MAX_AGE = 31536000` |

### Security

**Rate limiting** (`tools/utils/rate_limit.py`):

```python
from django.core.cache import cache
from django.http import JsonResponse

def rate_limit(key_prefix, limit=60, window=60):
    """Decorator factory for cache-based rate limiting."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
            cache_key = f'rl:{key_prefix}:{ip}'
            count = cache.get(cache_key, 0)
            if count >= limit:
                return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
            cache.set(cache_key, count + 1, window)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Applied to search_view:
# @rate_limit('search', limit=60, window=60)
```

**CSRF**: All POST endpoints (`toggle_bookmark`, `record_usage`) require the CSRF token. AJAX calls send it via the `X-CSRFToken` header (set from the `csrftoken` cookie in JavaScript).

**Pro tool paywall** (`templates/partials/paywall_overlay.html`):

```html
{% if tool.is_pro and not request.user.is_authenticated %}
<div class="paywall-overlay" role="dialog" aria-label="Pro feature">
  <p>This tool requires a free account.</p>
  <a href="{% url 'accounts:register' %}">Sign up free</a>
  <button class="btn-ghost" data-dismiss="paywall">Continue as Guest</button>
</div>
{% endif %}
```

---

## Data Models

### `tools` app

```python
class ToolCategory(models.Model):
    name          = models.CharField(max_length=100)
    slug          = models.SlugField(unique=True)
    icon          = models.CharField(max_length=60, default='bi-tools')
    color_from    = models.CharField(max_length=30, default='#6C63FF')
    color_to      = models.CharField(max_length=30, default='#00F5D4')
    description   = models.TextField(blank=True)
    short_desc    = models.CharField(max_length=200, blank=True)
    order         = models.IntegerField(default=0)
    is_active     = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def get_absolute_url(self):
        return reverse('tools:category', kwargs={'category_slug': self.slug})


class Tool(models.Model):
    name             = models.CharField(max_length=150)
    slug             = models.SlugField(unique=True)
    category         = models.ForeignKey(ToolCategory, on_delete=models.CASCADE, related_name='tools')
    description      = models.TextField()
    short_desc       = models.CharField(max_length=255)
    icon             = models.CharField(max_length=60, default='bi-wrench')
    template_name    = models.CharField(max_length=200)
    is_active        = models.BooleanField(default=True)
    is_featured      = models.BooleanField(default=False)
    is_new           = models.BooleanField(default=False)
    is_pro           = models.BooleanField(default=False)
    view_count       = models.BigIntegerField(default=0)
    usage_count      = models.BigIntegerField(default=0)   # NEW: separate from view_count
    tags             = models.CharField(max_length=500, blank=True)
    meta_title       = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    order            = models.IntegerField(default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__order', 'order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.meta_title:
            self.meta_title = f'{self.name} — Free Online Tool | LamGen'[:70]
        if not self.meta_description:
            self.meta_description = self.short_desc[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tools:tool', kwargs={
            'category_slug': self.category.slug,
            'tool_slug': self.slug,
        })

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]


class ToolBookmark(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    tool       = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tool')
        ordering = ['-created_at']


class ToolUsageHistory(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='tool_history')
    session_key = models.CharField(max_length=40, blank=True)
    tool        = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='usage_history')
    used_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-used_at']
        # Unique per registered user per tool (session users have no constraint)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tool'],
                condition=models.Q(user__isnull=False),
                name='unique_user_tool_history'
            )
        ]
```

**Migration note**: `usage_count` is a new field on `Tool`. A migration adding `usage_count = models.BigIntegerField(default=0)` is required. The `UniqueConstraint` on `ToolUsageHistory` replaces the previous lack of constraint — a data migration may be needed to deduplicate existing rows.

### `seo` app

```python
class SEOCategory(models.Model):
    """Content type grouping (e.g. 'captions', 'quotes', 'interview-questions')"""
    name               = models.CharField(max_length=100)
    slug               = models.SlugField(unique=True)
    description        = models.TextField(blank=True)
    title_template     = models.CharField(max_length=200, default='{topic} Ideas')
    meta_desc_template = models.CharField(max_length=300,
        default='Browse {count}+ {topic} ideas. Free, curated, and ready to use.')
    schema_type        = models.CharField(max_length=30, default='ItemList',
        choices=[('ItemList', 'ItemList'), ('FAQPage', 'FAQPage'), ('Article', 'Article')])
    is_active          = models.BooleanField(default=True)
    order              = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def get_absolute_url(self):
        return reverse('seo:category', kwargs={'category_slug': self.slug})


class SEOPage(models.Model):
    """Individual programmatic SEO page."""
    category         = models.ForeignKey(SEOCategory, on_delete=models.CASCADE, related_name='pages')
    topic            = models.CharField(max_length=200)
    slug             = models.SlugField(unique=True, max_length=250)
    content_intro    = models.TextField(blank=True)
    items            = models.JSONField(default=list)
    # items schema: list of str, or list of {"text": str, "category": str}
    # for FAQ pages: list of {"q": str, "a": str}
    meta_title       = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    related_tools    = models.ManyToManyField('tools.Tool', blank=True, related_name='seo_pages')
    view_count       = models.BigIntegerField(default=0)
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'topic']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.category.slug}-{self.topic}')
        if not self.meta_title:
            self.meta_title = self.category.title_template.replace('{topic}', self.topic)[:70]
        if not self.meta_description:
            self.meta_description = self.category.meta_desc_template \
                .replace('{topic}', self.topic) \
                .replace('{count}', str(len(self.items)))[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('seo:page', kwargs={
            'category_slug': self.category.slug,
            'page_slug': self.slug,
        })
```

**Key design decisions:**
- `SEOPage.items` is a `JSONField` storing a list. This avoids a separate `SEOItem` table and keeps queries simple. For pages with 20–100 items, JSON storage is appropriate.
- `SEOPage.related_tools` is a `ManyToManyField` populated by `generate_seo_pages` command. This enables the "link to 3 related tools" requirement without a separate linking table.
- `SEOCategory.schema_type` drives which JSON-LD template is injected by the Metadata Engine.

---

## Programmatic SEO Engine

### Content Generation Architecture

The SEO Engine generates content entirely in Python using deterministic seeding — no LLM calls, no external APIs.

**Core principle**: `random.seed(int(hashlib.md5(slug.encode()).hexdigest(), 16))` before any `random.choice()` call ensures identical output for the same slug across all invocations.

**`seo/engine/content_generator.py`**:

```python
import hashlib
import random
from .word_lists import WORD_LISTS
from .templates import CONTENT_TEMPLATES

def generate_items(category_slug: str, topic: str, slug: str, count: int = 30) -> list:
    """
    Generate deterministic content items for a given topic slug.
    Always produces identical output for the same slug.
    """
    seed = int(hashlib.md5(slug.encode('utf-8')).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)  # isolated RNG — does not affect global state

    templates = CONTENT_TEMPLATES.get(category_slug, CONTENT_TEMPLATES['default'])
    words = WORD_LISTS.get(category_slug, {})

    items = []
    for i in range(count):
        template = rng.choice(templates)
        # Fill template placeholders from word lists
        item = template.format(
            topic=topic,
            adj=rng.choice(words.get('adjectives', ['amazing'])),
            noun=rng.choice(words.get('nouns', ['moment'])),
            verb=rng.choice(words.get('verbs', ['explore'])),
            emotion=rng.choice(words.get('emotions', ['joy'])),
            number=rng.randint(1, 100),
        )
        items.append(item)

    # Deduplicate while preserving order
    seen = set()
    unique_items = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)

    # If deduplication reduced count below minimum, generate more
    while len(unique_items) < 20:
        extra_seed = seed + len(unique_items)
        rng2 = random.Random(extra_seed)
        template = rng2.choice(templates)
        item = template.format(
            topic=topic,
            adj=rng2.choice(words.get('adjectives', ['incredible'])),
            noun=rng2.choice(words.get('nouns', ['journey'])),
            verb=rng2.choice(words.get('verbs', ['discover'])),
            emotion=rng2.choice(words.get('emotions', ['wonder'])),
            number=rng2.randint(101, 200),
        )
        if item not in seen:
            seen.add(item)
            unique_items.append(item)

    return unique_items[:count]
```

**`seo/engine/word_lists.py`** (excerpt):

```python
WORD_LISTS = {
    'captions': {
        'adjectives': ['breathtaking', 'golden', 'serene', 'vibrant', 'timeless', ...],
        'nouns': ['adventure', 'memory', 'journey', 'moment', 'story', ...],
        'verbs': ['explore', 'discover', 'embrace', 'chase', 'capture', ...],
        'emotions': ['joy', 'wonder', 'gratitude', 'excitement', 'peace', ...],
    },
    'quotes': { ... },
    'interview-questions': { ... },
    # ... one entry per SEOCategory slug
}
```

**`seo/engine/templates.py`** (excerpt):

```python
CONTENT_TEMPLATES = {
    'captions': [
        "Living for {adj} {noun}s like this. ✨ #{topic}",
        "Every {noun} tells a story. This one is {adj}. 📸",
        "Chasing {adj} {noun}s and loving every second. 🌟",
        # ... 20+ templates per category
    ],
    'interview-questions': [
        "What is the difference between {noun} and {adj} in {topic}?",
        "Explain how you would {verb} a {noun} in {topic}.",
        # ...
    ],
    'default': [
        "{number} reasons why {topic} is {adj}.",
        "The {adj} guide to {topic}.",
    ],
}
```

### `generate_seo_pages` Management Command

```python
# seo/management/commands/generate_seo_pages.py
# python manage.py generate_seo_pages
# Idempotent: uses update_or_create on slug
# Generates 500+ unique topic slugs at initial launch

TOPIC_SEEDS = {
    'captions': [
        ('Travel Instagram Captions', 'travel-instagram-captions'),
        ('Birthday Captions', 'birthday-captions'),
        ('Motivational Monday Captions', 'motivational-monday-captions'),
        # ... 50+ topics
    ],
    'quotes': [ ... ],
    'interview-questions': [ ... ],
    # ... all content types
}

class Command(BaseCommand):
    def handle(self, *args, **options):
        for cat_slug, topics in TOPIC_SEEDS.items():
            category = SEOCategory.objects.get(slug=cat_slug)
            for topic_name, topic_slug in topics:
                items = generate_items(cat_slug, topic_name, topic_slug, count=30)
                page, created = SEOPage.objects.update_or_create(
                    slug=topic_slug,
                    defaults={
                        'category': category,
                        'topic': topic_name,
                        'items': items,
                    }
                )
                # Link related tools
                related_tools = Tool.objects.filter(
                    tags__icontains=cat_slug.split('-')[0], is_active=True
                )[:3]
                page.related_tools.set(related_tools)
```

### SEO Page Rendering

**Pagination**: `seo/views.py` uses Django's `Paginator` with `per_page=20`. The canonical URL always points to the first page (`?page=1` is omitted from canonical).

**Internal linking**: Each page template renders:
1. `page.related_tools.all()[:3]` — links to related Tool pages
2. `SEOPage.objects.filter(category=page.category).exclude(pk=page.pk).order_by('?')[:3]` — links to related SEO pages

**Design decision**: Random ordering for related SEO pages uses `order_by('?')` which is acceptable for small result sets (< 1000 pages per category). For larger datasets, a deterministic ordering by slug proximity would be more efficient.

---

## Design System

### TailwindCSS Configuration

The existing `base.html` uses inline CSS with CSS custom properties. The Design System formalises these as a TailwindCSS config (`tailwind.config.js`) for use in new templates, while keeping the existing inline styles for backward compatibility.

```javascript
// tailwind.config.js
module.exports = {
  content: ['./templates/**/*.html', './static/js/**/*.js'],
  darkMode: 'class',  // toggled via <html class="dark">
  theme: {
    extend: {
      colors: {
        bg:       '#0A0A0F',
        surface:  'rgba(255,255,255,0.04)',
        border:   'rgba(255,255,255,0.08)',
        primary:  '#6C63FF',
        accent:   '#00F5D4',
        danger:   '#FF6B6B',
        text:     '#F0F0F5',
        muted:    'rgba(240,240,245,0.5)',
        // Light mode overrides
        'light-bg':      '#F8F9FA',
        'light-surface': '#FFFFFF',
        'light-text':    '#1A1A2E',
      },
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        body:    ['DM Sans', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
      backdropBlur: {
        glass: '20px',
      },
      borderRadius: {
        card: '16px',
        pill: '50px',
      },
    },
  },
  plugins: [],
}
```

### Dark/Light Mode Toggle

```javascript
// static/js/theme.js — loaded in <head> to prevent FOUC
(function() {
  const stored = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (stored === 'light' || (!stored && !prefersDark)) {
    document.documentElement.classList.remove('dark');
    document.documentElement.classList.add('light');
  } else {
    document.documentElement.classList.add('dark');
  }
})();

function toggleTheme() {
  const isDark = document.documentElement.classList.contains('dark');
  document.documentElement.classList.toggle('dark', !isDark);
  document.documentElement.classList.toggle('light', isDark);
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
}
```

### Glassmorphism Tokens

The existing CSS custom properties in `base.html` define the glassmorphism aesthetic. Key tokens:

| Token | Dark Value | Light Value |
|---|---|---|
| `--bg` | `#0A0A0F` | `#F8F9FA` |
| `--surface` | `rgba(255,255,255,0.04)` | `rgba(0,0,0,0.04)` |
| `--border` | `rgba(255,255,255,0.08)` | `rgba(0,0,0,0.1)` |
| `--primary` | `#6C63FF` | `#5A52E0` |
| `--accent` | `#00F5D4` | `#00C4A8` |
| `--text` | `#F0F0F5` | `#1A1A2E` |
| `--muted` | `rgba(240,240,245,0.5)` | `rgba(26,26,46,0.5)` |

Light mode overrides are applied via `.light` class on `<html>`:

```css
html.light {
  --bg: #F8F9FA;
  --surface: rgba(0,0,0,0.04);
  --border: rgba(0,0,0,0.1);
  --text: #1A1A2E;
  --muted: rgba(26,26,46,0.5);
}
```

### Responsive Layout

The existing `tools-shell` grid handles desktop layout. Mobile layout uses the `os-dock` bottom navigation (already implemented). Breakpoints:

| Breakpoint | Layout |
|---|---|
| < 640px | Single column, bottom dock, hidden sidebar |
| 640–768px | Single column, bottom dock |
| 768–1024px | Single column, no sidebar |
| 1024–1280px | Two-column (sidebar + main) |
| > 1280px | Three-column (sidebar + main + actions panel) |

### Template Partials

All partials live in `templates/partials/`:

| Partial | Usage |
|---|---|
| `tool_card.html` | `{% include "partials/tool_card.html" with tool=tool %}` |
| `category_card.html` | `{% include "partials/category_card.html" with category=cat %}` |
| `breadcrumb.html` | `{% include "partials/breadcrumb.html" with crumbs=crumbs %}` |
| `ad_slot.html` | `{% include "partials/ad_slot.html" with slot_id="..." %}` |
| `tool_action_bar.html` | `{% include "partials/tool_action_bar.html" with label="Format" %}` |
| `search_result_item.html` | Used inside Command Palette JS template |
| `paywall_overlay.html` | `{% include "partials/paywall_overlay.html" with tool=tool %}` |
| `auth_prompt.html` | Non-blocking login nudge for guest users |

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Tool metadata auto-generation invariant

*For any* Tool instance saved with an empty `meta_title` and/or empty `meta_description`, the saved values SHALL satisfy: `meta_title == f"{name} — Free Online Tool | LamGen"[:70]` and `meta_description == short_desc[:160]`.

**Validates: Requirements 2.6, 2.7**

### Property 2: Tool canonical URL pattern

*For any* active Tool with a valid category, `tool.get_absolute_url()` SHALL return a string matching the pattern `/tools/{category.slug}/{tool.slug}/`, and the URL SHALL resolve to the `tools:tool` view without raising a `NoReverseMatch`.

**Validates: Requirements 2.8**

### Property 3: Search result bounds

*For any* query string of length 0 or 1, the search endpoint SHALL return `{"results": []}` with no database query. *For any* query string of length ≥ 2, the search endpoint SHALL return a results list of length between 0 and 15 (inclusive).

**Validates: Requirements 3.2, 3.3**

### Property 4: Metadata length invariants

*For any* Tool or SEOPage instance, the stored `meta_title` SHALL have length ≤ 70 characters and the stored `meta_description` SHALL have length ≤ 160 characters, regardless of the length of the input `name`, `short_desc`, or `topic` fields.

**Validates: Requirements 7.1, 7.2**

### Property 5: Bookmark toggle idempotence

*For any* authenticated user and any active Tool, calling the bookmark toggle endpoint twice in sequence SHALL return the bookmark to its original state: `toggle(toggle(initial_state)) == initial_state`.

**Validates: Requirements 9.7**

### Property 6: Unauthenticated bookmark rejection

*For any* tool slug, a POST request to `/tools/bookmark/toggle/` from an unauthenticated client SHALL always return HTTP 401 with body `{"error": "Login required"}`, regardless of the tool slug value.

**Validates: Requirements 9.8**

### Property 7: Session bookmark merge completeness

*For any* set of up to 10 valid tool slugs stored in a guest session's `session_bookmarks`, after the guest authenticates (login or register), all slugs in the session set SHALL appear as `ToolBookmark` records for that user in the database.

**Validates: Requirements 9.3**

### Property 8: SEO content determinism

*For any* topic slug, calling `generate_items(category_slug, topic, slug)` twice SHALL produce identical item lists. The output is a pure function of the slug — no randomness leaks between calls.

**Validates: Requirements 14.4**

### Property 9: SEO content minimum count

*For any* topic slug passed to `generate_items()`, the returned list SHALL contain at least 20 items after deduplication.

**Validates: Requirements 14.1**

### Property 10: MIME validation rejects mismatched files

*For any* file whose content-detected MIME type (via `python-magic`) does not appear in `ALLOWED_MIMES[expected_type]`, `validate_mime(file_obj, expected_type)` SHALL return `(False, detected_mime)`. *For any* file whose detected MIME type does appear in the allowed list, it SHALL return `(True, detected_mime)`.

**Validates: Requirements 13.1, 5.2**

---

## Error Handling

### File Upload Errors

| Condition | HTTP Status | Response |
|---|---|---|
| File size > `MAX_UPLOAD_SIZE` | 413 | `{"error": "File too large. Maximum size is {MAX_UPLOAD_SIZE}MB."}` |
| MIME type mismatch | 400 | `{"error": "Invalid file type. Expected {expected}, got {detected}."}` |
| Processing failure | 500 | `{"error": "Processing failed. Please try again."}` |

`MAX_UPLOAD_SIZE` is set in `config/settings.py` (default: 50MB). The size check happens before reading the file body:

```python
if request.META.get('CONTENT_LENGTH', 0) and int(request.META['CONTENT_LENGTH']) > settings.MAX_UPLOAD_SIZE:
    return JsonResponse({'error': f'File too large.'}, status=413)
```

### Search Errors

- Query < 2 chars: returns `{"results": []}` with HTTP 200 (not an error)
- Rate limit exceeded: HTTP 429 with `{"error": "Rate limit exceeded"}`
- Database error: logged, returns `{"results": []}` with HTTP 200 (graceful degradation)

### Browser Tool Errors

All Browser_Tools follow this error display pattern:

```javascript
function showError(message) {
    const el = document.getElementById('error-msg');
    el.textContent = message;
    el.classList.remove('hidden');
    document.getElementById('output-section').classList.add('hidden');
}

function showSuccess() {
    document.getElementById('error-msg').classList.add('hidden');
    document.getElementById('output-section').classList.remove('hidden');
}
```

### Missing Tool Templates

`tool_view` catches `TemplateDoesNotExist` and falls back to `tools/generic_tool.html`. This prevents 500 errors when a tool record exists but its template hasn't been created yet.

### SEO Page Not Found

`get_object_or_404` is used in all SEO views. Django's default 404 handler returns the `404.html` template. The platform defines a custom `404.html` that includes the search bar and trending tools to retain user engagement.

### Celery Task Failures

Cleanup tasks use `ignore_errors=True` in `shutil.rmtree`. If a file cannot be deleted (permissions, already deleted), the task logs a warning and continues. Tasks are retried automatically by Celery's default retry policy.

---

## Testing Strategy

### Dual Testing Approach

The platform uses both example-based unit tests and property-based tests (Hypothesis). The existing test suite uses Hypothesis (`hypothesis==6.112.1`) and pytest-django — no new testing dependencies are required.

### Property-Based Tests

Each correctness property maps to a single Hypothesis test. All property tests run a minimum of 100 iterations (configured via `settings.suppress_health_check` and `@settings(max_examples=100)`).

**Test file**: `tests/test_tools_properties.py`

```python
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st
import pytest

# Property 1: Tool metadata auto-generation invariant
# Feature: lamgen-tools-ecosystem, Property 1: Tool metadata auto-generation invariant
@given(
    name=st.text(min_size=1, max_size=100),
    short_desc=st.text(min_size=0, max_size=500),
)
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_tool_metadata_autogeneration(name, short_desc):
    from tools.models import Tool, ToolCategory
    cat = ToolCategory.objects.get_or_create(slug='test-cat', defaults={'name': 'Test'})[0]
    tool = Tool(name=name, short_desc=short_desc, category=cat,
                template_name='tools/generic_tool.html', description='x')
    tool.save()
    assert tool.meta_title == f'{name} — Free Online Tool | LamGen'[:70]
    assert tool.meta_description == short_desc[:160]
    assert len(tool.meta_title) <= 70
    assert len(tool.meta_description) <= 160


# Property 2: Tool canonical URL pattern
# Feature: lamgen-tools-ecosystem, Property 2: Tool canonical URL pattern
@given(
    cat_slug=st.from_regex(r'[a-z][a-z0-9-]{2,20}', fullmatch=True),
    tool_slug=st.from_regex(r'[a-z][a-z0-9-]{2,30}', fullmatch=True),
)
@h_settings(max_examples=100)
@pytest.mark.django_db
def test_tool_canonical_url(cat_slug, tool_slug):
    from tools.models import Tool, ToolCategory
    cat = ToolCategory.objects.get_or_create(slug=cat_slug, defaults={'name': cat_slug})[0]
    tool = Tool.objects.get_or_create(
        slug=tool_slug,
        defaults={'name': tool_slug, 'category': cat, 'short_desc': 'x',
                  'template_name': 'tools/generic_tool.html', 'description': 'x'}
    )[0]
    url = tool.get_absolute_url()
    assert url == f'/tools/{cat_slug}/{tool_slug}/'


# Property 3: Search result bounds
# Feature: lamgen-tools-ecosystem, Property 3: Search result bounds
@given(q=st.text(min_size=0, max_size=1))
@h_settings(max_examples=100)
@pytest.mark.django_db
def test_search_short_query_returns_empty(client, q):
    response = client.get('/tools/search/', {'q': q})
    assert response.status_code == 200
    assert response.json()['results'] == []

@given(q=st.text(min_size=2, max_size=100))
@h_settings(max_examples=100)
@pytest.mark.django_db
def test_search_result_count_bounded(client, q):
    response = client.get('/tools/search/', {'q': q})
    assert response.status_code == 200
    assert len(response.json()['results']) <= 15


# Property 4: Metadata length invariants
# Feature: lamgen-tools-ecosystem, Property 4: Metadata length invariants
@given(
    name=st.text(min_size=1, max_size=300),
    short_desc=st.text(min_size=0, max_size=1000),
)
@h_settings(max_examples=100)
@pytest.mark.django_db
def test_metadata_length_invariants(name, short_desc):
    from tools.models import Tool, ToolCategory
    cat = ToolCategory.objects.get_or_create(slug='meta-test', defaults={'name': 'Meta'})[0]
    tool = Tool(name=name, short_desc=short_desc, category=cat,
                template_name='tools/generic_tool.html', description='x')
    tool.save()
    assert len(tool.meta_title) <= 70
    assert len(tool.meta_description) <= 160


# Property 5: Bookmark toggle idempotence
# Feature: lamgen-tools-ecosystem, Property 5: Bookmark toggle idempotence
@pytest.mark.django_db
def test_bookmark_toggle_idempotence(client):
    from django.contrib.auth import get_user_model
    from tools.models import Tool, ToolCategory
    User = get_user_model()
    user = User.objects.create_user('testuser_bm', password='pass', email='bm@test.com', university='x')
    cat = ToolCategory.objects.get_or_create(slug='bm-cat', defaults={'name': 'BM'})[0]
    tool = Tool.objects.get_or_create(
        slug='bm-tool',
        defaults={'name': 'BM Tool', 'category': cat, 'short_desc': 'x',
                  'template_name': 'tools/generic_tool.html', 'description': 'x'}
    )[0]
    client.force_login(user)
    import json
    # Initial state: not bookmarked
    r1 = client.post('/tools/bookmark/toggle/', json.dumps({'tool_slug': 'bm-tool'}),
                     content_type='application/json')
    assert r1.json()['bookmarked'] is True
    r2 = client.post('/tools/bookmark/toggle/', json.dumps({'tool_slug': 'bm-tool'}),
                     content_type='application/json')
    assert r2.json()['bookmarked'] is False  # back to original state


# Property 6: Unauthenticated bookmark rejection
# Feature: lamgen-tools-ecosystem, Property 6: Unauthenticated bookmark rejection
@given(tool_slug=st.from_regex(r'[a-z][a-z0-9-]{2,20}', fullmatch=True))
@h_settings(max_examples=100)
@pytest.mark.django_db
def test_unauthenticated_bookmark_returns_401(client, tool_slug):
    import json
    response = client.post('/tools/bookmark/toggle/',
                           json.dumps({'tool_slug': tool_slug}),
                           content_type='application/json')
    assert response.status_code == 401
    assert response.json()['error'] == 'Login required'


# Property 8: SEO content determinism
# Feature: lamgen-tools-ecosystem, Property 8: SEO content determinism
@given(slug=st.from_regex(r'[a-z][a-z0-9-]{5,40}', fullmatch=True))
@h_settings(max_examples=100)
def test_seo_content_determinism(slug):
    from seo.engine.content_generator import generate_items
    result1 = generate_items('captions', 'Test Topic', slug)
    result2 = generate_items('captions', 'Test Topic', slug)
    assert result1 == result2


# Property 9: SEO content minimum count
# Feature: lamgen-tools-ecosystem, Property 9: SEO content minimum count
@given(slug=st.from_regex(r'[a-z][a-z0-9-]{5,40}', fullmatch=True))
@h_settings(max_examples=100)
def test_seo_content_minimum_count(slug):
    from seo.engine.content_generator import generate_items
    items = generate_items('captions', 'Test Topic', slug)
    assert len(items) >= 20


# Property 10: MIME validation rejects mismatched files
# Feature: lamgen-tools-ecosystem, Property 10: MIME validation rejects mismatched files
@given(content=st.binary(min_size=100, max_size=4096))
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_mime_validation_rejects_non_pdf_as_pdf(content):
    import io
    from tools.utils.file_validation import validate_mime
    # Random binary data is almost never a valid PDF
    # We test that the function returns a boolean tuple without raising
    file_obj = io.BytesIO(content)
    is_valid, detected = validate_mime(file_obj, 'pdf')
    assert isinstance(is_valid, bool)
    assert isinstance(detected, str)
    # A valid PDF must start with %PDF-
    if not content.startswith(b'%PDF-'):
        assert is_valid is False
```

### Unit Tests

**Test file**: `tests/test_tools_unit.py`

Key example-based tests:

- `test_seed_tools_idempotent`: Run `seed_tools` twice, verify no duplicate records
- `test_category_page_returns_active_tools_only`: Category view excludes `is_active=False` tools
- `test_tool_view_increments_session_history`: `recent_tools` session key updated on tool visit
- `test_bookmark_merge_on_login`: Session bookmarks transferred to DB on login
- `test_search_intent_expansion`: Query "convert json" returns more results than "json" alone
- `test_generate_seo_pages_idempotent`: Run command twice, verify no duplicate SEOPage records
- `test_seo_page_has_related_tools`: After `generate_seo_pages`, pages have `related_tools` populated
- `test_ad_slot_partial_renders_data_attribute`: Ad slot template renders correct `data-ad-slot` attribute
- `test_pro_tool_shows_paywall_for_guest`: `is_pro=True` tool renders paywall overlay for unauthenticated user
- `test_json_ld_software_application_schema`: Tool page response contains valid JSON-LD with `@type: SoftwareApplication`
- `test_sitemap_cached_24h`: Sitemap response has `Cache-Control: max-age=86400`
- `test_robots_txt_disallows_admin`: `/robots.txt` contains `Disallow: /admin/`
- `test_file_upload_413_on_oversized_file`: Backend tool returns 413 for files > `MAX_UPLOAD_SIZE`
- `test_cleanup_task_deletes_old_uploads`: Celery task removes directories older than 1 hour

### Integration Tests

- `test_full_tool_page_render`: End-to-end render of a tool page with all context variables
- `test_sitemap_includes_all_active_tools`: Sitemap XML contains URLs for all active tools
- `test_command_palette_search_latency`: Search endpoint responds within 300ms for typical queries (measured in test)

### Test Configuration

```ini
# pytest.ini (existing, no changes needed)
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests/test_*.py
```

Hypothesis database is already configured (`.hypothesis/` directory exists in the project).
