"""
Validate Developer Tools templates for production readiness.

Checks:
- template exists and loads
- no "coming soon" or placeholder markers
- has primary action, copy, and reset affordances
- reports missing items with severity
"""
from pathlib import Path
import re

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run static validation checks for Developer Tools templates."

    def handle(self, *args, **options):
        from config.tool_categories import TOOL_CATEGORIES

        category = next((c for c in TOOL_CATEGORIES if c.get("slug") == "developer-tools"), None)
        if not category:
            self.stderr.write(self.style.ERROR("Developer Tools category not found in config/tool_categories.py"))
            return

        workspace = Path.cwd()
        checks = []

        for tool in category.get("tools", []):
            template_name = tool.get("template_name", "")
            template_path = workspace / "templates" / template_name
            result = {
                "tool": tool.get("name", tool.get("slug", "unknown")),
                "slug": tool.get("slug", ""),
                "category": "Developer Tools",
                "template": template_name,
                "status": "pass",
                "runtime_errors": [],
                "missing_features": [],
                "severity": "none",
            }

            if not template_path.exists():
                result["status"] = "fail"
                result["severity"] = "critical"
                result["runtime_errors"].append("Template file missing")
                checks.append(result)
                continue

            content = template_path.read_text(encoding="utf-8", errors="ignore")
            lowered = content.lower()

            if "coming soon" in lowered:
                result["status"] = "fail"
                result["severity"] = "critical"
                result["missing_features"].append("Contains 'coming soon' text")

            # Heuristic feature checks
            if not re.search(r'class="btn-go"|onclick="[^"]*\(', content):
                result["status"] = "warn" if result["status"] == "pass" else result["status"]
                result["missing_features"].append("Primary action button not detected")

            if "copy" not in lowered:
                result["status"] = "warn" if result["status"] == "pass" else result["status"]
                result["missing_features"].append("Copy action not detected")

            if "reset" not in lowered and "clear" not in lowered:
                result["status"] = "warn" if result["status"] == "pass" else result["status"]
                result["missing_features"].append("Reset/Clear action not detected")

            if "placeholder" in lowered and len(content.strip()) < 250:
                result["status"] = "warn" if result["status"] == "pass" else result["status"]
                result["missing_features"].append("Template appears minimal")

            if result["status"] == "warn" and result["severity"] == "none":
                result["severity"] = "medium"

            checks.append(result)

        self.stdout.write(self.style.MIGRATE_HEADING("Developer Tools Validation Report"))
        fail_count = 0
        warn_count = 0
        pass_count = 0
        for row in checks:
            status = row["status"]
            if status == "fail":
                fail_count += 1
                prefix = self.style.ERROR("[FAIL]")
            elif status == "warn":
                warn_count += 1
                prefix = self.style.WARNING("[WARN]")
            else:
                pass_count += 1
                prefix = self.style.SUCCESS("[PASS]")

            self.stdout.write(f"{prefix} {row['tool']} ({row['slug']})")
            if row["runtime_errors"]:
                self.stdout.write(f"  runtime_errors: {', '.join(row['runtime_errors'])}")
            if row["missing_features"]:
                self.stdout.write(f"  missing_features: {', '.join(row['missing_features'])}")

        self.stdout.write("")
        self.stdout.write(
            f"Summary: total={len(checks)} pass={pass_count} warn={warn_count} fail={fail_count}"
        )

