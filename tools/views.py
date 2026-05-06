from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import cache_page, cache_control
from django.db.models import Q, F
from django.core.cache import cache
from .models import Tool, ToolCategory, ToolBookmark, ToolUsageHistory
from .utils.rate_limit import rate_limit
import json


@cache_control(public=True, max_age=60)
def index(request):
    """All tools homepage — categorized grid."""
    from django.db.models import Prefetch
    categories = ToolCategory.objects.filter(is_active=True).prefetch_related(
        Prefetch('tools', queryset=Tool.objects.filter(is_active=True))
    )
    featured_tools = Tool.objects.filter(is_active=True, is_featured=True).select_related('category')[:8]
    new_tools = Tool.objects.filter(is_active=True, is_new=True).select_related('category')[:6]
    trending = Tool.objects.filter(is_active=True).order_by('-view_count').select_related('category')[:8]

    recent_slugs = request.session.get('recent_tools', [])
    recent_tools = list(Tool.objects.filter(slug__in=recent_slugs, is_active=True).select_related('category'))
    slug_order = {s: i for i, s in enumerate(recent_slugs)}
    recent_tools.sort(key=lambda t: slug_order.get(t.slug, 999))

    bookmarked_slugs = []
    if request.user.is_authenticated:
        bookmarked_slugs = list(
            ToolBookmark.objects.filter(user=request.user).values_list('tool__slug', flat=True)
        )

    import json as _json
    from .utils.metadata import build_website_schema, build_organization_schema
    website_schema = _json.dumps(build_website_schema(request))
    org_schema = _json.dumps(build_organization_schema(request))

    return render(request, 'tools/index.html', {
        'categories': categories,
        'featured_tools': featured_tools,
        'new_tools': new_tools,
        'trending': trending,
        'recent_tools': recent_tools[:5],
        'bookmarked_slugs': bookmarked_slugs,
        'page_title': 'LamGen — 265+ Free Online Tools for Developers, Students & Writers',
        'meta_description': 'Free online tools for developers, students, writers and professionals. 265+ tools including JSON formatter, image compressor, word counter, GPA calculator and more. No signup, no ads, 100% private.',
        'canonical_url': request.build_absolute_uri('/'),
        'schema_json': website_schema,
        'org_schema': org_schema,
    })

@cache_control(public=True, max_age=60)
def tools_index_view(request):
    """All tools ecosystem explorer — dense launcher grid."""
    from django.db.models import Prefetch
    categories = ToolCategory.objects.filter(is_active=True).prefetch_related(
        Prefetch('tools', queryset=Tool.objects.filter(is_active=True))
    ).order_by('order', 'name')

    # Recent tools from session
    recent_slugs = request.session.get('recent_tools', [])
    recent_tools = list(Tool.objects.filter(slug__in=recent_slugs, is_active=True).select_related('category'))
    slug_order = {s: i for i, s in enumerate(recent_slugs)}
    recent_tools.sort(key=lambda t: slug_order.get(t.slug, 999))

    trending = Tool.objects.filter(is_active=True).order_by('-view_count').select_related('category')[:8]
    new_tools = Tool.objects.filter(is_active=True, is_new=True).select_related('category')[:6]

    return render(request, 'tools/workspaces.html', {
        'categories': categories,
        'recent_tools': recent_tools[:5],
        'trending': trending,
        'new_tools': new_tools,
        'page_title': 'All Tools — LamGen',
        'meta_description': 'Browse 256+ free online tools. Developer tools, writing tools, image tools, SEO tools and more.',
    })


@cache_control(public=True, max_age=600)
def category_view(request, category_slug):
    """Category listing page — SEO landing hub."""
    category = get_object_or_404(ToolCategory, slug=category_slug, is_active=True)
    tools = list(Tool.objects.filter(category=category, is_active=True).order_by('order', 'name'))

    bookmarked_slugs = []
    if request.user.is_authenticated:
        bookmarked_slugs = list(
            ToolBookmark.objects.filter(user=request.user, tool__category=category).values_list('tool__slug', flat=True)
        )

    # Group tools dynamically
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
            elif "encod" in name_lower or "decod" in name_lower or "hash" in name_lower:
                group_name = "Security & Encoding"
            elif "compress" in name_lower or "minif" in name_lower or "optimiz" in name_lower:
                group_name = "Optimization"
            elif "split" in name_lower or "merg" in name_lower or "extract" in name_lower:
                group_name = "Manipulation"
        if group_name not in tool_groups:
            tool_groups[group_name] = []
        tool_groups[group_name].append(tool)

    sorted_groups = []
    for k in sorted(tool_groups.keys()):
        if k != "Other Utilities":
            sorted_groups.append((k, tool_groups[k]))
    if "Other Utilities" in tool_groups:
        sorted_groups.append(("Other Utilities", tool_groups["Other Utilities"]))

    # SEO metadata
    import json as _json
    from .utils.metadata import build_breadcrumb_schema, build_category_schema

    cat_name = category.name
    tool_count = len(tools)
    meta_title = f'{cat_name} — {tool_count} Free Online Tools | LamGen'[:70]
    meta_desc = (
        category.description[:157] + '...'
        if category.description and len(category.description) > 160
        else category.description
        or f'Free {cat_name.lower()} online. {tool_count} tools — no download, no signup, instant results.'
    )

    breadcrumb_schema = _json.dumps(build_breadcrumb_schema(request, category))
    category_schema = _json.dumps(build_category_schema(category, tools, request))

    # Featured and trending tools for the landing hub
    featured = [t for t in tools if t.is_featured][:4]
    trending = sorted(tools, key=lambda t: -t.view_count)[:6]
    newest = [t for t in tools if t.is_new][:4]

    return render(request, 'tools/category.html', {
        'category': category,
        'tools': tools,
        'tool_groups': sorted_groups,
        'bookmarked_slugs': bookmarked_slugs,
        'featured_tools': featured,
        'trending_tools': trending,
        'newest_tools': newest,
        'tool_count': tool_count,
        'page_title': meta_title,
        'meta_description': meta_desc,
        'canonical_url': request.build_absolute_uri(category.get_absolute_url()),
        'schema_json': category_schema,
        'breadcrumb_schema': breadcrumb_schema,
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

    # All active tools in category (for related tool engine)
    all_category_tools = list(
        Tool.objects.filter(category=category, is_active=True)
        .exclude(id=tool.id)
        .order_by('order', 'name')
    )

    # Handle missing templates gracefully
    from django.template.loader import get_template, TemplateDoesNotExist
    actual_template = tool.template_name
    try:
        get_template(actual_template)
    except TemplateDoesNotExist:
        actual_template = 'tools/generic_tool.html'

    # ── Full metadata engine ──
    import json as _json
    from .utils.metadata import (
        build_software_application_schema,
        build_faq_schema,
        build_breadcrumb_schema,
        generate_meta_title,
        generate_meta_description,
        generate_intro_paragraph,
        generate_use_cases,
        generate_faq_items,
        get_related_tools,
    )

    # Smart related tools (topical clusters + tag similarity)
    related_tools = get_related_tools(tool, all_category_tools, limit=8)

    # SEO content generation
    seo_intro = generate_intro_paragraph(tool.name, tool.short_desc, category.name)
    seo_use_cases = generate_use_cases(tool.name, tool.tags or '')
    seo_faq_items = generate_faq_items(tool.name, tool.short_desc, category.name)

    # JSON-LD schemas
    tool_schema_dict = build_software_application_schema(tool, request)
    tool_schema = _json.dumps(tool_schema_dict)
    faq_schema = _json.dumps(build_faq_schema(seo_faq_items))
    breadcrumb_schema = _json.dumps(build_breadcrumb_schema(request, category, tool))

    # Canonical URL
    canonical = request.build_absolute_uri(tool.get_absolute_url())

    # Meta title/description — use stored values if set, else generate
    meta_title = tool.meta_title or generate_meta_title(tool.name, category.name)
    meta_desc = tool.meta_description or generate_meta_description(
        tool.name, tool.short_desc, category.name
    )

    return render(request, actual_template, {
        'tool': tool,
        'category': category,
        'is_bookmarked': is_bookmarked,
        'related_tools': related_tools,
        # SEO metadata
        'page_title': meta_title,
        'meta_description': meta_desc,
        'canonical_url': canonical,
        'og_type': 'website',
        # JSON-LD schemas
        'schema_json': tool_schema,
        'tool_schema': tool_schema,
        'faq_schema': faq_schema,
        'breadcrumb_schema': breadcrumb_schema,
        # SEO content for template
        'seo_intro': seo_intro,
        'seo_use_cases': seo_use_cases,
        'seo_faq_items': seo_faq_items,
    })


@require_GET
@rate_limit('search', limit=60, window=60)
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
    """Toggle bookmark for a tool. Auth required for DB persistence; guests use session (max 10)."""
    try:
        data = json.loads(request.body)
        tool_slug = data.get('tool_slug')
    except (json.JSONDecodeError, AttributeError):
        tool_slug = request.POST.get('tool_slug')

    if not tool_slug:
        return JsonResponse({'error': 'tool_slug required'}, status=400)

    # Authenticated: DB bookmarks
    if request.user.is_authenticated:
        tool = get_object_or_404(Tool, slug=tool_slug, is_active=True)
        bookmark, created = ToolBookmark.objects.get_or_create(user=request.user, tool=tool)
        if not created:
            bookmark.delete()
            cache.delete(f'bookmarks_{request.user.pk}')
            return JsonResponse({'bookmarked': False})

        cache.delete(f'bookmarks_{request.user.pk}')
        return JsonResponse({'bookmarked': True})

    # Guest: session-based bookmarks, max 10
    session_bookmarks = request.session.get('session_bookmarks', [])
    if tool_slug in session_bookmarks:
        session_bookmarks.remove(tool_slug)
        bookmarked = False
    elif len(session_bookmarks) >= 10:
        return JsonResponse({'error': 'Session bookmark limit reached (10). Sign in to save more.'}, status=400)
    else:
        session_bookmarks.append(tool_slug)
        bookmarked = True
    request.session['session_bookmarks'] = session_bookmarks
    request.session.modified = True
    return JsonResponse({'bookmarked': bookmarked})


@require_POST
def toggle_bookmark_auth(request):
    """DB bookmark toggle for authenticated users only."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=401)

    try:
        data = json.loads(request.body)
        tool_slug = data.get('tool_slug')
    except (json.JSONDecodeError, AttributeError):
        tool_slug = request.POST.get('tool_slug')

    if not tool_slug:
        return JsonResponse({'error': 'tool_slug required'}, status=400)

    tool = get_object_or_404(Tool, slug=tool_slug, is_active=True)
    bookmark, created = ToolBookmark.objects.get_or_create(user=request.user, tool=tool)
    if not created:
        bookmark.delete()
        # Invalidate cache
        from django.core.cache import cache
        cache.delete(f'bookmarks_{request.user.pk}')
        return JsonResponse({'bookmarked': False})

    from django.core.cache import cache
    cache.delete(f'bookmarks_{request.user.pk}')
    return JsonResponse({'bookmarked': True})


@require_POST
def record_usage(request):
    """Lightweight AJAX endpoint to increment tool usage_count."""
    try:
        data = json.loads(request.body)
        tool_slug = data.get('tool_slug')
    except (json.JSONDecodeError, AttributeError):
        tool_slug = request.POST.get('tool_slug')

    if not tool_slug:
        return JsonResponse({'ok': False, 'error': 'tool_slug required'}, status=400)

    Tool.objects.filter(slug=tool_slug, is_active=True).update(usage_count=F('usage_count') + 1)

    if request.user.is_authenticated:
        try:
            tool = Tool.objects.get(slug=tool_slug, is_active=True)
            ToolUsageHistory.objects.update_or_create(
                user=request.user,
                tool=tool,
                defaults={},
            )
        except Tool.DoesNotExist:
            pass

    return JsonResponse({'ok': True})


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
