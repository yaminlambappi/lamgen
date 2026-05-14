from django.core.cache import cache
from django.urls import reverse
from .models import ToolCategory, Tool, ToolBookmark
from config.games import GAMES_CONFIG



_TOOL_COUNT_CACHE_KEY = "tool_count_active_v1"


def tools_context(request):
    """Global context processor — inject tool categories & bookmarks into every template."""
    try:
        categories = cache.get('tool_categories_nav_v2')
    except Exception:
        categories = None
    if categories is None:
        categories = list(
            ToolCategory.objects.filter(is_active=True).prefetch_related('tools').order_by('order', 'name')
        )
        try:
            cache.set('tool_categories_nav_v2', categories, 60 * 30)
        except Exception:
            pass

    try:
        active_tool_count = cache.get(_TOOL_COUNT_CACHE_KEY)
    except Exception:
        active_tool_count = None
    if active_tool_count is None:
        active_tool_count = Tool.objects.filter(is_active=True).count()
        try:
            cache.set(_TOOL_COUNT_CACHE_KEY, active_tool_count, 60 * 30)
        except Exception:
            pass

    bookmarked_slugs = []
    if hasattr(request, 'user') and request.user.is_authenticated:
        cache_key = f'bookmarks_{request.user.pk}'
        try:
            bookmarked_slugs = cache.get(cache_key)
        except Exception:
            bookmarked_slugs = None
        if bookmarked_slugs is None:
            bookmarked_slugs = list(
                ToolBookmark.objects.filter(user=request.user).values_list('tool__slug', flat=True)
            )
            try:
                cache.set(cache_key, bookmarked_slugs, 60 * 5)
            except Exception:
                pass



    return {
        'nav_categories': categories,
        'bookmarked_slugs': bookmarked_slugs,
        'nav_games': GAMES_CONFIG,

        'nav_active_tool_count': active_tool_count,
    }
