"""
Bug condition exploration and preservation tests for tools-page-js-errors.

Bug Condition (C):
  1. base.html renders {% block extra_js %} BEFORE tool-runtime.js script tag
     → registerToolData is not defined when tool scripts execute
  2. xml-formatter.html has duplicate `let indentSize` declaration
  3. sql-beautifier.html has duplicate `const BREAK_BEFORE` declaration

Expected Behavior (P):
  1. tool-runtime.js script tag appears BEFORE {% block extra_js %} in base.html
  2. `let indentSize` appears exactly once in xml-formatter.html script block
  3. `const BREAK_BEFORE` appears exactly once in sql-beautifier.html script block

Preservation (¬C):
  - All tool pages not calling registerToolData are unaffected
  - tool-runtime.js API (registerToolData/getToolData) semantics unchanged
  - xml-formatter setIndent function still present
  - sql-beautifier BREAK_BEFORE set and formatSql function still present
"""
import re
import os
import pytest
from pathlib import Path
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_HTML = BASE_DIR / "templates" / "base.html"
XML_FORMATTER_HTML = BASE_DIR / "templates" / "tools" / "developer" / "xml-formatter.html"
SQL_BEAUTIFIER_HTML = BASE_DIR / "templates" / "tools" / "developer" / "sql-beautifier.html"


# ── Property 1: Bug Condition — Script Ordering ──────────────────────────────

def test_tool_runtime_loaded_before_extra_js_block():
    """
    **Property 1: Bug Condition** - Script Ordering Bug

    Asserts that in base.html, the tool-runtime.js <script> tag appears
    BEFORE the {% block extra_js %} tag. On unfixed code this FAILS,
    confirming the bug exists.
    """
    content = BASE_HTML.read_text(encoding="utf-8")

    # Find positions of the two markers
    runtime_pos = content.find("tool-runtime.js")
    extra_js_pos = content.find("{% block extra_js %}")

    assert runtime_pos != -1, "tool-runtime.js script tag not found in base.html"
    assert extra_js_pos != -1, "{% block extra_js %} block not found in base.html"

    assert runtime_pos < extra_js_pos, (
        f"BUG CONFIRMED: tool-runtime.js (pos {runtime_pos}) appears AFTER "
        f"{{% block extra_js %}} (pos {extra_js_pos}). "
        "Fix: move <script src='tool-runtime.js'> to before {% block extra_js %}."
    )


# ── Property 1: Bug Condition — Duplicate let indentSize ────────────────────

def test_xml_formatter_no_duplicate_indent_size():
    """
    **Property 1: Bug Condition** - Duplicate let indentSize in xml-formatter

    Asserts that `let indentSize` appears exactly once in xml-formatter.html.
    On unfixed code with a duplicate this FAILS, confirming the bug exists.
    """
    content = XML_FORMATTER_HTML.read_text(encoding="utf-8")
    count = content.count("let indentSize")
    assert count == 1, (
        f"BUG CONFIRMED: 'let indentSize' appears {count} times in xml-formatter.html "
        "(expected exactly 1). Duplicate let declaration causes SyntaxError."
    )


# ── Property 1: Bug Condition — Duplicate const BREAK_BEFORE ────────────────

def test_sql_beautifier_no_duplicate_break_before():
    """
    **Property 1: Bug Condition** - Duplicate const BREAK_BEFORE in sql-beautifier

    Asserts that `const BREAK_BEFORE` appears exactly once in sql-beautifier.html.
    On unfixed code with a duplicate this FAILS, confirming the bug exists.
    """
    content = SQL_BEAUTIFIER_HTML.read_text(encoding="utf-8")
    count = content.count("const BREAK_BEFORE")
    assert count == 1, (
        f"BUG CONFIRMED: 'const BREAK_BEFORE' appears {count} times in sql-beautifier.html "
        "(expected exactly 1). Duplicate const declaration causes SyntaxError."
    )


# ── Property 2: Preservation — tool_js block still present in base.html ─────

def test_base_html_tool_js_block_preserved():
    """
    **Property 2: Preservation** - {% block tool_js %} still present in base.html

    Tools that use {% block tool_js %} directly (not via tool_base.html) must
    continue to work. The block must still exist after the fix.
    """
    content = BASE_HTML.read_text(encoding="utf-8")
    assert "{% block tool_js %}" in content, (
        "{% block tool_js %} block missing from base.html — tools using it directly would break."
    )


def test_base_html_extra_js_block_preserved():
    """
    **Property 2: Preservation** - {% block extra_js %} still present in base.html
    """
    content = BASE_HTML.read_text(encoding="utf-8")
    assert "{% block extra_js %}" in content, (
        "{% block extra_js %} block missing from base.html."
    )


# ── Property 2: Preservation — xml-formatter core functions intact ───────────

def test_xml_formatter_set_indent_function_preserved():
    """
    **Property 2: Preservation** - setIndent function still present in xml-formatter

    After removing any duplicate declaration, the setIndent function must still
    be present and functional.
    """
    content = XML_FORMATTER_HTML.read_text(encoding="utf-8")
    assert "function setIndent(" in content, (
        "setIndent function missing from xml-formatter.html — indent switching would break."
    )
    assert "indentSize = size" in content, (
        "indentSize assignment in setIndent missing — indent switching would break."
    )


def test_xml_formatter_register_tool_data_present():
    """
    **Property 2: Preservation** - registerToolData call still present in xml-formatter
    """
    content = XML_FORMATTER_HTML.read_text(encoding="utf-8")
    assert "registerToolData('xmlFormatter'" in content, (
        "registerToolData call missing from xml-formatter.html."
    )


# ── Property 2: Preservation — sql-beautifier core functions intact ──────────

def test_sql_beautifier_format_sql_function_preserved():
    """
    **Property 2: Preservation** - formatSql function still present in sql-beautifier

    After removing any duplicate declaration, the formatSql function must still
    be present and use BREAK_BEFORE.
    """
    content = SQL_BEAUTIFIER_HTML.read_text(encoding="utf-8")
    assert "function formatSql(" in content, (
        "formatSql function missing from sql-beautifier.html."
    )
    assert "BREAK_BEFORE.forEach" in content, (
        "BREAK_BEFORE.forEach usage missing from sql-beautifier.html — SQL formatting would break."
    )


def test_sql_beautifier_break_before_set_preserved():
    """
    **Property 2: Preservation** - BREAK_BEFORE set contains expected SQL keywords
    """
    content = SQL_BEAUTIFIER_HTML.read_text(encoding="utf-8")
    # Extract the BREAK_BEFORE set definition
    match = re.search(r'const BREAK_BEFORE\s*=\s*new Set\(\[([^\]]+)\]\)', content)
    assert match is not None, "BREAK_BEFORE set definition not found in sql-beautifier.html"
    keywords_str = match.group(1)
    for keyword in ["SELECT", "FROM", "WHERE", "ORDER BY"]:
        assert keyword in keywords_str, (
            f"Expected SQL keyword '{keyword}' missing from BREAK_BEFORE set."
        )


# ── Property 2: Preservation — tool-runtime.js API contract ─────────────────

def test_tool_runtime_js_exists():
    """
    **Property 2: Preservation** - tool-runtime.js file still exists and is unchanged
    """
    runtime_path = BASE_DIR / "static" / "js" / "tool-runtime.js"
    assert runtime_path.exists(), "static/js/tool-runtime.js not found"


def test_tool_runtime_js_api_intact():
    """
    **Property 2: Preservation** - registerToolData and getToolData still defined in tool-runtime.js
    """
    runtime_path = BASE_DIR / "static" / "js" / "tool-runtime.js"
    content = runtime_path.read_text(encoding="utf-8")
    assert "registerToolData" in content, "registerToolData missing from tool-runtime.js"
    assert "getToolData" in content, "getToolData missing from tool-runtime.js"
    assert "window.LamGenTools" in content, "window.LamGenTools missing from tool-runtime.js"
