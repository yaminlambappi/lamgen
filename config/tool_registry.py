"""
Single loader for the tool/category registry used by management commands.
Provides deep copies (no in-place pop side effects), validation and normalization.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Set, Tuple, Type

from config.tool_categories_ecosystem import ECOSYSTEM_CATEGORY_SLUGS


def filter_model_fields(
    model: Type[Any],
    data: Dict[str, Any],
    exclude: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    names = {f.name for f in model._meta.fields}
    ex = exclude or set()
    return {k: v for k, v in data.items() if k in names and k not in ex}


def copy_registry() -> List[Dict[str, Any]]:
    from config.tool_categories import TOOL_CATEGORIES

    return copy.deepcopy(TOOL_CATEGORIES)


def _normalize_tool(tool: Dict[str, Any], order_hint: int) -> Dict[str, Any]:
    t = dict(tool)
    t.setdefault("order", order_hint)
    t.setdefault("description", (t.get("short_desc") or "").strip())
    t.setdefault("is_active", True)
    t.setdefault("is_ai_powered", False)
    t.setdefault("is_featured", False)
    t.setdefault("is_new", False)
    t.setdefault("is_pro", False)
    t.setdefault("is_trending", False)
    t.setdefault("tags", "")
    t.setdefault("icon", "bi-wrench")
    return t


def _normalize_category(category: Dict[str, Any]) -> Dict[str, Any]:
    c = dict(category)
    c.setdefault("is_active", True)
    c.setdefault("short_desc", c.get("short_desc") or c.get("description") or "")
    tools_raw = c.get("tools") or []
    c["tools"] = [_normalize_tool(t, i + 1) for i, t in enumerate(tools_raw)]
    return c


def prepare_registry(categories: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    src = categories if categories is not None else copy_registry()
    
    # Merge AI tools into the registry dynamically
    try:
        from apps.ai_tools.registry import TOOL_REGISTRY as AI_TOOLS
        
        # Track existing slugs to avoid duplicates
        existing_slugs = set()
        for c in src:
            for t in c.get('tools', []):
                existing_slugs.add(t.get('slug'))

        ai_cats = {}
        for tool in AI_TOOLS:
            slug = tool.get('slug')
            if slug in existing_slugs:
                # Update existing tool's properties to mark it as AI-powered and use dynamic template
                for c in src:
                    for t in c.get('tools', []):
                        if t.get('slug') == slug:
                            t['is_ai_powered'] = True
                            t['template_name'] = 'ai_tools/detail.html'
                continue  # Skip if already exists in the main registry
            
            cat_slug = tool.get('category', 'ai-other')
            if cat_slug not in ai_cats:
                ai_cats[cat_slug] = []
            
            # Map AI tool to the standard format
            mapped_tool = {
                'slug': slug,
                'name': tool.get('name'),
                'short_desc': tool.get('description') or f"AI-powered {tool.get('name')} tool.",
                'icon': tool.get('icon', 'bi-robot'),
                'is_ai_powered': True,
                # Force dynamic template from tool_base instead of defaulting to tools/index.html
                'template_name': 'ai_tools/detail.html'
            }
            ai_cats[cat_slug].append(mapped_tool)
            existing_slugs.add(slug)
            
        # Append to existing categories or create new ones
        existing_cat_slugs = {c.get('slug'): c for c in src}
        for cat_slug, tools in ai_cats.items():
            if cat_slug in existing_cat_slugs:
                if 'tools' not in existing_cat_slugs[cat_slug]:
                    existing_cat_slugs[cat_slug]['tools'] = []
                existing_cat_slugs[cat_slug]['tools'].extend(tools)
            else:
                src.append({
                    'name': cat_slug.replace('-', ' ').title(),
                    'slug': cat_slug,
                    'short_desc': f'{cat_slug.replace("-", " ").title()} AI Tools',
                    'icon': 'bi-robot',
                    'order': 99,
                    'tools': tools
                })
    except ImportError:
        pass

    return [_normalize_category(c) for c in src]


def validate_registry(categories: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """Return (errors, warnings). Empty errors means safe to seed."""
    errors: List[str] = []
    warnings: List[str] = []
    cat_slugs: Set[str] = set()
    tool_slugs: Set[str] = set()
    required_cat = ("slug", "name")
    required_tool = ("slug", "name", "short_desc", "template_name")

    for cat in categories:
        for key in required_cat:
            if not cat.get(key):
                errors.append(f"Category missing {key!r}: {cat!r}")
        slug = cat.get("slug")
        if slug:
            if slug in cat_slugs:
                errors.append(f"Duplicate category slug: {slug}")
            cat_slugs.add(slug)
        tools = cat.get("tools") or []
        if not tools:
            warnings.append(f"Category {slug!r} has no tools")
        for tool in tools:
            for key in required_tool:
                if not tool.get(key):
                    errors.append(f"Tool missing {key!r} in category {slug!r}: {tool.get('slug')!r}")
            ts = tool.get("slug")
            if ts:
                if ts in tool_slugs:
                    errors.append(f"Duplicate tool slug (global): {ts}")
                tool_slugs.add(ts)
    return errors, warnings


def registry_stats(categories: List[Dict[str, Any]]) -> Tuple[int, int]:
    n_tools = sum(len(c.get("tools") or []) for c in categories)
    return len(categories), n_tools


def ecosystem_tool_names(categories: List[Dict[str, Any]]) -> List[str]:
    names: List[str] = []
    for c in categories:
        if c.get("slug") not in ECOSYSTEM_CATEGORY_SLUGS:
            continue
        for t in c.get("tools") or []:
            n = t.get("name")
            if n:
                names.append(n)
    return sorted(names)
