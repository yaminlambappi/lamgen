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

from apps.seo.models import LongTailVariant
from apps.tools.data.elite_content import ELITE_TOOL_DATA
from .utils.rate_limit import rate_limit
from config.games import GAMES_CONFIG
import json
import logging

logger = logging.getLogger(__name__)


@cache_control(public=True, max_age=60)
def new_homepage_view(request):
    """The new, redesigned homepage."""
    import json
    from config.homepage_data import (
        HERO_CHIPS,
        AI_TOOLS,
        BROWSER_UTILITIES,
        CATEGORIES,
        TRENDING_TOOLS,
        FAQS,
        FOOTER_DATA
    )

    def get_item_list_schema(tool_list, list_name):
        elements = []
        position = 1
        for category in tool_list:
            for tool in category.get("tools", []):
                elements.append({
                    "@type": "ListItem",
                    "position": position,
                    "item": {
                        "@type": "SoftwareApplication",
                        "name": tool["name"],
                        "url": request.build_absolute_uri(tool["route"]),
                        "description": tool.get("description", ""),
                    }
                })
                position += 1

        return {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": list_name,
            "itemListElement": elements
        }

    ai_tools_schema = get_item_list_schema(AI_TOOLS, "AI Tools")
    browser_utilities_schema = get_item_list_schema(BROWSER_UTILITIES, "Browser Utilities")

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"],
                }
            } for faq in FAQS
        ]
    }

    from django.db.models import Count, Q
    from apps.tools.models import ToolCategory

    # Recalculate tools count logic from actual dataset source
    db_categories = ToolCategory.objects.filter(is_active=True).annotate(
        computed_tool_count=Count('tools', filter=Q(tools__is_active=True))
    ).order_by('order', 'name')

    dynamic_categories = []
    for cat in db_categories:
        dynamic_categories.append({
            'name': cat.name,
            'slug': cat.slug,
            'icon': cat.icon.replace('bi-', '') if cat.icon.startswith('bi-') else cat.icon,
            'tool_count': cat.computed_tool_count,
            'description': cat.short_desc or cat.description,
            'route': cat.get_absolute_url(),
        })

    from django.db.models import Sum
    from apps.tools.models import Tool
    
    ai_tools_count = Tool.objects.filter(is_active=True, is_ai_powered=True).count()
    utilities_count = Tool.objects.filter(is_active=True, is_ai_powered=False).count()
    categories_count = db_categories.count()
    
    usage_stats = Tool.objects.filter(is_active=True).aggregate(
        total_views=Sum('view_count'),
        total_usage=Sum('usage_count')
    )
    total_users = (usage_stats['total_views'] or 0) + (usage_stats['total_usage'] or 0)
    # Provide a realistic baseline if the DB is freshly seeded
    total_users = max(10000, total_users)
    
    if total_users >= 1000000:
        users_helped_formatted = f"{total_users // 1000000}m+"
    elif total_users >= 1000:
        users_helped_formatted = f"{total_users // 1000}k+"
    else:
        users_helped_formatted = f"{total_users}+"

    dynamic_stats = {
        'ai_tools': f"{ai_tools_count}+" if ai_tools_count > 0 else "30+",
        'utilities': f"{utilities_count}+" if utilities_count > 0 else "15+",
        'categories': categories_count if categories_count > 0 else 8,
        'users_helped': users_helped_formatted
    }

    context = {
        "hero_chips": HERO_CHIPS,
        "ai_tools_categories": AI_TOOLS,
        "browser_utilities_categories": BROWSER_UTILITIES,
        "categories": dynamic_categories,
        "dynamic_stats": dynamic_stats,
        "trending_tools": TRENDING_TOOLS,
        "faqs": FAQS,
        "footer_data": FOOTER_DATA,
        "ai_tools_schema": json.dumps(ai_tools_schema),
        "browser_utilities_schema": json.dumps(browser_utilities_schema),
        "faq_schema": json.dumps(faq_schema),
        "page_title": "LamGen: Your AI Productivity Ecosystem",
        "meta_description": "Discover powerful AI tools for career, content, development, productivity, and growth — all in one place.",
        "canonical_url": request.build_absolute_uri("/"),
    }
    return render(request, "pages/home_new.html", context)


@cache_control(public=True, max_age=60)
def index(request):
    """All tools homepage — categorized grid."""
    from django.db.models import Prefetch
    categories = ToolCategory.objects.filter(is_active=True).prefetch_related(
        Prefetch("tools", queryset=Tool.objects.filter(is_active=True))
    )
    featured_tools = Tool.objects.filter(is_active=True, is_featured=True).select_related("category")[:8]
    new_tools = Tool.objects.filter(is_active=True, is_new=True).select_related("category")[:6]
    trending = Tool.objects.filter(is_active=True).order_by("-created_at").select_related("category")[:8]
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
    from django.template.loader import get_template, TemplateDoesNotExist

    # Build the set of template names that actually exist on disk so we can
    # exclude placeholder tools from the hub grid (they'd just show the
    # fallback screen when clicked, which is a dead end for users).
    all_active = Tool.objects.filter(is_active=True).values_list('template_name', flat=True).distinct()
    live_templates = set()
    for tmpl in all_active:
        try:
            get_template(tmpl)
            live_templates.add(tmpl)
        except TemplateDoesNotExist:
            pass

    live_tools_qs = Tool.objects.filter(
        is_active=True, template_name__in=live_templates
    ).select_related('category')

    categories = (
        ToolCategory.objects.filter(is_active=True)
        .prefetch_related(Prefetch("tools", queryset=live_tools_qs))
        .order_by("order", "name")
    )

    # Recent tools from session
    recent_slugs = request.session.get("recent_tools", [])
    recent_tools = list(Tool.objects.filter(slug__in=recent_slugs, is_active=True,
                                            template_name__in=live_templates).select_related("category"))
    slug_order = {s: i for i, s in enumerate(recent_slugs)}
    recent_tools.sort(key=lambda t: slug_order.get(t.slug, 999))

    trending = (Tool.objects.filter(is_active=True, template_name__in=live_templates)
                .order_by("-view_count", "-created_at").select_related("category")[:8])
    new_tools = (Tool.objects.filter(is_active=True, is_new=True, template_name__in=live_templates)
                 .select_related("category")[:6])

    live_tool_count = live_tools_qs.count()
    approx_tools = max(live_tool_count, 1)

    return render(
        request,
        "tools/workspaces.html",
        {
            "categories": categories,
            "recent_tools": recent_tools[:5],
            "trending": trending,
            "new_tools": new_tools,
            "page_title": "All Tools — LamGen",
            "meta_description": (f"Browse {approx_tools}+ free online tools. Developer tools, writing tools, image tools, "
                                  "SEO tools and more."),
            "canonical_url": request.build_absolute_uri("/tools/"),
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
    trending = sorted(tools, key=lambda t: t.created_at, reverse=True)[:6]
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
        pass

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

    # Validate template exists — show fallback for tools not yet implemented
    from django.template.loader import get_template, TemplateDoesNotExist

    actual_template = tool.template_name
    try:
        get_template(actual_template)
    except TemplateDoesNotExist:
        # tool_fallback.html is the proper "coming soon" page for unimplemented tools
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
        # Persist generated SEO content so it's only generated once
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

    # OG image — use dynamic generated image, fallback to custom or default
    if tool.og_image:
        og_image_url = request.build_absolute_uri(tool.og_image)
    else:
        og_image_url = request.build_absolute_uri(
            f"/og-image/{category.slug}/{tool.slug}.png"
        )

    # Meta title/description — use stored values if set, else generate
    meta_title = tool.meta_title or generate_meta_title(tool.name, category.name)
    meta_desc = tool.meta_description or generate_meta_description(tool.name, tool.short_desc, category.name)

    # ── AI Tool enrichment ──
    # DB Tool objects don't carry input_fields — fetch them from the AI registry
    # so that ai_tools/detail.html can render the form correctly.
    if tool.is_ai_powered:
        try:
            from apps.ai_tools.registry import get_tool as _get_ai_tool
            _ai_reg = _get_ai_tool(tool.slug)
            if _ai_reg:
                tool.input_fields = _ai_reg.get('input_fields', [])
                tool.response_format = _ai_reg.get('response_format', 'text')
            else:
                tool.input_fields = getattr(tool, 'input_fields', [])
                tool.response_format = getattr(tool, 'response_format', 'text')
        except Exception:
            tool.input_fields = []
            tool.response_format = 'text'

    # ── Journey context ──
    journey_contexts = []
    try:
        from config.journeys import get_journeys_for_tool
        journey_contexts = get_journeys_for_tool(tool.slug)
    except Exception:
        journey_contexts = []

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
            "og_image_url": og_image_url,
            "schema_json": tool_schema,
            "tool_schema": tool_schema,
            "faq_schema": faq_schema,
            "breadcrumb_schema": breadcrumb_schema,
            # SEO content for template
            "seo_intro": seo_intro,
            "seo_use_cases": seo_use_cases,
            "seo_faq_items": seo_faq_items,
            "tool_template": tool.template_name,
            # Journey context
            "journey_contexts": journey_contexts,
            "primary_journey": journey_contexts[0] if journey_contexts else None,
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

    from django.template.loader import get_template, TemplateDoesNotExist

    actual_template = tool.template_name
    try:
        get_template(actual_template)
    except TemplateDoesNotExist:
        actual_template = "tools/tool_redirect.html"

    return render(
        request,
        actual_template,
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
            "tool_template": tool.template_name,
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
    tools = Tool.objects.filter(is_active=True).order_by("-created_at").select_related("category")[:30]
    return render(
        request,
        "tools/trending.html",
        {
            "tools": tools,
            "page_title": "Trending Tools — LamGen",
            "meta_description": "Most popular free online tools on LamGen. See what others are using right now.",
            "canonical_url": request.build_absolute_uri("/tools/trending/"),
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


# --- Unified Tool Counts API ---
@cache_control(public=True, max_age=300)
@require_GET
def tool_counts_api(request):
    """Unified tool counts \u2014 derived from DB which mirrors registry state.
    Returns total, ai_tools, utility_tools, and per-category breakdown.
    """
    from django.db.models import Count, Q

    cats = (
        ToolCategory.objects.filter(is_active=True)
        .annotate(
            total=Count('tools', filter=Q(tools__is_active=True)),
            ai_count=Count('tools', filter=Q(tools__is_active=True, tools__is_ai_powered=True)),
        )
        .values('slug', 'name', 'icon', 'total', 'ai_count')
        .order_by('order', 'name')
    )

    categories = list(cats)
    total_tools = sum(c['total'] for c in categories)
    total_ai = sum(c['ai_count'] for c in categories)
    total_utility = total_tools - total_ai

    return JsonResponse({
        'total': total_tools,
        'ai_tools': total_ai,
        'utility_tools': total_utility,
        'categories': categories,
    })


# --- New Dynamic Routing Views ---
from django.shortcuts import redirect
from apps.ai_tools.registry import get_tool, get_all_tools

@cache_control(public=True, max_age=60)
def dynamic_tool_view(request, category_slug, tool_slug):
    """Dynamic tool view relying on registry and db fallback."""
    # 1. Check AI Tool Registry — category_slug is ignored so single-slug
    #    URLs (/tools/<slug>/) always resolve correctly regardless of the
    #    category stored in the registry vs the DB.
    ai_tool = get_tool(tool_slug)
    if ai_tool:
        # Prefer the DB record so we get the real ToolCategory object
        # (needed for tool_base.html colour variables, etc.)
        db_tool = Tool.objects.filter(slug=tool_slug, is_active=True).select_related('category').first()
        if db_tool:
            return tool_view(request, db_tool.category.slug, tool_slug)

        # No DB record yet — build a lightweight mock so the template renders.
        # Resolve category with 3-level fallback to guarantee a non-None value.
        reg_cat_slug = ai_tool.get("category", None)
        category = None
        # 1. Try AI registry category slug (e.g. "writing" → DB slug "writing-tools")
        if reg_cat_slug:
            category = ToolCategory.objects.filter(slug=reg_cat_slug, is_active=True).first()
        # 2. Try URL-provided category_slug (e.g. "writing-tools" from the URL)
        if not category and category_slug:
            category = ToolCategory.objects.filter(slug=category_slug, is_active=True).first()
        # 3. Last resort: first active category in DB
        if not category:
            category = ToolCategory.objects.filter(is_active=True).order_by('order').first()

        class MockTool:
            def __init__(self, data, cat):
                self.name = data["name"]
                self.slug = data["slug"]
                self.icon = data.get("icon", "bi-stars")
                self.short_desc = data.get("description", "AI Powered Tool")
                self.description = self.short_desc
                self.is_ai_powered = True
                self.category = cat
                self.input_fields = data.get("input_fields", [])
                self.response_format = data.get("response_format", "text")
            def get_absolute_url(self):
                return f"/tools/{self.slug}/"

        mock_tool = MockTool(ai_tool, category)
        return render(request, "ai_tools/detail.html", {
            "tool": mock_tool,
            "category": category,
            "raw_tool": ai_tool,
            "page_title": f"{ai_tool['name']} - LamGen",
            "meta_description": ai_tool.get("system_prompt", "")[:150],
        })

    # 2. Fallback to DB Tool — match by slug only (category_slug is advisory / may be None)
    tool = Tool.objects.filter(slug=tool_slug, is_active=True).select_related('category').first()
    if not tool and category_slug:
        tool = Tool.objects.filter(
            slug=tool_slug, category__slug=category_slug, is_active=True
        ).select_related('category').first()
    if not tool:
        return render(request, 'tools/tool_fallback.html', {'slug': tool_slug}, status=404)
    return tool_view(request, tool.category.slug, tool_slug)

def category_or_tool_dispatcher(request, category_slug=None, tool_slug=None):
    """Dispatcher to handle overlapping category and tool slugs."""
    slug = category_slug or tool_slug
    if ToolCategory.objects.filter(slug=slug, is_active=True).exists():
        return category_view(request, slug)
    # It's a tool slug — resolve via dynamic_tool_view with no assumed category
    return dynamic_tool_view(request, None, slug)

def tool_redirect_view(request, category_slug, tool_slug):
    """Redirect old /category/tool/ paths to /tool/ OR render the new dynamic AI view."""
    # We now serve AI tools at /tools/<category>/<slug>/ directly!
    return dynamic_tool_view(request, category_slug, tool_slug)

def longtail_redirect_view(request, category_slug, tool_slug, variant_slug):
    """Redirect old longtail paths."""
    return redirect('tools:tool', tool_slug=tool_slug, permanent=True)
