"""
LamGen Metadata Engine — Programmatic SEO generation for 265+ tools.

Generates unique, keyword-rich metadata for every tool page:
- SEO titles, meta descriptions, H1 variants
- JSON-LD schemas (SoftwareApplication, FAQPage, BreadcrumbList, WebSite, Organization)
- OG/Twitter card metadata
- Smart related tool suggestions
- Semantic keyword extraction
"""
from __future__ import annotations
import re
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# TITLE & DESCRIPTION GENERATORS
# ─────────────────────────────────────────────────────────────────────────────

# Action verbs mapped to tool name patterns for unique title generation
_VERB_MAP = {
    "formatter":   "Format",
    "validator":   "Validate",
    "converter":   "Convert",
    "generator":   "Generate",
    "checker":     "Check",
    "calculator":  "Calculate",
    "encoder":     "Encode",
    "decoder":     "Decode",
    "compressor":  "Compress",
    "minifier":    "Minify",
    "beautifier":  "Beautify",
    "builder":     "Build",
    "editor":      "Edit",
    "analyzer":    "Analyze",
    "extractor":   "Extract",
    "previewer":   "Preview",
    "tester":      "Test",
    "timer":       "Time",
    "counter":     "Count",
    "remover":     "Remove",
    "cleaner":     "Clean",
    "reverser":    "Reverse",
    "expander":    "Expand",
    "shortener":   "Shorten",
    "organizer":   "Organize",
    "estimator":   "Estimate",
    "predictor":   "Predict",
    "planner":     "Plan",
    "notepad":     "Write",
    "stopwatch":   "Track",
    "countdown":   "Count Down",
}

_CATEGORY_KEYWORDS = {
    "developer-tools":  "free online developer tool",
    "student-tools":    "free student tool",
    "writing-tools":    "free writing tool",
    "utility-tools":    "free online utility",
    "image-tools":      "free image tool",
    "pdf-tools":        "free PDF tool",
    "seo-tools":        "free SEO tool",
    "social-tools":     "free social media tool",
    "career-tools":     "free career tool",
    "resume-tools":     "free resume tool",
}


def _get_action_verb(tool_name: str) -> str:
    """Extract the primary action verb from a tool name."""
    name_lower = tool_name.lower()
    for pattern, verb in _VERB_MAP.items():
        if pattern in name_lower:
            return verb
    return "Use"


def generate_meta_title(tool_name: str, category_name: str = "") -> str:
    """
    Generate a unique, keyword-optimized meta title (≤70 chars).
    Pattern: {Tool Name} — Free Online {Category} Tool | LamGen
    """
    base = f"{tool_name} — Free Online Tool | LamGen"
    if len(base) <= 70:
        return base
    # Shorten if needed
    short = f"{tool_name} | Free Online Tool — LamGen"
    return short[:70]


def generate_meta_description(tool_name: str, short_desc: str, category_name: str = "") -> str:
    """
    Generate a unique, keyword-rich meta description (≤160 chars).
    Includes action verb, tool name, key benefit, and trust signal.
    """
    desc = short_desc.rstrip(".")

    # Build description with keyword variation
    candidates = [
        f"{desc}. Free online tool — no signup, no upload, 100% private. Works in your browser.",
        f"Free online {tool_name.lower()}. {desc}. No installation required. Instant results, completely private.",
        f"{tool_name}: {desc}. Free, instant, and secure. No account needed. Runs entirely in your browser.",
    ]

    for candidate in candidates:
        if len(candidate) <= 160:
            return candidate

    # Fallback: truncate cleanly
    fallback = f"{tool_name} — {desc}. Free online, instant, no signup required."
    return fallback[:160]


def generate_h1(tool_name: str) -> str:
    """Generate the page H1 — same as tool name for exact-match SEO."""
    return tool_name


def generate_intro_paragraph(tool_name: str, short_desc: str, category_name: str = "") -> str:
    """
    Generate a unique, human-readable intro paragraph for each tool.
    Keyword-rich but natural. ~2-3 sentences.
    """
    verb = _get_action_verb(tool_name).lower()
    desc = short_desc.rstrip(".")
    cat_kw = _CATEGORY_KEYWORDS.get(
        category_name.lower().replace(" ", "-"),
        "free online tool"
    )

    return (
        f"{tool_name} is a {cat_kw} that lets you {desc.lower()}. "
        f"It runs entirely in your browser — no server uploads, no account required, "
        f"and no data ever leaves your device. "
        f"Whether you're a developer, student, writer, or professional, "
        f"this tool delivers instant, accurate results with zero friction."
    )


def generate_use_cases(tool_name: str, tags: str = "") -> list[str]:
    """Generate contextual use cases from tool name and tags."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    name_lower = tool_name.lower()

    use_cases = []

    if "developer" in tag_list or "json" in tag_list or "code" in name_lower:
        use_cases.append(f"Developers debugging and formatting data during API development")
    if "student" in tag_list or "academic" in tag_list:
        use_cases.append(f"Students working on assignments, essays, and research papers")
    if "seo" in tag_list or "keyword" in tag_list:
        use_cases.append(f"SEO professionals optimizing content for search engines")
    if "writing" in tag_list or "text" in tag_list:
        use_cases.append(f"Writers and content creators improving their writing quality")
    if "image" in tag_list or "compress" in name_lower:
        use_cases.append(f"Web developers optimizing images for faster page load times")
    if "pdf" in tag_list:
        use_cases.append(f"Office workers managing and processing PDF documents")
    if "calculator" in name_lower or "calculate" in name_lower:
        use_cases.append(f"Anyone needing quick, accurate calculations without installing software")
    if "convert" in name_lower or "converter" in name_lower:
        use_cases.append(f"Professionals converting data between formats for different systems")
    if "generator" in name_lower:
        use_cases.append(f"Teams generating content, data, or code snippets quickly")
    if "password" in name_lower:
        use_cases.append(f"Security-conscious users creating strong, unique passwords")

    # Always add generic use cases
    use_cases.extend([
        f"Anyone who needs a fast, reliable {tool_name.lower()} without installing software",
        f"Remote workers and freelancers who need browser-based productivity tools",
    ])

    return use_cases[:5]


def generate_faq_items(tool_name: str, short_desc: str, category_name: str = "") -> list[dict]:
    """
    Generate 5+ unique, tool-specific FAQ items for FAQPage schema and display.
    """
    verb = _get_action_verb(tool_name)
    desc = short_desc.rstrip(".")

    faqs = [
        {
            "q": f"Is {tool_name} completely free?",
            "a": f"Yes, {tool_name} is 100% free with no hidden costs, no premium tiers, and no usage limits. LamGen is committed to keeping all tools free forever."
        },
        {
            "q": f"Is my data safe when using {tool_name}?",
            "a": f"Absolutely. All processing happens locally in your browser using JavaScript. Your data never leaves your device and is never sent to any server. LamGen does not store, log, or transmit any content you enter."
        },
        {
            "q": f"Do I need to create an account to use {tool_name}?",
            "a": f"No account is required. Simply open the page and start using it immediately. An optional account lets you save bookmarks and access your tool history across devices."
        },
        {
            "q": f"Does {tool_name} work on mobile devices?",
            "a": f"Yes, {tool_name} is fully responsive and works on all devices including smartphones, tablets, and desktops. The interface adapts to your screen size for a comfortable experience."
        },
        {
            "q": f"Are there any file size or usage limits?",
            "a": f"Since all processing is done in your browser, practical limits depend on your device's memory. For most use cases there are no meaningful limits. Very large inputs may be slower on older devices."
        },
        {
            "q": f"How does {tool_name} compare to desktop software?",
            "a": f"{tool_name} offers the same core functionality as desktop alternatives but with zero installation, zero cost, and instant access from any device with a browser. No updates to manage, no licenses to buy."
        },
        {
            "q": f"Can I use {tool_name} offline?",
            "a": f"Once the page has loaded, {tool_name} works without an internet connection since all processing happens in your browser. You may need to reload the page initially if you're offline."
        },
    ]

    return faqs


# ─────────────────────────────────────────────────────────────────────────────
# JSON-LD SCHEMA BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_software_application_schema(tool, request) -> dict:
    """
    Full SoftwareApplication schema with rating, screenshot, and feature list.
    """
    url = request.build_absolute_uri(tool.get_absolute_url())
    tags = [t.strip() for t in (tool.tags or "").split(",") if t.strip()]

    schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": tool.name,
        "description": tool.meta_description or tool.short_desc,
        "url": url,
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Web Browser",
        "browserRequirements": "Requires JavaScript",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
        },
        "provider": {
            "@type": "Organization",
            "name": "LamGen",
            "url": request.build_absolute_uri("/"),
        },
        "featureList": [
            "Free to use",
            "No signup required",
            "Browser-based processing",
            "No data uploaded to servers",
            "Mobile responsive",
        ],
    }

    if tags:
        schema["keywords"] = ", ".join(tags[:10])

    return schema


def build_faq_schema(items: list) -> dict:
    """Return JSON-LD FAQPage schema dict from a list of {q, a} dicts."""
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item.get("q", ""),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item.get("a", ""),
                },
            }
            for item in items
            if "q" in item and "a" in item
        ],
    }


def build_breadcrumb_schema(request, category, tool=None) -> dict:
    """Build BreadcrumbList schema for category or tool pages."""
    items = [
        {
            "@type": "ListItem",
            "position": 1,
            "name": "LamGen",
            "item": request.build_absolute_uri("/"),
        },
        {
            "@type": "ListItem",
            "position": 2,
            "name": "Tools",
            "item": request.build_absolute_uri("/tools/"),
        },
        {
            "@type": "ListItem",
            "position": 3,
            "name": category.name,
            "item": request.build_absolute_uri(category.get_absolute_url()),
        },
    ]

    if tool:
        items.append({
            "@type": "ListItem",
            "position": 4,
            "name": tool.name,
            "item": request.build_absolute_uri(tool.get_absolute_url()),
        })

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items,
    }


def build_website_schema(request) -> dict:
    """WebSite schema with SearchAction for sitelinks search box."""
    base_url = request.build_absolute_uri("/")
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "LamGen",
        "url": base_url,
        "description": "Free online tools for developers, students, writers and professionals. 265+ tools, no signup required.",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{base_url}tools/search/?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def build_organization_schema(request) -> dict:
    """Organization schema for brand authority."""
    base_url = request.build_absolute_uri("/")
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "LamGen",
        "url": base_url,
        "description": "LamGen is a free AI-powered utility ecosystem with 265+ tools for developers, students, writers and professionals.",
        "sameAs": [],
    }


def build_item_list_schema(page, request) -> dict:
    """Return JSON-LD ItemList schema dict for an SEOPage."""
    items = page.items or []
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": page.meta_title,
        "url": request.build_absolute_uri(page.get_absolute_url()),
        "numberOfItems": len(items),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": item if isinstance(item, str) else item.get("text", str(item)),
            }
            for i, item in enumerate(items[:20])
        ],
    }


def build_category_schema(category, tools, request) -> dict:
    """CollectionPage schema for category landing pages."""
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{category.name} — Free Online Tools",
        "description": category.description or category.short_desc,
        "url": request.build_absolute_uri(category.get_absolute_url()),
        "hasPart": [
            {
                "@type": "SoftwareApplication",
                "name": tool.name,
                "url": request.build_absolute_uri(tool.get_absolute_url()),
                "applicationCategory": "UtilitiesApplication",
                "offers": {"@type": "Offer", "price": "0"},
            }
            for tool in tools[:10]
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# SMART RELATED TOOLS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

# Explicit topical clusters — tools that should always link to each other
_TOPICAL_CLUSTERS = {
    "json-formatter":        ["json-validator", "json-csv-converter", "json-to-typescript", "yaml-formatter", "xml-formatter"],
    "json-validator":        ["json-formatter", "json-csv-converter", "yaml-formatter"],
    "json-csv-converter":    ["json-formatter", "json-validator", "json-to-typescript"],
    "json-to-typescript":    ["json-formatter", "json-validator", "json-csv-converter"],
    "yaml-formatter":        ["json-formatter", "xml-formatter", "toml-to-json"],
    "xml-formatter":         ["json-formatter", "yaml-formatter", "html-formatter"],
    "html-formatter":        ["css-formatter", "js-formatter", "xml-formatter"],
    "css-formatter":         ["html-formatter", "js-formatter", "css-minifier"],
    "js-formatter":          ["html-formatter", "css-formatter", "js-minifier"],
    "css-minifier":          ["js-minifier", "css-formatter", "html-formatter"],
    "js-minifier":           ["css-minifier", "js-formatter", "html-formatter"],
    "base64-encoder":        ["url-encoder", "hash-generator", "html-entity-encoder"],
    "url-encoder":           ["base64-encoder", "html-entity-encoder", "jwt-decoder"],
    "hash-generator":        ["base64-encoder", "uuid-generator", "password-generator"],
    "uuid-generator":        ["hash-generator", "fake-data-generator", "lorem-ipsum"],
    "jwt-decoder":           ["base64-encoder", "url-encoder", "hash-generator"],
    "regex-tester":          ["diff-checker", "json-formatter", "markdown-previewer"],
    "diff-checker":          ["regex-tester", "markdown-previewer", "json-formatter"],
    "markdown-previewer":    ["diff-checker", "html-formatter", "lorem-ipsum"],
    "lorem-ipsum":           ["fake-data-generator", "uuid-generator", "markdown-previewer"],
    "fake-data-generator":   ["lorem-ipsum", "uuid-generator", "json-formatter"],
    "color-converter":       ["color-palette-generator", "gradient-generator", "css-formatter"],
    "color-palette-generator": ["color-converter", "gradient-generator", "css-formatter"],
    "gradient-generator":    ["color-converter", "color-palette-generator", "css-formatter"],
    "image-compressor":      ["image-resize", "jpg-to-png", "png-to-jpg", "webp-converter"],
    "image-resize":          ["image-compressor", "jpg-to-png", "png-to-jpg"],
    "jpg-to-png":            ["png-to-jpg", "image-compressor", "webp-converter"],
    "png-to-jpg":            ["jpg-to-png", "image-compressor", "webp-converter"],
    "webp-converter":        ["jpg-to-png", "png-to-jpg", "image-compressor"],
    "qr-generator":          ["favicon-generator", "image-compressor"],
    "pdf-merge":             ["pdf-split", "image-compressor"],
    "pdf-split":             ["pdf-merge", "image-compressor"],
    "word-counter":          ["reading-time-estimator", "readability-checker", "case-converter"],
    "reading-time-estimator": ["word-counter", "readability-checker", "pomodoro-timer"],
    "readability-checker":   ["word-counter", "reading-time-estimator", "keyword-density"],
    "case-converter":        ["word-counter", "text-cleaner", "duplicate-remover"],
    "text-cleaner":          ["case-converter", "duplicate-remover", "word-counter"],
    "duplicate-remover":     ["text-cleaner", "case-converter", "word-counter"],
    "keyword-density":       ["readability-checker", "word-counter", "headline-generator"],
    "headline-generator":    ["keyword-density", "email-subject-generator", "bullet-point-generator"],
    "email-subject-generator": ["headline-generator", "bullet-point-generator", "conclusion-generator"],
    "bullet-point-generator": ["headline-generator", "paragraph-expander", "conclusion-generator"],
    "paragraph-expander":    ["bullet-point-generator", "sentence-shortener", "introduction-generator"],
    "sentence-shortener":    ["paragraph-expander", "text-cleaner", "readability-checker"],
    "introduction-generator": ["conclusion-generator", "paragraph-expander", "headline-generator"],
    "conclusion-generator":  ["introduction-generator", "paragraph-expander", "headline-generator"],
    "gpa-calculator":        ["cgpa-calculator", "grade-predictor", "pomodoro-timer"],
    "cgpa-calculator":       ["gpa-calculator", "grade-predictor", "study-planner"],
    "grade-predictor":       ["gpa-calculator", "cgpa-calculator", "exam-countdown"],
    "pomodoro-timer":        ["stopwatch", "countdown-timer", "exam-countdown"],
    "exam-countdown":        ["pomodoro-timer", "countdown-timer", "study-planner"],
    "flashcard-generator":   ["pomodoro-timer", "academic-title-generator", "plagiarism-checklist"],
    "password-generator":    ["password-strength-checker", "hash-generator", "uuid-generator"],
    "password-strength-checker": ["password-generator", "hash-generator"],
    "unit-converter":        ["age-calculator", "percentage-calculator", "bmi-calculator"],
    "age-calculator":        ["unit-converter", "date-calculator", "countdown-timer"],
    "percentage-calculator": ["unit-converter", "bmi-calculator", "age-calculator"],
    "bmi-calculator":        ["percentage-calculator", "unit-converter", "age-calculator"],
    "timezone-converter":    ["unix-timestamp-converter", "countdown-timer", "age-calculator"],
    "unix-timestamp-converter": ["timezone-converter", "cron-builder", "date-calculator"],
    "countdown-timer":       ["stopwatch", "pomodoro-timer", "exam-countdown"],
    "stopwatch":             ["countdown-timer", "pomodoro-timer"],
    "online-notepad":        ["word-counter", "text-cleaner", "markdown-previewer"],
}


def get_related_tools(tool, all_category_tools, limit: int = 8):
    """
    Return related tools using topical clusters first, then same-category fallback.
    Returns Tool queryset-compatible list.
    """
    from tools.models import Tool as ToolModel

    # 1. Check explicit topical cluster
    cluster_slugs = _TOPICAL_CLUSTERS.get(tool.slug, [])

    if cluster_slugs:
        # Fetch cluster tools in defined order
        cluster_tools = list(
            ToolModel.objects.filter(
                slug__in=cluster_slugs, is_active=True
            ).select_related("category")
        )
        # Sort by cluster order
        slug_order = {s: i for i, s in enumerate(cluster_slugs)}
        cluster_tools.sort(key=lambda t: slug_order.get(t.slug, 99))

        if len(cluster_tools) >= limit:
            return cluster_tools[:limit]

        # Pad with same-category tools
        existing_slugs = {t.slug for t in cluster_tools} | {tool.slug}
        padding = [t for t in all_category_tools if t.slug not in existing_slugs]
        return (cluster_tools + padding)[: limit]

    # 2. Fallback: same-category tools by tag similarity
    tool_tags = set(t.strip() for t in (tool.tags or "").split(",") if t.strip())
    scored = []
    for t in all_category_tools:
        if t.slug == tool.slug:
            continue
        t_tags = set(x.strip() for x in (t.tags or "").split(",") if x.strip())
        score = len(tool_tags & t_tags)
        scored.append((score, t))

    scored.sort(key=lambda x: -x[0])
    return [t for _, t in scored[:limit]]


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY HELPERS (backwards compat)
# ─────────────────────────────────────────────────────────────────────────────

def truncate_meta_title(name: str) -> str:
    return generate_meta_title(name)


def truncate_meta_description(text: str) -> str:
    return text[:160] if text else ""
