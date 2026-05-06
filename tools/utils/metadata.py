"""Metadata generation helpers."""


def truncate_meta_title(name: str) -> str:
    """Generate and truncate meta title to 70 chars."""
    title = f'{name} — Free Online Tool | LamGen'
    return title[:70]


def truncate_meta_description(text: str) -> str:
    """Truncate meta description to 160 chars."""
    return text[:160] if text else ''


def build_software_application_schema(tool, request) -> dict:
    """Return JSON-LD SoftwareApplication schema dict for a Tool."""
    return {
        '@context': 'https://schema.org',
        '@type': 'SoftwareApplication',
        'name': tool.name,
        'description': tool.short_desc,
        'url': request.build_absolute_uri(tool.get_absolute_url()),
        'applicationCategory': 'UtilitiesApplication',
        'operatingSystem': 'Web',
        'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
    }


def build_faq_schema(items: list) -> dict:
    """Return JSON-LD FAQPage schema dict from a list of {q, a} dicts."""
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': item.get('q', ''),
                'acceptedAnswer': {'@type': 'Answer', 'text': item.get('a', '')},
            }
            for item in items
            if 'q' in item and 'a' in item
        ],
    }


def build_item_list_schema(page, request) -> dict:
    """Return JSON-LD ItemList schema dict for an SEOPage."""
    items = page.items or []
    return {
        '@context': 'https://schema.org',
        '@type': 'ItemList',
        'name': page.meta_title,
        'url': request.build_absolute_uri(page.get_absolute_url()),
        'numberOfItems': len(items),
        'itemListElement': [
            {
                '@type': 'ListItem',
                'position': i + 1,
                'name': item if isinstance(item, str) else item.get('text', str(item)),
            }
            for i, item in enumerate(items[:20])
        ],
    }
