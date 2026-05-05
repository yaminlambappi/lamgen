from django import template

register = template.Library()


@register.simple_tag
def tool_gradient(category):
    return f'linear-gradient(135deg, {category.color_from}, {category.color_to})'


@register.filter
def is_bookmarked(tool_slug, bookmarked_slugs):
    return tool_slug in bookmarked_slugs


@register.simple_tag
def tool_icon_bg(category):
    return f'background: linear-gradient(135deg, {category.color_from}22, {category.color_to}22); border: 1px solid {category.color_from}44;'
