from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import cache_control
from .models import ContentArticle
import json


def build_article_schema(article, request):
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "author": {"@type": "Organization", "name": article.author},
        "datePublished": article.published_at.isoformat() if article.published_at else "",
        "dateModified": article.updated_at.isoformat(),
        "url": request.build_absolute_uri(article.get_absolute_url()),
        "publisher": {
            "@type": "Organization",
            "name": "LamGen",
            "url": request.build_absolute_uri("/"),
        },
    }


@cache_control(public=True, max_age=3600)
def blog_index(request):
    articles = ContentArticle.objects.filter(is_published=True).prefetch_related("related_tools")[:20]
    return render(request, "blog/index.html", {
        "articles": articles,
        "page_title": "Blog & Guides — LamGen",
        "meta_description": "Tutorials, comparisons, and guides for developers, students, and writers. Learn how to use free online tools effectively.",
        "canonical_url": request.build_absolute_uri("/blog/"),
    })


@cache_control(public=True, max_age=3600)
def blog_type_index(request, content_type):
    label_map = dict(ContentArticle.CONTENT_TYPES)
    label = label_map.get(content_type, content_type.title())
    articles = ContentArticle.objects.filter(is_published=True, content_type=content_type)
    return render(request, "blog/type_index.html", {
        "articles": articles,
        "content_type": content_type,
        "content_type_label": label,
        "page_title": f"{label} — LamGen Blog",
        "meta_description": f"Browse all {label.lower()} articles on LamGen.",
        "canonical_url": request.build_absolute_uri(f"/blog/{content_type}/"),
    })


@cache_control(public=True, max_age=3600)
def article_view(request, content_type, slug):
    article = get_object_or_404(ContentArticle, slug=slug, content_type=content_type, is_published=True)
    related_articles = ContentArticle.objects.filter(
        is_published=True, content_type=content_type
    ).exclude(pk=article.pk)[:4]
    schema = json.dumps(build_article_schema(article, request))
    return render(request, "blog/article.html", {
        "article": article,
        "related_articles": related_articles,
        "page_title": article.meta_title or article.title,
        "meta_description": article.meta_description,
        "canonical_url": request.build_absolute_uri(article.get_absolute_url()),
        "schema_json": schema,
    })
