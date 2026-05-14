from django.shortcuts import render, get_object_or_404

from django.views.decorators.cache import cache_page, cache_control
from .models import SEOCategory, SEOPage


@cache_control(public=True, max_age=3600, s_maxage=86400)
@cache_page(60 * 60 * 24)  # 24hr cache
def index_view(request):
    """SEO content index page"""
    categories = SEOCategory.objects.filter(is_active=True).order_by('order')
    
    return render(request, 'seo/index.html', {
        'categories': categories,
        'page_title': 'SEO Content Hub — Guides, Comparisons & Resources | LamGen',
        'meta_description': 'Browse our comprehensive SEO content including guides, comparisons, learning resources, and best tools recommendations.',
        'canonical_url': request.build_absolute_uri('/content/'),
    })


@cache_control(public=True, max_age=3600, s_maxage=86400)
@cache_page(60 * 60 * 24)  # 24hr cache
def category_view(request, category_slug):
    category = get_object_or_404(SEOCategory, slug=category_slug, is_active=True)
    pages = SEOPage.objects.filter(category=category, is_active=True).only('topic', 'slug', 'items').order_by('topic')

    return render(request, 'seo/category.html', {
        'category': category,
        'pages': pages,
        'page_title': f'{category.name} — Browse All Topics | LamGen',
        'meta_description': category.description[:160] if category.description else f'Browse all {category.name.lower()} topics. Free, curated content ready to use.',
        'canonical_url': request.build_absolute_uri(category.get_absolute_url()),
    })


@cache_control(public=True, max_age=3600, s_maxage=86400)
@cache_page(60 * 60 * 24)  # 24hr cache
def page_view(request, category_slug, page_slug):
    category = get_object_or_404(SEOCategory, slug=category_slug, is_active=True)
    page = get_object_or_404(SEOPage, slug=page_slug, category=category, is_active=True)

    # Note: View count increment is skipped when served from cache for performance

    # Related pages in same category
    related = SEOPage.objects.filter(
        category=category, is_active=True
    ).exclude(pk=page.pk).order_by('?')[:6]

    return render(request, 'seo/page.html', {
        'category': category,
        'page': page,
        'related_pages': related,
        'page_title': page.meta_title,
        'meta_description': page.meta_description,
        'canonical_url': request.build_absolute_uri(page.get_absolute_url()),
    })
