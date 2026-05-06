from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.contrib.sitemaps.views import sitemap, index as sitemap_index
from django.views.decorators.cache import cache_page


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /accounts/login/',
        'Disallow: /accounts/register/',
        '',
        f'Sitemap: {settings.SITE_URL}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


# Sitemaps
def get_sitemaps():
    try:
        from seo.sitemaps import ToolSitemap, CategorySitemap, SEOPageSitemap, StaticViewSitemap
        return {
            'static': StaticViewSitemap,
            'tools': ToolSitemap,
            'categories': CategorySitemap,
            'seo_pages': SEOPageSitemap,
        }
    except Exception:
        return {}


sitemaps = get_sitemaps()

from tools.views import index as control_center_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', control_center_view, name='home'),
    # Existing ecosystem apps
    path('accounts/', include('accounts.urls')),
    path('thesis/', include('thesis.urls')),
    path('generation/', include('generation.urls')),
    # New Tools Ecosystem
    path('tools/', include('tools.urls', namespace='tools')),
    # SEO Programmatic pages — mounted under /content/ to avoid collisions
    path('content/', include('seo.urls', namespace='seo')),
    # Platform utilities
    path('robots.txt', robots_txt, name='robots_txt'),
    # Sitemaps with Edge Caching (Paginated for scale)
    path('sitemap.xml', cache_page(86400)(sitemap_index), {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.index'),
    path('sitemap-<section>.xml', cache_page(86400)(sitemap), {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

