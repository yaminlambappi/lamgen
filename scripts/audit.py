import os
import sys
from pathlib import Path

import django

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from config.tool_categories import TOOL_CATEGORIES
from apps.tools.models import Tool, ToolCategory

def audit_platform():
    db_tools = {t.slug: t for t in Tool.objects.all()}
    db_categories = {c.slug: c for c in ToolCategory.objects.all()}

    report = ""

    config_tools = []
    for category in TOOL_CATEGORIES:
        for tool in category.get("tools", []):
            config_tools.append(tool)

    # 1. Orphaned tools (in DB but not in config)
    config_tool_slugs = {t["slug"] for t in config_tools}
    orphaned_tools = [t for t in db_tools.values() if t.slug not in config_tool_slugs]

    # 2. Missing tools (in config but not in DB)
    db_tool_slugs = set(db_tools.keys())
    missing_tools = [t for t in config_tools if t["slug"] not in db_tool_slugs]

    # 3. Unused templates
    all_templates = []
    for dirpath, _, filenames in os.walk(REPO_ROOT / "templates" / "tools"):
        for f in filenames:
            if f.endswith(".html"):
                rel = os.path.relpath(os.path.join(dirpath, f), REPO_ROOT / "templates")
                all_templates.append(rel.replace(os.sep, "/"))
    used_templates = {t["template_name"] for t in config_tools}
    unused_templates = [t for t in all_templates if t not in used_templates]

    report += "# LamGen Platform Audit Report\n\n"

    report += "## 1. Category and Tool Inventory\n\n"

    for category in TOOL_CATEGORIES:
        report += f'### {category["name"]}\n\n'
        db_category = db_categories.get(category["slug"])
        category_status = "Active" if db_category and db_category.is_active else "Inactive"

        report += f'- **Status:** {category_status}\n'
        report += f'- **Frontend Visibility:** {"Visible" if category_status == "Active" else "Hidden"}\n'
        report += "- **Tools:**\n"
        for tool in category.get("tools", []):
            db_tool = db_tools.get(tool["slug"])
            tool_status = "Active" if db_tool and db_tool.is_active else "Inactive"
            template_path = REPO_ROOT / "templates" / tool.get("template_name", "")
            template_exists = template_path.is_file()

            broken_route_reasons = []
            if not db_tool:
                broken_route_reasons.append("Not in DB")
            if db_tool and not db_tool.is_active:
                broken_route_reasons.append("Tool inactive in DB")
            if db_category and not db_category.is_active:
                broken_route_reasons.append("Category inactive in DB")
            broken_route_status = ", ".join(broken_route_reasons) if broken_route_reasons else "OK"

            report += f'    - **{tool["name"]}**\n'
            report += f'        - **Active/Inactive Status:** {tool_status}\n'
            report += f'        - **Frontend Visibility:** {"Visible" if tool_status == "Active" else "Hidden"}\n'
            report += f'        - **Missing Template Status:** {"Missing" if not template_exists else "Exists"}\n'
            report += f'        - **Broken Route Status:** {broken_route_status}\n'
            report += f'        - **SEO Page Status:** {"Missing SEO info" if not (db_tool and db_tool.meta_title and db_tool.meta_description) else "OK"}\n'

    report += "## 2. Platform Health Analysis\n\n"
    report += f"### Orphaned Tools (in DB but not in config)\n- {', '.join([t.slug for t in orphaned_tools]) if orphaned_tools else 'None'}\n"
    report += f"### Missing Tools (in config but not in DB)\n- {', '.join([t['slug'] for t in missing_tools]) if missing_tools else 'None'}\n"
    report += f"### Unused Templates\n- {', '.join(unused_templates) if unused_templates else 'None'}\n"

    report += "### Duplicate Slugs\n"
    all_category_slugs = [c["slug"] for c in TOOL_CATEGORIES]
    duplicate_category_slugs = set([s for s in all_category_slugs if all_category_slugs.count(s) > 1])
    report += f"- **Duplicate Category Slugs:** {', '.join(duplicate_category_slugs) if duplicate_category_slugs else 'None'}\n"
    all_tool_slugs = [t["slug"] for t in config_tools]
    duplicate_tool_slugs = set([s for s in all_tool_slugs if all_tool_slugs.count(s) > 1])
    report += f"- **Duplicate Tool Slugs:** {', '.join(duplicate_tool_slugs) if duplicate_tool_slugs else 'None'}\n"

    report += "### Duplicate Names\n"
    all_category_names = [c["name"] for c in TOOL_CATEGORIES]
    duplicate_category_names = set([n for n in all_category_names if all_category_names.count(n) > 1])
    report += f"- **Duplicate Category Names:** {', '.join(duplicate_category_names) if duplicate_category_names else 'None'}\n"
    all_tool_names = [t["name"] for t in config_tools]
    duplicate_tool_names = set([n for n in all_tool_names if all_tool_names.count(n) > 1])
    report += f"- **Duplicate Tool Names:** {', '.join(duplicate_tool_names) if duplicate_tool_names else 'None'}\n"

    report += f"### Empty Categories\n- {', '.join([c['name'] for c in TOOL_CATEGORIES if not c.get('tools')]) if [c for c in TOOL_CATEGORIES if not c.get('tools')] else 'None'}\n"

    report += "## 3. Architecture and Strategy Analysis\n\n"
    report += "### Root Causes of Issues\n"
    report += "- **Reliance on hardcoded configuration:** The `config/tool_categories.py` file is the single source of truth, but it is disconnected from the database. This leads to potential synchronization issues.\n"
    report += "- **Manual template creation:** Templates are created manually, and there is no automated check to ensure that a template exists for every tool.\n"
    report += "- **Lack of a robust data seeding process:** The `seed_tools` command is a good start, but it does not seem to handle deletions or updates gracefully, leading to orphaned tools.\n"

    report += "### Architecture Weaknesses\n"
    report += "- **Single source of truth is a Python file:** This is not ideal for a large, dynamic system. A database-first approach would be more robust.\n"
    report += "- **No foreign key constraint between config and reality:** The system relies on convention (matching slugs) rather than database constraints to link tools and categories.\n"

    report += "### Missing Systems\n"
    report += "- **A proper CMS for managing tools and categories:** A user-friendly interface for managing tools would be a significant improvement.\n"
    report += "- **Automated testing for tool health:** There are no automated tests to check for broken routes, missing templates, or other issues.\n"

    report += "### Recommended Fixes\n"
    report += "- **Migrate to a database-first approach:** Make the database the single source of truth and build a CMS to manage it.\n"
    report += "- **Implement a robust data synchronization mechanism:** If a config file is still desired, create a script that can intelligently sync the database with the config file (handling additions, updates, and deletions).\n"
    report += "- **Create a comprehensive test suite:** Implement unit and integration tests to check for the issues identified in this report.\n"

    report += "### Scalability Issues\n"
    report += "- **The hardcoded config file will become a bottleneck:** As the number of tools grows, managing this file will become increasingly difficult.\n"
    report += "- **The lack of a CMS makes content management difficult:** Adding and updating tools is a developer-centric task, which is not scalable.\n"

    report += "### Dynamic Rendering Issues\n"
    report += "- **The system relies on a fallback template:** While this prevents crashes, it can lead to a poor user experience when templates are missing.\n"

    return report

if __name__ == "__main__":
    report = audit_platform()
    out = REPO_ROOT / "docs" / "reports" / "LAMGEN_PLATFORM_AUDIT_REPORT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Audit report generated: {out}")
