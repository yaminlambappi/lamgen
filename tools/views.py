from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import cache_page, cache_control
from django.db.models import Q, F
from django.core.cache import cache
from .models import Tool, ToolCategory, ToolBookmark, ToolUsageHistory
import json


@cache_control(public=True, max_age=60)
def index(request):
    """All tools homepage — categorized grid."""
    categories = ToolCategory.objects.filter(is_active=True).prefetch_related(
        'tools'
    )
    featured_tools = Tool.objects.filter(is_active=True, is_featured=True).select_related('category')[:8]
    new_tools = Tool.objects.filter(is_active=True, is_new=True).select_related('category')[:6]
    trending = Tool.objects.filter(is_active=True).order_by('-view_count').select_related('category')[:8]

    # Recent tools from session
    recent_slugs = request.session.get('recent_tools', [])
    recent_tools = list(Tool.objects.filter(slug__in=recent_slugs, is_active=True).select_related('category'))
    # Restore order
    slug_order = {s: i for i, s in enumerate(recent_slugs)}
    recent_tools.sort(key=lambda t: slug_order.get(t.slug, 999))

    bookmarked_slugs = []
    if request.user.is_authenticated:
        bookmarked_slugs = list(
            ToolBookmark.objects.filter(user=request.user).values_list('tool__slug', flat=True)
        )

    return render(request, 'tools/index.html', {
        'categories': categories,
        'featured_tools': featured_tools,
        'new_tools': new_tools,
        'trending': trending,
        'recent_tools': recent_tools[:5],
        'bookmarked_slugs': bookmarked_slugs,
        'page_title': 'Home — LamGen',
        'meta_description': 'LamGen Home. Access your tools, active nodes, and smart systems.',
    })

@cache_control(public=True, max_age=60)
def tools_index_view(request):
    """All tools ecosystem explorer."""
    categories = ToolCategory.objects.filter(is_active=True).prefetch_related('tools')
    return render(request, 'tools/workspaces.html', {
        'categories': categories,
        'page_title': 'All Tools — LamGen',
        'meta_description': 'Browse all LamGen ecosystems and tool categories.',
    })


@cache_control(public=True, max_age=600)
def category_view(request, category_slug):
    """Category listing page."""
    category = get_object_or_404(ToolCategory, slug=category_slug, is_active=True)
    tools = list(Tool.objects.filter(category=category, is_active=True).order_by('order', 'name'))

    bookmarked_slugs = []
    if request.user.is_authenticated:
        bookmarked_slugs = list(
            ToolBookmark.objects.filter(user=request.user, tool__category=category).values_list('tool__slug', flat=True)
        )
        
    # Group tools dynamically for mega-menu style
    tool_groups = {}
    for tool in tools:
        group_name = "Other Utilities"
        if tool.tags:
            group_name = tool.tags.split(',')[0].strip().title()
        else:
            name_lower = tool.name.lower()
            if "format" in name_lower or "valid" in name_lower or "lint" in name_lower:
                group_name = "Formatting & Validation"
            elif "convert" in name_lower or " to " in name_lower:
                group_name = "Converters"
            elif "generat" in name_lower or "build" in name_lower or "creat" in name_lower:
                group_name = "Generators"
            elif "encod" in name_lower or "decod" in name_lower or "hash" in name_lower or "cipher" in name_lower:
                group_name = "Security & Encoding"
            elif "compress" in name_lower or "minif" in name_lower or "optimiz" in name_lower:
                group_name = "Optimization"
            elif "split" in name_lower or "merg" in name_lower or "extract" in name_lower:
                group_name = "Manipulation"

        if group_name not in tool_groups:
            tool_groups[group_name] = []
        tool_groups[group_name].append(tool)

    # Sort groups alphabetically, but keep "Other Utilities" at the end
    sorted_groups = []
    for k in sorted(tool_groups.keys()):
        if k != "Other Utilities":
            sorted_groups.append((k, tool_groups[k]))
    if "Other Utilities" in tool_groups:
        sorted_groups.append(("Other Utilities", tool_groups["Other Utilities"]))

    return render(request, 'tools/category.html', {
        'category': category,
        'tools': tools,
        'tool_groups': sorted_groups,
        'bookmarked_slugs': bookmarked_slugs,
        'page_title': f'{category.name} — LamGen',
        'meta_description': category.description[:160] if category.description else f'Free {category.name.lower()} tools online. No download, no signup required.',
    })


@cache_control(public=True, max_age=60)
def tool_view(request, category_slug, tool_slug):
    """Individual tool page renderer."""
    category = get_object_or_404(ToolCategory, slug=category_slug, is_active=True)
    tool = get_object_or_404(Tool, slug=tool_slug, category=category, is_active=True)

    # Increment view count (cached counter to reduce DB writes)
    cache_key = f'tool_views_{tool.pk}'
    views = cache.get(cache_key, 0)
    views += 1
    cache.set(cache_key, views, 60 * 5)
    if views % 10 == 0:
        Tool.objects.filter(pk=tool.pk).update(view_count=F('view_count') + 1)

    # Track in session
    recent = request.session.get('recent_tools', [])
    if tool.slug in recent:
        recent.remove(tool.slug)
    recent.insert(0, tool.slug)
    request.session['recent_tools'] = recent[:10]
    request.session.modified = True

    # Track in DB (for logged-in users) - UNIQUE entries per tool
    if request.user.is_authenticated:
        ToolUsageHistory.objects.update_or_create(
            user=request.user, 
            tool=tool,
            defaults={} # auto_now=True on used_at handles the timestamp
        )

    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = ToolBookmark.objects.filter(user=request.user, tool=tool).exists()

    # Related tools in the same toolset
    related_tools = Tool.objects.filter(category=category, is_active=True).exclude(id=tool.id)[:10]

    # Handle missing templates gracefully
    from django.template.loader import get_template, TemplateDoesNotExist
    
    actual_template = tool.template_name
    try:
        get_template(actual_template)
    except TemplateDoesNotExist:
        actual_template = 'tools/generic_tool.html'

    return render(request, actual_template, {
        'tool': tool,
        'category': category,
        'is_bookmarked': is_bookmarked,
        'related_tools': related_tools,
        'page_title': tool.meta_title or f'{tool.name} — Free Online Tool | LamGen',
        'meta_description': tool.meta_description or tool.short_desc,
    })


@require_GET
def search_view(request):
    """AJAX tool search endpoint."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    # Natural Language Intent Mapping
    q_clean = q.lower().replace('i want to ', '').replace('how to ', '').replace('show me ', '').replace('can you ', '')
    
    # Keyword expansions for common intents
    intent_map = {
        'convert': ['converter', 'transform', 'to'],
        'format': ['formatter', 'beautify', 'clean'],
        'validate': ['validator', 'checker', 'verify'],
        'make': ['generator', 'create', 'builder'],
    }

    words = q_clean.split()
    query = Q(name__icontains=q_clean) | Q(short_desc__icontains=q_clean) | Q(tags__icontains=q_clean)
    
    for word in words:
        if word in intent_map:
            for expansion in intent_map[word]:
                query |= Q(name__icontains=expansion) | Q(tags__icontains=expansion)
        query |= Q(name__icontains=word) | Q(tags__icontains=word)

    tools = list(Tool.objects.filter(query, is_active=True).select_related('category').distinct())

    # Calculate relevance score for sorting
    for t in tools:
        score = 0
        t_name = t.name.lower()
        t_desc = (t.short_desc or '').lower()
        t_tags = (t.tags or '').lower()
        
        # Exact full query match gets highest priority
        if q_clean in t_name:
            score += 100
        elif q_clean in t_desc or q_clean in t_tags:
            score += 50
            
        # Individual word matches
        for word in words:
            if word in t_name:
                score += 10
            if word in t_desc or word in t_tags:
                score += 5
                
        t.relevance_score = score
        
    # Sort by relevance score (descending), then alphabetically
    tools.sort(key=lambda t: (-t.relevance_score, t.name))
    tools = tools[:15]

    results = []
    for t in tools:
        results.append({
            'name': t.name,
            'short_desc': t.short_desc,
            'icon': t.icon,
            'url': t.get_absolute_url(),
            'category': t.category.name,
            'category_color_from': t.category.color_from,
        })

    return JsonResponse({'results': results})


@require_POST
def toggle_bookmark(request):
    """Toggle bookmark for a tool (auth required)."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    try:
        data = json.loads(request.body)
        tool_slug = data.get('tool_slug')
    except (json.JSONDecodeError, AttributeError):
        tool_slug = request.POST.get('tool_slug')

    tool = get_object_or_404(Tool, slug=tool_slug, is_active=True)
    bookmark, created = ToolBookmark.objects.get_or_create(user=request.user, tool=tool)

    if not created:
        bookmark.delete()
        return JsonResponse({'bookmarked': False, 'message': 'Bookmark removed'})

    return JsonResponse({'bookmarked': True, 'message': 'Bookmarked!'})


@cache_control(public=True, max_age=3600)
@cache_page(60 * 60)
@require_GET
def trending_view(request):
    """Trending tools page."""
    tools = Tool.objects.filter(is_active=True).order_by('-view_count').select_related('category')[:30]
    return render(request, 'tools/trending.html', {
        'tools': tools,
        'page_title': 'Trending Tools — LamGen',
        'meta_description': 'Most popular free online tools on LamGen. See what others are using right now.',
    })


def models_F(val):
    from django.db.models import F
    return F('view_count') + 1
