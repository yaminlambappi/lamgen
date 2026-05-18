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
    # Ensure template_name always resolves to a file that exists on disk.
    # Tools without a specific template use the universal generic_tool.html.
    tmpl = t.get("template_name") or ""
    if tmpl:
        try:
            from django.template.loader import get_template, TemplateDoesNotExist
            get_template(tmpl)
        except Exception:
            t["template_name"] = "tools/generic_tool.html"
    else:
        t["template_name"] = "tools/generic_tool.html"
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
    
    # Sync AI tool flags: mark tools that exist in the AI registry as is_ai_powered.
    # AI-only slugs (no template) are NOT injected into the DB — they are served
    # via the AI API endpoint directly. This prevents phantom categories.
    try:
        from apps.ai_tools.registry import TOOL_REGISTRY as AI_TOOLS
        ai_slug_set = {t.get('slug') for t in AI_TOOLS}
        for c in src:
            for t in c.get('tools', []):
                if t.get('slug') in ai_slug_set:
                    t['is_ai_powered'] = True
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
