from pathlib import Path

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.sitemaps.views import sitemap, index as sitemap_index
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView

_BASE_DIR = Path(__file__).resolve().parent.parent

from apps.tools.views import og_image_view
from apps.generation.views import serve_protected_media

# Import new sitemap engine if available, fallback to old
try:
    from apps.seo.engine.sitemap import get_sitemaps as get_new_sitemaps, rebuild_all_sitemaps, ping_search_engines
    USE_NEW_SITEMAP = True
except ImportError:
    USE_NEW_SITEMAP = False
    from apps.seo.sitemaps import get_sitemaps


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /users/",
        "Disallow: /api/",
        "Disallow: /media/og/",
        "",
        # Embed pages are intentionally iframed — noindex is set in the view,
        # but we also disallow crawling to save crawl budget.
        "Disallow: /tools/*/embed/",
        "",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# Sitemaps
if USE_NEW_SITEMAP:
    sitemaps = get_new_sitemaps()
else:
    sitemaps = get_sitemaps()

from apps.tools.views import index as control_center_view
from apps.tools.admin_views import tool_system_health_view

_urlpatterns_prefix = []
if settings.DEBUG:
    # In development, serve media files directly from disk without auth so
    # developers can access files without needing to log in.  In production
    # this block is skipped and the authenticated serve_protected_media view
    # (below) handles all /media/ requests via Nginx X-Accel-Redirect.
    _urlpatterns_prefix += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = _urlpatterns_prefix + [
    path("admin/system-health/", admin.site.admin_view(tool_system_health_view), name="admin_tool_system_health"),
    path("admin/", admin.site.urls),
    path("favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "img/favicon.svg", permanent=False)),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("og-image/<slug:category_slug>/<slug:tool_slug>.png", og_image_view, name="og_image"),
    # Authenticated media serving — replaces direct Nginx /media/ serving (Req 5.1, 5.2, 5.3)
    # In DEBUG mode the static() patterns above take precedence (matched first).
    path("media/<path:path>", serve_protected_media, name="serve_protected_media"),
    # Sitemaps with Edge Caching (Paginated for scale)
    path("sitemap.xml", cache_page(86400)(sitemap_index), {"sitemaps": sitemaps, "template_name": "seo/sitemap.xml"}, name="django.contrib.sitemaps.views.index"),
    path("sitemap-<section>.xml", cache_page(86400)(sitemap), {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    # Legal and contact pages
    path("privacy/", lambda request: render(request, "legal/privacy.html"), name="privacy"),
    path("terms/", lambda request: render(request, "legal/terms.html"), name="terms"),
    path("about/", lambda request: render(request, "about/company.html"), name="about"),
    path("contact/", lambda request: render(request, "contact/contact.html"), name="contact"),
    # Static files
    path(
        "ads.txt",
        lambda request: HttpResponse(
            (_BASE_DIR / "public" / "ads.txt").read_text(encoding="utf-8"),
            content_type="text/plain",
        ),
        name="ads.txt",
    ),
    # Non-localized includes
    path("users/", include("apps.users.urls")),
    path("thesis/", include("apps.thesis.urls")),
    path("generation/", include("apps.generation.urls")),
    path("games/", include("apps.games.urls", namespace="games")),
]

urlpatterns += i18n_patterns(
    path("", control_center_view, name="home"),
    path("tools/", include("apps.tools.urls", namespace="tools")),
    path("content/", include("apps.seo.urls", namespace="seo")),
    path("blog/", include("apps.blog.urls", namespace="blog")),
    prefix_default_language=False,
)

if settings.DEBUG:
    pass  # DEBUG media serving is already prepended above
