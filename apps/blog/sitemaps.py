from django.contrib.sitemaps import Sitemap
from .models import ContentArticle


class BlogSitemap(Sitemap):
    priority = 0.70
    changefreq = "weekly"
    protocol = "https"

    def items(self):
        return ContentArticle.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
