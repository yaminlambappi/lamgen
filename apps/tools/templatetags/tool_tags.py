"""Template tags and filters for the LamGen Tools Ecosystem."""
import json
from django import template
from apps.tools.utils.metadata import (
    build_software_application_schema,
    build_faq_schema,
    build_item_list_schema,
)

register = template.Library()


# ── Gradient / styling helpers ──────────────────────────────────────────────

@register.simple_tag
def tool_gradient(category):
    return f'linear-gradient(135deg, {category.color_from}, {category.color_to})'


@register.simple_tag
def tool_icon_bg(category):
    return (
        f'background: linear-gradient(135deg, {category.color_from}22, {category.color_to}22);'
        f' border: 1px solid {category.color_from}44;'
    )


# ── Bookmark filter ──────────────────────────────────────────────────────────

@register.filter
def is_bookmarked(tool_slug, bookmarked_slugs):
    """Usage: {{ tool.slug|is_bookmarked:bookmarked_slugs }}"""
    return tool_slug in (bookmarked_slugs or [])


# ── JSON-LD schema tags ──────────────────────────────────────────────────────

@register.simple_tag(takes_context=True)
def software_application_schema(context, tool):
    """Render JSON-LD SoftwareApplication schema for a Tool page."""
    request = context.get('request')
    if not request:
        return ''
    schema = build_software_application_schema(tool, request)
    return json.dumps(schema, ensure_ascii=False)


@register.simple_tag
def faq_schema(items):
    """Render JSON-LD FAQPage schema from a list of {q, a} dicts."""
    schema = build_faq_schema(items)
    return json.dumps(schema, ensure_ascii=False)


@register.simple_tag(takes_context=True)
def item_list_schema(context, page):
    """Render JSON-LD ItemList schema for an SEOPage."""
    request = context.get('request')
    if not request:
        return ''
    schema = build_item_list_schema(page, request)
    return json.dumps(schema, ensure_ascii=False)


# ── Breadcrumb helper ────────────────────────────────────────────────────────

@register.inclusion_tag('partials/breadcrumb.html')
def breadcrumb(*crumbs):
    """
    Usage: {% breadcrumb "Home" "/" "Developer Tools" "/tools/developer-tools/" "JSON Formatter" %}
    Pass alternating label/url pairs; last item has no URL (current page).
    """
    items = []
    crumb_list = list(crumbs)
    i = 0
    while i < len(crumb_list):
        label = crumb_list[i]
        url = crumb_list[i + 1] if i + 1 < len(crumb_list) else None
        # If next item looks like a label (no leading /), treat current as leaf
        if url and not str(url).startswith('/') and not str(url).startswith('http'):
            items.append({'label': label, 'url': None})
            i += 1
        else:
            items.append({'label': label, 'url': url})
            i += 2
    return {'crumbs': items}


# ── Ad slot tag ──────────────────────────────────────────────────────────────

@register.inclusion_tag('partials/ad_slot.html')
def ad_slot(slot_id='default'):
    """Usage: {% ad_slot "tool-header" %}"""
    return {'slot_id': slot_id}
