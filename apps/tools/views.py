from io import BytesIO
from pathlib import Path
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import cache_page, cache_control
from django.db.models import Q, F
from django.core.cache import cache
from django.conf import settings
from .models import Tool, ToolCategory, ToolBookmark, ToolUsageHistory
from apps.tools.services.internal_linking import internal_linking_engine
from apps.tools.services.islamic_panel import PrayerTimesService
from apps.seo.models import LongTailVariant
from apps.tools.data.elite_content import ELITE_TOOL_DATA
from .utils.rate_limit import rate_limit
from config.games import GAMES_CONFIG
import json
import logging

logger = logging.getLogger(__name__)


@cache_control(public=True, max_age=60)
def index(request):
    """All tools homepage — categorized grid."""
    from django.db.models import Prefetch
    categories = ToolCategory.objects.filter(is_active=True).prefetch_related(
        Prefetch("tools", queryset=Tool.objects.filter(is_active=True))
    )
    featured_tools = Tool.objects.filter(is_active=True, is_featured=True).select_related("category")[:8]
    new_tools = Tool.objects.filter(is_active=True, is_new=True).select_related("category")[:6]
    trending = Tool.objects.filter(is_active=True).order_by("-view_count").select_related("category")[:8]
    most_used = Tool.objects.filter(is_active=True).order_by("-usage_count").select_related("category")[:8]

    recent_slugs = request.session.get("recent_tools", [])
    recent_tools = list(Tool.objects.filter(slug__in=recent_slugs, is_active=True).select_related("category"))
    slug_order = {s: i for i, s in enumerate(recent_slugs)}
    recent_tools.sort(key=lambda t: slug_order.get(t.slug, 999))

    bookmarked_slugs = []
    if request.user.is_authenticated:
        bookmarked_slugs = list(
            ToolBookmark.objects.filter(user=request.user).values_list("tool__slug", flat=True)
        )

    import json as _json
    from .utils.metadata import build_website_schema, build_organization_schema

    website_schema = _json.dumps(build_website_schema(request))
    org_schema = _json.dumps(build_organization_schema(request))

    active_tool_count = Tool.objects.filter(is_active=True).count()
    approx_tools = max(active_tool_count, 1)

    return render(
        request,
        "tools/index.html",
        {
            "categories": categories,
            "featured_tools": featured_tools,
            "new_tools": new_tools,
            "trending": trending,
            "most_used": most_used,
            "recent_tools": recent_tools[:5],
            "bookmarked_slugs": bookmarked_slugs,
            "page_title": f"LamGen — {approx_tools}+ Free Online Tools for Developers, Students & Writers",
            "meta_description": (
                f"Free online tools for developers, students, writers and professionals. {approx_tools}+ tools "
                "including JSON formatter, image compressor, word counter, GPA calculator and more. "
                "No signup, no ads, 100% private."
            ),
            "canonical_url": request.build_absolute_uri("/"),
            "schema_json": website_schema,
            "org_schema": org_schema,
        },
    )


@cache_control(public=True, max_age=60)
def tools_index_view(request):
    """All tools ecosystem explorer — dense launcher grid."""
    from django.db.models import Prefetch

    categories = (
        ToolCategory.objects.filter(is_active=True)
        .prefetch_related(Prefetch("tools", queryset=Tool.objects.filter(is_active=True)))
        .order_by("order", "name")
    )

    # Recent tools from session
    recent_slugs = request.session.get("recent_tools", [])
    recent_tools = list(Tool.objects.filter(slug__in=recent_slugs, is_active=True).select_related("category"))
    slug_order = {s: i for i, s in enumerate(recent_slugs)}
    recent_tools.sort(key=lambda t: slug_order.get(t.slug, 999))

    trending = Tool.objects.filter(is_active=True).order_by("-view_count").select_related("category")[:8]
    new_tools = Tool.objects.filter(is_active=True, is_new=True).select_related("category")[:6]

    active_tool_count = Tool.objects.filter(is_active=True).count()
    approx_tools = max(active_tool_count, 1)

    return render(
        request,
        "tools/workspaces.html",
        {
            "categories": categories,
            "recent_tools": recent_tools[:5],
            "trending": trending,
            "new_tools": new_tools,
            "page_title": "All Tools — LamGen",
            "meta_description": (f"Browse {approx_tools}+ free online tools. Developer tools, writing tools, image tools, " "SEO tools and more."),
        },
    )


@cache_control(public=True, max_age=600)
def category_view(request, category_slug):
    """Category listing page — SEO landing hub."""
    category = get_object_or_404(ToolCategory, slug=category_slug, is_active=True)
    tools = list(Tool.objects.filter(category=category, is_active=True).select_related("category").order_by("order", "name"))

    bookmarked_slugs = []
    if request.user.is_authenticated:
        bookmarked_slugs = list(ToolBookmark.objects.filter(user=request.user, tool__category=category).values_list("tool__slug", flat=True))

    # Group tools dynamically
    tool_groups = {}
    for tool in tools:
        group_name = "Other Utilities"
        if tool.tags:
            group_name = tool.tags.split(",")[0].strip().title()
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
    meta_title = f"{cat_name} — {tool_count} Free Online Tools | LamGen"[:70]
    meta_desc = (
        category.description[:157] + "..."
        if category.description and len(category.description) > 160
        else category.description or f"Free {cat_name.lower()} online. {tool_count} tools — no download, no signup, instant results."
    )

    breadcrumb_schema = _json.dumps(build_breadcrumb_schema(request, category))
    category_schema = _json.dumps(build_category_schema(category, tools, request))

    # Featured and trending tools for the landing hub
    featured = [t for t in tools if t.is_featured][:4]
    trending = sorted(tools, key=lambda t: -t.view_count)[:6]
    newest = [t for t in tools if t.is_new][:4]

    return render(
        request,
        "tools/category.html",
        {
            "category": category,
            "tools": tools,
            "tool_groups": sorted_groups,
            "bookmarked_slugs": bookmarked_slugs,
            "featured_tools": featured,
            "trending_tools": trending,
            "newest_tools": newest,
            "tool_count": tool_count,
            "page_title": meta_title,
            "meta_description": meta_desc,
            "canonical_url": request.build_absolute_uri(category.get_absolute_url()),
            "schema_json": category_schema,
            "breadcrumb_schema": breadcrumb_schema,
        },
    )


@cache_control(public=True, max_age=60)
def tool_view(request, category_slug, tool_slug):
    """Individual tool page renderer."""
    category = get_object_or_404(ToolCategory, slug=category_slug, is_active=True)
    tool = get_object_or_404(Tool, slug=tool_slug, category=category, is_active=True)

    # Increment view count (cached counter to reduce DB writes)
    cache_key = f"tool_views_{tool.pk}"
    views = cache.get(cache_key, 0)
    views += 1
    cache.set(cache_key, views, 60 * 5)
    if views % 10 == 0:
        Tool.objects.filter(pk=tool.pk).update(view_count=F("view_count") + 1)

    # Track in session
    recent = request.session.get("recent_tools", [])
    if tool.slug in recent:
        recent.remove(tool.slug)
    recent.insert(0, tool.slug)
    request.session["recent_tools"] = recent[:10]
    request.session.modified = True

    # Track in DB (for logged-in users) - UNIQUE entries per tool
    if request.user.is_authenticated:
        ToolUsageHistory.objects.update_or_create(user=request.user, tool=tool, defaults={})  # auto_now=True on used_at handles the timestamp

    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = ToolBookmark.objects.filter(user=request.user, tool=tool).exists()

    # All active tools in category (for related tool engine)
    all_category_tools = list(Tool.objects.filter(category=category, is_active=True).exclude(id=tool.id).order_by("order", "name"))

    # Handle missing templates gracefully
    from django.template.loader import get_template, TemplateDoesNotExist

    actual_template = tool.template_name
    try:
        get_template(actual_template)
    except TemplateDoesNotExist:
        actual_template = "tools/tool_fallback.html"

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

    # Get related tools
    all_category_tools = list(Tool.objects.filter(category=category, is_active=True).exclude(id=tool.id).order_by("order", "name"))
    related_tools = get_related_tools(tool, all_category_tools)
    # Get enhanced internal links with safe fallback
    try:
        internal_links = internal_linking_engine.get_tool_internal_links(tool, "tool_page")
    except Exception as e:
        logger.error(f"Error getting internal links for tool {tool.slug}: {e}")
        internal_links = []

    # Use stored SEO content if present; otherwise generate and save
    if not tool.seo_intro:
        tool.seo_intro = generate_intro_paragraph(tool.name, tool.short_desc, category.name)
        tool.use_cases = generate_use_cases(tool.name, tool.tags or "")
        tool.faq_items = generate_faq_items(tool.name, tool.short_desc, category.name)
        # Save async via Celery to avoid blocking response, or sync for now
        from django.conf import settings

        if not settings.DEBUG:
            from .tasks import update_tool_seo_content

            update_tool_seo_content.delay(tool.pk)
        else:
            Tool.objects.filter(pk=tool.pk).update(
                seo_intro=tool.seo_intro,
                use_cases=tool.use_cases,
                faq_items=tool.faq_items,
            )

    seo_intro = tool.seo_intro
    seo_use_cases = tool.use_cases or generate_use_cases(tool.name, tool.tags or "")
    seo_faq_items = tool.faq_items or generate_faq_items(tool.name, tool.short_desc, category.name)

    # JSON-LD schemas
    tool_schema_dict = build_software_application_schema(tool, request)
    tool_schema = _json.dumps(tool_schema_dict)
    faq_schema = _json.dumps(build_faq_schema(seo_faq_items))
    breadcrumb_schema = _json.dumps(build_breadcrumb_schema(request, category, tool))

    # Canonical URL
    canonical = request.build_absolute_uri(tool.get_absolute_url())

    # Meta title/description — use stored values if set, else generate
    meta_title = tool.meta_title or generate_meta_title(tool.name, category.name)
    meta_desc = tool.meta_description or generate_meta_description(tool.name, tool.short_desc, category.name)

    return render(
        request,
        actual_template,
        {
            "tool": tool,
            "category": category,
            "elite": ELITE_TOOL_DATA.get(tool.slug, {}),
            "is_bookmarked": is_bookmarked,
            "related_tools": related_tools,
            "internal_links": internal_links,
            "page_title": meta_title,
            "meta_description": meta_desc,
            "canonical_url": canonical,
            "schema_json": tool_schema,
            "tool_schema": tool_schema,
            "faq_schema": faq_schema,
            "breadcrumb_schema": breadcrumb_schema,
            # SEO content for template
            "seo_intro": seo_intro,
            "seo_use_cases": seo_use_cases,
            "seo_faq_items": seo_faq_items,
        },
    )


def longtail_view(request, category_slug, tool_slug, variant_slug):
    category = get_object_or_404(ToolCategory, slug=category_slug, is_active=True)
    tool = get_object_or_404(Tool, slug=tool_slug, category=category, is_active=True)
    variant = get_object_or_404(
        LongTailVariant,
        tool=tool,
        variant_slug=variant_slug,
        is_active=True,
    )

    import json as _json
    from .utils.metadata import (
        build_software_application_schema,
        build_faq_schema,
        build_breadcrumb_schema,
        generate_use_cases,
        generate_faq_items,
        get_related_tools,
    )

    # Get enhanced internal links using smart linking engine
    try:
        internal_links = internal_linking_engine.get_tool_internal_links(tool, "tool_page")
    except Exception as e:
        logger.error(f"Error getting internal links for tool {tool.slug} (longtail): {e}")
        internal_links = []

    # Related tools — always computed regardless of internal_links
    all_category_tools = list(Tool.objects.filter(category=category, is_active=True).exclude(id=tool.id).order_by("order", "name"))
    related_tools = get_related_tools(tool, all_category_tools)

    # Use stored SEO content from variant, fallback to generated
    seo_intro = variant.unique_intro
    seo_use_cases = variant.use_cases or generate_use_cases(tool.name, tool.tags or "")
    seo_faq_items = variant.faq_items or generate_faq_items(tool.name, tool.short_desc, category.name)

    # JSON-LD schemas
    tool_schema = _json.dumps(build_software_application_schema(tool, request))
    faq_schema = _json.dumps(build_faq_schema(seo_faq_items))
    breadcrumb_schema = _json.dumps(build_breadcrumb_schema(request, category, tool))

    # SELF-REFERENTIAL CANONICAL: Each longtail page indexes independently
    canonical = request.build_absolute_uri(variant.get_absolute_url())

    return render(
        request,
        tool.template_name,
        {
            "tool": tool,
            "category": category,
            "variant": variant,
            "elite": ELITE_TOOL_DATA.get(tool.slug, {}),
            "related_tools": related_tools,
            "internal_links": internal_links,
            "page_title": variant.meta_title,
            "meta_description": variant.meta_description,
            "canonical_url": canonical,
            "schema_json": tool_schema,
            "tool_schema": tool_schema,
            "faq_schema": faq_schema,
            "breadcrumb_schema": breadcrumb_schema,
            "seo_intro": seo_intro,
            "seo_use_cases": seo_use_cases,
            "seo_faq_items": seo_faq_items,
        },
    )


@cache_control(public=True, max_age=3600)
def embed_view(request, category_slug, tool_slug):
    category = get_object_or_404(ToolCategory, slug=category_slug, is_active=True)
    tool = get_object_or_404(Tool, slug=tool_slug, category=category, is_active=True)
    response = render(
        request,
        "tools/embed.html",
        {
            "tool": tool,
            "category": category,
            "page_title": f"{tool.name} Embed — LamGen",
            "meta_description": tool.short_desc,
            "canonical_url": request.build_absolute_uri(tool.get_absolute_url()),
        },
    )
    response["X-Frame-Options"] = "ALLOWALL"
    return response


@cache_control(public=True, max_age=86400)
def og_image_view(request, category_slug, tool_slug):
    tool = get_object_or_404(
        Tool,
        slug=tool_slug,
        category__slug=category_slug,
        is_active=True,
    )
    cache_path = Path(settings.MEDIA_ROOT) / "og" / category_slug / f"{tool_slug}.png"
    if cache_path.exists():
        return FileResponse(open(cache_path, "rb"), content_type="image/png")
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (1200, 630), (7, 9, 26))
        draw = ImageDraw.Draw(img)
        title_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
        draw.rectangle((0, 0, 1200, 630), fill=(8, 10, 28))
        draw.text((70, 120), tool.name[:60], fill=(240, 245, 255), font=title_font)
        draw.text((70, 200), tool.short_desc[:90], fill=(190, 198, 230), font=brand_font)
        draw.text((70, 540), "LamGen", fill=(122, 111, 255), font=brand_font)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(cache_path, "PNG")
        buf = BytesIO()
        img.save(buf, "PNG")
        buf.seek(0)
        return HttpResponse(buf.getvalue(), content_type="image/png")
    except Exception as e:
        logger.error(f"Error generating OG image for tool {tool_slug}: {e}")
        fallback = Path(settings.BASE_DIR) / "static" / "img" / "og-default.png"
        if fallback.exists():
            return FileResponse(open(fallback, "rb"), content_type="image/png")
        return HttpResponse(status=404)


@require_GET
@rate_limit("search", limit=60, window=60)
def search_view(request):
    """AJAX tool search endpoint."""
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    # Natural Language Intent Mapping
    q_clean = q.lower().replace("i want to ", "").replace("how to ", "").replace("show me ", "").replace("can you ", "")

    # Keyword expansions for common intents
    intent_map = {
        "convert": ["converter", "transform", "to"],
        "format": ["formatter", "beautify", "clean"],
        "validate": ["validator", "checker", "verify"],
        "make": ["generator", "create", "builder"],
    }

    words = q_clean.split()
    query = Q(name__icontains=q_clean) | Q(short_desc__icontains=q_clean) | Q(tags__icontains=q_clean)

    for word in words:
        if word in intent_map:
            for expansion in intent_map[word]:
                query |= Q(name__icontains=expansion) | Q(tags__icontains=expansion)
        query |= Q(name__icontains=word) | Q(tags__icontains=word)

    tools = list(Tool.objects.filter(query, is_active=True).select_related("category").distinct())

    # Calculate relevance score for sorting
    for t in tools:
        score = 0
        t_name = t.name.lower()
        t_desc = (t.short_desc or "").lower()
        t_tags = (t.tags or "").lower()

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
        results.append(
            {
                "name": t.name,
                "short_desc": t.short_desc,
                "icon": t.icon,
                "url": t.get_absolute_url(),
                "category": t.category.name,
                "category_color_from": t.category.color_from,
            }
        )

    return JsonResponse({"results": results})


@require_GET
@cache_control(private=True, max_age=300)
def islamic_panel_api(request):
    """Location-aware prayer snapshot for the global Islamic utility strip."""
    latitude = request.GET.get("lat")
    longitude = request.GET.get("lon")
    try:
        snapshot = PrayerTimesService.get_snapshot(latitude=latitude, longitude=longitude)
        return JsonResponse(snapshot)
    except Exception as e:
        logger.error(f"Error getting Islamic panel data: {e}")
        fallback_snapshot = PrayerTimesService._build_placeholder_snapshot(
            PrayerTimesService.DEFAULT_LOCATION["latitude"], PrayerTimesService.DEFAULT_LOCATION["longitude"], fallback_label=PrayerTimesService.DEFAULT_LOCATION["label"]
        )
        return JsonResponse(fallback_snapshot)


@require_POST
@rate_limit('toggle_bookmark', limit=100, window=60)
def toggle_bookmark(request):
    """Toggle bookmark for a tool. Auth required for DB persistence; guests use session (max 10)."""
    try:
        data = json.loads(request.body)
        tool_slug = data.get("tool_slug")
    except (json.JSONDecodeError, AttributeError):
        tool_slug = request.POST.get("tool_slug")

    if not tool_slug:
        return JsonResponse({"error": "tool_slug required"}, status=400)

    # Authenticated: DB bookmarks
    if request.user.is_authenticated:
        tool = get_object_or_404(Tool, slug=tool_slug, is_active=True)
        bookmark, created = ToolBookmark.objects.get_or_create(user=request.user, tool=tool)
        if not created:
            bookmark.delete()
            cache.delete(f"bookmarks_{request.user.pk}")
            return JsonResponse({"bookmarked": False})

        cache.delete(f"bookmarks_{request.user.pk}")
        return JsonResponse({"bookmarked": True})

    # Guest: session-based bookmarks, max 10
    session_bookmarks = request.session.get("session_bookmarks", [])
    if tool_slug in session_bookmarks:
        session_bookmarks.remove(tool_slug)
        bookmarked = False
    elif len(session_bookmarks) >= 10:
        return JsonResponse({"error": "Session bookmark limit reached (10). Sign in to save more."}, status=400)
    else:
        session_bookmarks.append(tool_slug)
        bookmarked = True
    request.session["session_bookmarks"] = session_bookmarks
    request.session.modified = True
    return JsonResponse({"bookmarked": bookmarked})


@require_POST
@rate_limit('toggle_bookmark_auth', limit=100, window=60)
def toggle_bookmark_auth(request):
    """DB bookmark toggle for authenticated users only."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    try:
        data = json.loads(request.body)
        tool_slug = data.get("tool_slug")
    except (json.JSONDecodeError, AttributeError):
        tool_slug = request.POST.get("tool_slug")

    if not tool_slug:
        return JsonResponse({"error": "tool_slug required"}, status=400)

    tool = get_object_or_404(Tool, slug=tool_slug, is_active=True)
    bookmark, created = ToolBookmark.objects.get_or_create(user=request.user, tool=tool)
    if not created:
        bookmark.delete()
        # Invalidate cache
        from django.core.cache import cache

        cache.delete(f"bookmarks_{request.user.pk}")
        return JsonResponse({"bookmarked": False})

    from django.core.cache import cache

    cache.delete(f"bookmarks_{request.user.pk}")
    return JsonResponse({"bookmarked": True})


@require_POST
@rate_limit('record_usage', limit=100, window=60)
def record_usage(request):
    """Lightweight AJAX endpoint to increment tool usage_count."""
    try:
        data = json.loads(request.body)
        tool_slug = data.get("tool_slug")
    except (json.JSONDecodeError, AttributeError):
        tool_slug = request.POST.get("tool_slug")

    if not tool_slug:
        return JsonResponse({"ok": False, "error": "tool_slug required"}, status=400)

    Tool.objects.filter(slug=tool_slug, is_active=True).update(usage_count=F("usage_count") + 1)

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

    return JsonResponse({"ok": True})


@cache_control(public=True, max_age=3600)
@cache_page(60 * 60)
@require_GET
def trending_view(request):
    """Trending tools page."""
    tools = Tool.objects.filter(is_active=True).order_by("-view_count").select_related("category")[:30]
    return render(
        request,
        "tools/trending.html",
        {
            "tools": tools,
            "page_title": "Trending Tools — LamGen",
            "meta_description": "Most popular free online tools on LamGen. See what others are using right now.",
        },
    )


@cache_control(public=True, max_age=300)  # 5 minutes cache
def games_data_api(request):
    """API endpoint to provide games data as JSON"""
    try:
        # Return the static games configuration
        return JsonResponse(GAMES_CONFIG, safe=False)
    except Exception as e:
        logger.error(f"Error getting games data: {e}")
        return JsonResponse({"error": str(e)}, status=500)



