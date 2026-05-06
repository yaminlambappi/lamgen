from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap, index as sitemap_index
from django.views.decorators.cache import cache_page
from tools.views import og_image_view


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /accounts/',
        'Disallow: /api/',
        'Disallow: /embed/',
        '',
        f'Sitemap: {settings.SITE_URL}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


# Sitemaps
def get_sitemaps():
    try:
        from seo.sitemaps import ToolSitemap, CategorySitemap, SEOPageSitemap, StaticViewSitemap, LongTailSitemap
        from blog.sitemaps import BlogSitemap
        return {
            'static': StaticViewSitemap,
            'tools': ToolSitemap,
            'categories': CategorySitemap,
            'seo_pages': SEOPageSitemap,
            'longtail': LongTailSitemap,
            'blog': BlogSitemap,
        }
    except Exception:
        return {}


sitemaps = get_sitemaps()

from tools.views import index as control_center_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('og-image/<slug:category_slug>/<slug:tool_slug>.png', og_image_view, name='og_image'),
    # Sitemaps with Edge Caching (Paginated for scale)
    path('sitemap.xml', cache_page(86400)(sitemap_index), {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.index'),
    path('sitemap-<section>.xml', cache_page(86400)(sitemap), {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # Non-localized includes
    path('accounts/', include('accounts.urls')),
    path('thesis/', include('thesis.urls')),
    path('generation/', include('generation.urls')),
    path('games/', include('games.urls', namespace='games')),
]

urlpatterns += i18n_patterns(
    path('', control_center_view, name='home'),
    path('tools/', include('tools.urls', namespace='tools')),
    path('content/', include('seo.urls', namespace='seo')),
    path('blog/', include('blog.urls', namespace='blog')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

