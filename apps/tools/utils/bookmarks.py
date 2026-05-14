"""Session bookmark merge utility — called after user login."""
from django.core.cache import cache
from apps.tools.models import Tool, ToolBookmark


def merge_session_bookmarks(request, user) -> int:
    """
    Transfer session bookmarks to DB bookmarks for a newly authenticated user.
    Returns the number of bookmarks merged.
    """
    session_slugs: list = request.session.pop('session_bookmarks', [])
    if not session_slugs:
        return 0

    tools = Tool.objects.filter(slug__in=session_slugs, is_active=True)
    merged = 0
    for tool in tools:
        _, created = ToolBookmark.objects.get_or_create(user=user, tool=tool)
        if created:
            merged += 1

    # Invalidate cached bookmark list for this user
    cache.delete(f'bookmarks_{user.pk}')
    return merged
