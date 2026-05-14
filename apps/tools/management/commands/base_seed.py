from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.tools.models import Tool, ToolCategory
from config.tool_registry import (
    ecosystem_tool_names,
    filter_model_fields,
    prepare_registry,
    registry_stats,
    validate_registry,
)

class BaseSeedCommand(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting the seeder..."))

        registry = prepare_registry()
        errors, warnings = validate_registry(registry)
        n_cat, n_tool = registry_stats(registry)

        self.stdout.write(self.style.SUCCESS("=== Registry (before DB insert) ==="))
        self.stdout.write(f"Total categories loaded: {n_cat}")
        self.stdout.write(f"Total tools loaded: {n_tool}")
        self.stdout.write("Category names (sorted by order, name):")
        for c in sorted(registry, key=lambda x: (x.get("order", 0), x.get("name") or "")):
            self.stdout.write(f"  - {c.get("name")} [{c.get("slug")}]")
        eco = ecosystem_tool_names(registry)
        self.stdout.write(f"Ecosystem / new-vertical tool names ({len(eco)}):")
        for name in eco:
            self.stdout.write(f"  - {name}")

        for w in warnings:
            self.stdout.write(self.style.WARNING(f"Validation warning: {w}"))
        if errors:
            self.stdout.write(self.style.ERROR("Validation failed; aborting seed."))
            for e in errors:
                self.stderr.write(self.style.ERROR(f"  {e}"))
            return

        missing_eco = []
        from config.tool_categories_ecosystem import ECOSYSTEM_CATEGORY_SLUGS

        reg_slugs = {c.get("slug") for c in registry}
        for s in sorted(ECOSYSTEM_CATEGORY_SLUGS):
            if s not in reg_slugs:
                missing_eco.append(s)
        if missing_eco:
            self.stderr.write(self.style.ERROR(f"Missing ecosystem category slugs: {missing_eco}"))
            return

        self.seed_data(registry, options)

        cache.delete("tool_categories_nav_v2")
        cache.delete("tool_count_active_v1")

        self.stdout.write(self.style.SUCCESS("Seeding complete."))

    def seed_data(self, registry, options):
        raise NotImplementedError("Subclasses must implement seed_data method.")
