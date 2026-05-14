from django.contrib.auth import get_user_model
from apps.tools.models import Tool, ToolCategory
from apps.tools.management.commands.base_seed import BaseSeedCommand
from config.tool_registry import filter_model_fields


class Command(BaseSeedCommand):
    help = "Seeds the database with all tools, categories, and a superuser from the unified registry."

    def seed_data(self, registry, options):
        self.clear_data()

        cat_created = cat_updated = 0
        tool_created = tool_updated = 0
        skipped_tools = 0
        failed = []

        for cat in registry:
            tools = list(cat.get("tools") or [])
            cat_payload = {k: v for k, v in cat.items() if k != "tools"}
            cat_defaults = filter_model_fields(
                ToolCategory,
                {
                    **cat_payload,
                    "seo_title": "{} - LamGen".format(cat_payload.get("name", "")),
                    "seo_description": "Find the best {} tools on LamGen.".format(cat_payload.get("name", "")),
                },
                exclude={"slug"},
            )
            category, c_created = ToolCategory.objects.update_or_create(
                slug=cat_payload["slug"],
                defaults=cat_defaults,
            )
            if c_created:
                cat_created += 1
                self.stdout.write(self.style.SUCCESS(f"  Created category: {category.name}"))
            else:
                cat_updated += 1
                self.stdout.write(self.style.NOTICE(f"  Updated category: {category.name}"))

            for tool_row in tools:
                tool_defaults = filter_model_fields(
                    Tool,
                    {
                        **tool_row,
                        "category": category,
                        "meta_title": "{} - LamGen".format(tool_row.get("name", ""))[:70],
                        "meta_description": (tool_row.get("short_desc") or "")[:160],
                    },
                    exclude={"slug"},
                )
                try:
                    tool, t_created = Tool.objects.update_or_create(
                        slug=tool_row["slug"],
                        defaults=tool_defaults,
                    )
                except Exception as exc:
                    failed.append((tool_row.get("slug"), str(exc)))
                    skipped_tools += 1
                    self.stderr.write(
                        self.style.ERROR(f"    Failed tool {tool_row.get("slug")!r}: {exc}")
                    )
                    continue
                if t_created:
                    tool_created += 1
                    self.stdout.write(self.style.SUCCESS(f"    Created tool: {tool.name}"))
                else:
                    tool_updated += 1
                    self.stdout.write(self.style.NOTICE(f"    Updated tool: {tool.name}"))

        self.create_superuser()

        self.stdout.write(self.style.SUCCESS("=== After DB insert ==="))
        self.stdout.write(
            f"Categories: +{cat_created} created, ~{cat_updated} updated. "
            f"Tools: +{tool_created} created, ~{tool_updated} updated."
        )
        self.stdout.write(f"Skipped / failed tools: {skipped_tools}")
        if failed:
            for slug, msg in failed:
                self.stderr.write(self.style.ERROR(f"  Failed: {slug} — {msg}"))
        self.stdout.write(
            f"Database now has {ToolCategory.objects.count()} categories, "
            f"{Tool.objects.count()} tools."
        )

    def clear_data(self):
        self.stdout.write(self.style.SUCCESS("Clearing existing data..."))
        Tool.objects.all().delete()
        ToolCategory.objects.all().delete()

    def create_superuser(self):
        self.stdout.write(self.style.SUCCESS("Creating superuser..."))
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "password")
