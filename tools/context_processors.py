from django.core.cache import cache
from django.urls import reverse
from .models import ToolCategory, Tool, ToolBookmark
from config.games import GAMES_CONFIG
from .services.islamic_panel import IslamicContentService, PrayerTimesService


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

    try:
        islamic_panel = IslamicContentService.get_panel_context()
        islamic_panel['api_url'] = reverse('tools:islamic_panel_api')
    except Exception as e:
        # Fallback data if service fails
        fallback_snapshot = PrayerTimesService._build_placeholder_snapshot(
            PrayerTimesService.DEFAULT_LOCATION['latitude'],
            PrayerTimesService.DEFAULT_LOCATION['longitude'],
            fallback_label=PrayerTimesService.DEFAULT_LOCATION['label'],
        )
        islamic_panel = {
            'prayer': fallback_snapshot,
            'api_url': '#'
        }

    return {
        'nav_categories': categories,
        'bookmarked_slugs': bookmarked_slugs,
        'nav_games': GAMES_CONFIG,
        'islamic_panel': islamic_panel,
    }
