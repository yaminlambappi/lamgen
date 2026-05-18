"""
Management command: verify_tools

Compares the registry (source of truth) against the database and reports:
  - Total tools/categories in registry vs DB
  - Tools present in registry but missing from DB
  - Tools present in DB but not in registry (orphans)
  - Version mismatches between registry and DB entries

Usage:
    python manage.py verify_tools
    python manage.py verify_tools --fail-on-mismatch   # exit code 1 if any issue (for CI)

Run this after every git pull or deployment.
"""
import sys

from django.core.management.base import BaseCommand

from apps.tools.models import Tool, ToolCategory
from apps.tools.management.commands.seed_tools import REGISTRY_VERSION
from config.tool_registry import prepare_registry, validate_registry, registry_stats


class Command(BaseCommand):
    help = (
        "Verify that the database matches the tool registry. "
        "Reports missing tools, orphans and version mismatches."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fail-on-mismatch",
            action="store_true",
            help="Exit with code 1 if any mismatch is found (useful for CI/CD pipelines).",
        )

    def handle(self, *args, **options):
        fail_on_mismatch = options["fail_on_mismatch"]
        issues_found = False

        # ------------------------------------------------------------------
        # Load + validate registry
        # ------------------------------------------------------------------
        registry = prepare_registry()
        errors, warnings = validate_registry(registry)
        n_reg_cats, n_reg_tools = registry_stats(registry)

        if errors:
            self.stderr.write(self.style.ERROR("Registry has validation errors:"))
            for e in errors:
                self.stderr.write(self.style.ERROR(f"  {e}"))
            issues_found = True

        if warnings:
            for w in warnings:
                self.stdout.write(self.style.WARNING(f"  [warn] {w}"))

        # ------------------------------------------------------------------
        # Collect slugs from registry
        # ------------------------------------------------------------------
        registry_cat_slugs: set[str] = set()
        registry_tool_slugs: set[str] = set()
        registry_tool_versions: dict[str, str] = {}

        for cat in registry:
            registry_cat_slugs.add(cat["slug"])
            for tool in cat.get("tools") or []:
                ts = tool["slug"]
                registry_tool_slugs.add(ts)
                registry_tool_versions[ts] = REGISTRY_VERSION  # single version source

        # ------------------------------------------------------------------
        # Collect slugs from DB
        # ------------------------------------------------------------------
        db_cat_slugs: set[str] = set(ToolCategory.objects.values_list("slug", flat=True))
        db_tools_qs = Tool.objects.values("slug", "registry_version")
        db_tool_slugs: set[str] = set()
        db_tool_versions: dict[str, str] = {}
        for row in db_tools_qs:
            db_tool_slugs.add(row["slug"])
            db_tool_versions[row["slug"]] = row["registry_version"]

        n_db_cats = ToolCategory.objects.count()
        n_db_tools = Tool.objects.count()

        # ------------------------------------------------------------------
        # Report
        # ------------------------------------------------------------------
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  LAMGEN TOOL REGISTRY VERIFICATION REPORT")
        self.stdout.write("=" * 60)

        self.stdout.write(f"\n{'Registry':20} | {n_reg_cats:>6} categories  {n_reg_tools:>6} tools")
        self.stdout.write(f"{'Database':20} | {n_db_cats:>6} categories  {n_db_tools:>6} tools")

        # Missing from DB (in registry, not in DB)
        missing_tools = registry_tool_slugs - db_tool_slugs
        missing_cats = registry_cat_slugs - db_cat_slugs
        if missing_tools or missing_cats:
            issues_found = True
            self.stdout.write(self.style.ERROR(f"\n[MISSING FROM DB]"))
            for s in sorted(missing_cats):
                self.stdout.write(self.style.ERROR(f"  category: {s}"))
            for s in sorted(missing_tools):
                self.stdout.write(self.style.ERROR(f"  tool    : {s}"))
        else:
            self.stdout.write(self.style.SUCCESS("\n[OK] No missing tools or categories in DB."))

        # Orphans in DB (in DB, not in registry)
        orphan_tools = db_tool_slugs - registry_tool_slugs
        orphan_cats = db_cat_slugs - registry_cat_slugs
        if orphan_tools or orphan_cats:
            issues_found = True
            self.stdout.write(self.style.WARNING(f"\n[ORPHAN IN DB — not in registry]"))
            for s in sorted(orphan_cats):
                self.stdout.write(self.style.WARNING(f"  category: {s}"))
            for s in sorted(orphan_tools):
                self.stdout.write(self.style.WARNING(f"  tool    : {s}"))
        else:
            self.stdout.write(self.style.SUCCESS("[OK] No orphan tools or categories in DB."))

        # Version mismatches
        version_mismatches = []
        for slug in registry_tool_slugs & db_tool_slugs:
            db_ver = db_tool_versions.get(slug, "?")
            reg_ver = REGISTRY_VERSION
            if db_ver != reg_ver:
                version_mismatches.append((slug, db_ver, reg_ver))

        if version_mismatches:
            issues_found = True
            self.stdout.write(self.style.WARNING(f"\n[VERSION MISMATCH] ({len(version_mismatches)} tools)"))
            self.stdout.write(f"  {'Slug':45} {'DB ver':10} {'Registry ver':12}")
            self.stdout.write(f"  {'-'*45} {'-'*10} {'-'*12}")
            for slug, db_ver, reg_ver in sorted(version_mismatches):
                self.stdout.write(f"  {slug:45} {db_ver:10} {reg_ver:12}")
        else:
            self.stdout.write(self.style.SUCCESS("[OK] No version mismatches."))

        # ------------------------------------------------------------------
        # Final verdict
        # ------------------------------------------------------------------
        self.stdout.write("\n" + "=" * 60)
        if issues_found:
            self.stdout.write(
                self.style.ERROR(
                    "RESULT: MISMATCH DETECTED\n"
                    "  Fix: python manage.py seed_tools --strict-sync"
                )
            )
            self.stdout.write("=" * 60 + "\n")
            if fail_on_mismatch:
                sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("RESULT: FULLY IN SYNC ✓"))
            self.stdout.write("=" * 60 + "\n")
