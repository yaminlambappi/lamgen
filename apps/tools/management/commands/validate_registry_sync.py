"""
Management command: validate_registry_sync
Generates a diagnostic report of mismatches between the registry and DB.
Safe to run anytime — read-only, no writes.

Usage:
    python manage.py validate_registry_sync
"""
from django.core.management.base import BaseCommand
from django.template.loader import get_template, TemplateDoesNotExist
from apps.tools.models import Tool, ToolCategory
from config.tool_registry import prepare_registry, validate_registry, registry_stats


class Command(BaseCommand):
    help = "Read-only diagnostic: compare registry vs DB, report mismatches."

    def handle(self, *args, **options):
        registry = prepare_registry()
        errors, warnings = validate_registry(registry)
        n_cat, n_tool = registry_stats(registry)

        self.stdout.write(self.style.SUCCESS("=== Registry State ==="))
        self.stdout.write(f"Categories : {n_cat}")
        self.stdout.write(f"Tools      : {n_tool}")

        # Collect registry slugs
        reg_cat_slugs = {c['slug'] for c in registry}
        reg_tool_slugs = {
            t['slug']
            for c in registry
            for t in (c.get('tools') or [])
        }

        # --- Validation errors ---
        if errors:
            self.stdout.write(self.style.ERROR("\n=== Registry Validation ERRORS ==="))
            for e in errors:
                self.stderr.write(self.style.ERROR(f"  {e}"))
        else:
            self.stdout.write(self.style.SUCCESS("\n[OK] Registry validation passed (no duplicate slugs)"))

        for w in warnings:
            self.stdout.write(self.style.WARNING(f"  WARN: {w}"))

        # --- DB vs Registry mismatches ---
        self.stdout.write(self.style.SUCCESS("\n=== DB vs Registry Mismatches ==="))

        db_cat_slugs = set(ToolCategory.objects.values_list('slug', flat=True))
        db_tool_slugs = set(Tool.objects.values_list('slug', flat=True))

        missing_cats = reg_cat_slugs - db_cat_slugs
        orphan_cats = db_cat_slugs - reg_cat_slugs
        missing_tools = reg_tool_slugs - db_tool_slugs
        orphan_tools = db_tool_slugs - reg_tool_slugs

        if missing_cats:
            self.stdout.write(self.style.WARNING(f"\nCategories in registry but NOT in DB ({len(missing_cats)}):"))
            for s in sorted(missing_cats):
                self.stdout.write(f"  [MISSING] {s}")
        else:
            self.stdout.write("  [OK] All registry categories are in DB")

        if orphan_cats:
            self.stdout.write(self.style.WARNING(f"\nCategories in DB but NOT in registry ({len(orphan_cats)}) — orphans:"))
            for s in sorted(orphan_cats):
                self.stdout.write(f"  [ORPHAN] {s}")
        else:
            self.stdout.write("  [OK] No orphan categories in DB")

        if missing_tools:
            self.stdout.write(self.style.WARNING(f"\nTools in registry but NOT in DB ({len(missing_tools)}):"))
            for s in sorted(missing_tools):
                self.stdout.write(f"  [MISSING] {s}")
        else:
            self.stdout.write("  [OK] All registry tools are in DB")

        if orphan_tools:
            self.stdout.write(self.style.WARNING(f"\nTools in DB but NOT in registry ({len(orphan_tools)}) — orphans:"))
            for s in sorted(orphan_tools):
                self.stdout.write(f"  [ORPHAN] {s}")
        else:
            self.stdout.write("  [OK] No orphan tools in DB")

        # --- Broken routes (template missing) ---
        self.stdout.write(self.style.SUCCESS("\n=== Broken Routes (template missing) ==="))
        broken = []
        for c in registry:
            for t in (c.get('tools') or []):
                tmpl = t.get('template_name')
                if not tmpl:
                    broken.append((t['slug'], 'no template_name'))
                    continue
                try:
                    get_template(tmpl)
                except TemplateDoesNotExist:
                    broken.append((t['slug'], f"template not found: {tmpl}"))

        if broken:
            self.stdout.write(self.style.WARNING(f"  {len(broken)} tools with missing templates:"))
            for slug, reason in broken:
                self.stdout.write(f"  [BROKEN] {slug} — {reason}")
        else:
            self.stdout.write("  [OK] All tool templates exist on disk")

        # --- AI vs Utility counts ---
        self.stdout.write(self.style.SUCCESS("\n=== Tool Type Breakdown (from DB) ==="))
        ai_count = Tool.objects.filter(is_active=True, is_ai_powered=True).count()
        util_count = Tool.objects.filter(is_active=True, is_ai_powered=False).count()
        total_active = Tool.objects.filter(is_active=True).count()
        self.stdout.write(f"  Active tools : {total_active}")
        self.stdout.write(f"  AI-powered   : {ai_count}")
        self.stdout.write(f"  Utility      : {util_count}")

        # --- Category counts ---
        self.stdout.write(self.style.SUCCESS("\n=== Category Tool Counts (DB) ==="))
        from django.db.models import Count, Q
        for cat in (
            ToolCategory.objects.filter(is_active=True)
            .annotate(
                active=Count('tools', filter=Q(tools__is_active=True)),
                ai=Count('tools', filter=Q(tools__is_active=True, tools__is_ai_powered=True)),
            )
            .order_by('order', 'name')
        ):
            self.stdout.write(f"  {cat.name:<40} total={cat.active}  ai={cat.ai}  utility={cat.active - cat.ai}")

        self.stdout.write(self.style.SUCCESS("\n=== Validation complete ==="))
