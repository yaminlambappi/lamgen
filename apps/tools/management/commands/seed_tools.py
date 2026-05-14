"""
Management command: seed_tools
Idempotently seeds ToolCategory and Tool records from config/tool_categories.py (full registry).
Usage: python manage.py seed_tools [--dry-run]
"""
from apps.tools.models import Tool, ToolCategory
from apps.tools.management.commands.base_seed import BaseSeedCommand
from config.tool_registry import filter_model_fields


class Command(BaseSeedCommand):
    help = "Seed tool categories and tools from unified registry (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Preview without saving.")

    def seed_data(self, registry, options):
        dry_run = options["dry_run"]

        if dry_run:
            for c in registry:
                tools = c.get("tools") or []
                self.stdout.write(f"[DRY RUN] Category: {c.get('name')} ({len(tools)} tools)")
                for t in tools:
                    self.stdout.write(f"  - {t.get('name')} ({t.get('slug')})")
            return

        cat_created = cat_updated = tool_created = tool_updated = 0
        skipped = 0
        failed = []

        for cat in registry:
            tools_list = list(cat.get("tools") or [])
            cat_payload = {k: v for k, v in cat.items() if k != "tools"}
            cat_slug = cat_payload["slug"]
            cat_defaults = filter_model_fields(
                ToolCategory,
                {**cat_payload, "is_active": cat_payload.get("is_active", True)},
                exclude={"slug"},
            )

            category, created = ToolCategory.objects.update_or_create(
                slug=cat_slug,
                defaults=cat_defaults,
            )
            if created:
                cat_created += 1
                self.stdout.write(self.style.SUCCESS(f"  Created category: {category.name}"))
            else:
                cat_updated += 1
                self.stdout.write(self.style.NOTICE(f"  Updated category: {category.name}"))

            for tool_row in tools_list:
                tool_slug = tool_row["slug"]
                tool_defaults = filter_model_fields(
                    Tool,
                    {
                        **tool_row,
                        "category": category,
                        "description": tool_row.get("description")
                        or tool_row.get("short_desc")
                        or "",
                    },
                    exclude={"slug"},
                )
                try:
                    tool, t_created = Tool.objects.update_or_create(
                        slug=tool_slug,
                        defaults=tool_defaults,
                    )
                except Exception as exc:
                    failed.append((tool_slug, str(exc)))
                    skipped += 1
                    self.stderr.write(self.style.ERROR(f"    Failed tool {tool_slug!r}: {exc}"))
                    continue
                if t_created:
                    tool_created += 1
                else:
                    tool_updated += 1

        self.stdout.write(self.style.SUCCESS("=== After DB upsert ==="))
        self.stdout.write(
            f"Categories: +{cat_created} created, ~{cat_updated} updated. "
            f"Tools: +{tool_created} created, ~{tool_updated} updated."
        )
        self.stdout.write(f"Skipped / failed tools: {skipped}")
        if failed:
            for slug, msg in failed:
                self.stderr.write(self.style.ERROR(f"  Failed: {slug} — {msg}"))
        self.stdout.write(
            f"Database totals: {ToolCategory.objects.count()} categories, "
            f"{Tool.objects.count()} tools."
        )
