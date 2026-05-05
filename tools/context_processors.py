from django.core.cache import cache
from .models import ToolCategory, Tool, ToolBookmark


def tools_context(request):
    """Global context processor — inject tool categories & bookmarks into every template."""
    categories = cache.get('tool_categories_nav_v2')
    if categories is None:
        categories = list(
            ToolCategory.objects.filter(is_active=True).prefetch_related('tools').order_by('order', 'name')
        )
        cache.set('tool_categories_nav_v2', categories, 60 * 30)

    bookmarked_slugs = []
    if request.user.is_authenticated:
        cache_key = f'bookmarks_{request.user.pk}'
        bookmarked_slugs = cache.get(cache_key)
        if bookmarked_slugs is None:
            bookmarked_slugs = list(
                ToolBookmark.objects.filter(user=request.user).values_list('tool__slug', flat=True)
            )
            cache.set(cache_key, bookmarked_slugs, 60 * 5)

    return {
        'nav_categories': categories,
        'bookmarked_slugs': bookmarked_slugs,
    }
