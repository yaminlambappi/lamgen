"""
Management command: seed_tools
Idempotently seeds ToolCategory and Tool records from the registry
(config/tool_categories.py + ecosystem extension).

Usage:
    python manage.py seed_tools              # upsert only — safe, no deletions
    python manage.py seed_tools --strict-sync  # upsert + delete orphan DB tools/categories
    python manage.py seed_tools --dry-run    # preview without writing anything
"""
from django.core.cache import cache
from django.db import connection

from apps.tools.models import Tool, ToolCategory
from apps.tools.management.commands.base_seed import BaseSeedCommand
from config.tool_registry import filter_model_fields

# Bump this whenever the registry schema changes shape.
REGISTRY_VERSION = "1.1"


def _version_column_exists() -> bool:
    """Return True only if registry_version column exists in the DB.
    Lets seed_tools run safely on a server before migration 0009 is applied."""
    try:
        cols = connection.introspection.get_table_description(
            connection.cursor(), "tools_tool"
        )
        return any(c.name == "registry_version" for c in cols)
    except Exception:
        return False


class Command(BaseSeedCommand):
    help = (
        "Seed tool categories and tools from the unified registry (idempotent). "
        "Use --strict-sync to also remove orphan DB entries not present in the registry."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would change without writing to the database.",
        )
        parser.add_argument(
            "--strict-sync",
            action="store_true",
            help=(
                "After upserting, delete any Tool or ToolCategory whose slug "
                "is NOT present in the registry. "
                "Ensures DB == registry exactly."
            ),
        )

    # ------------------------------------------------------------------
    def seed_data(self, registry, options):
        dry_run = options["dry_run"]
        strict_sync = options["strict_sync"]

        if dry_run:
            self._dry_run_preview(registry, strict_sync)
            return

        # Detect whether registry_version column is available yet.
        has_version_col = _version_column_exists()
        if not has_version_col:
            self.stdout.write(
                self.style.WARNING(
                    "  [warn] registry_version column missing — run 'python manage.py migrate' "
                    "to enable version tracking. Seeding continues without it."
                )
            )

        cat_created = cat_updated = tool_created = tool_updated = 0
        version_bumped = skipped = 0
        failed = []

        registry_cat_slugs: set[str] = set()
        registry_tool_slugs: set[str] = set()

        for cat in registry:
            tools_list = list(cat.get("tools") or [])
            cat_payload = {k: v for k, v in cat.items() if k != "tools"}
            cat_slug = cat_payload["slug"]
            registry_cat_slugs.add(cat_slug)

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
                self.stdout.write(self.style.SUCCESS(f"  [+] Category created: {category.name}"))
            else:
                cat_updated += 1
                self.stdout.write(self.style.NOTICE(f"  [~] Category updated: {category.name}"))

            for tool_row in tools_list:
                tool_slug = tool_row["slug"]
                registry_tool_slugs.add(tool_slug)

                base_data = {
                    **tool_row,
                    "category": category,
                    "description": tool_row.get("description") or tool_row.get("short_desc") or "",
                }
                if has_version_col:
                    base_data["registry_version"] = REGISTRY_VERSION

                tool_defaults = filter_model_fields(
                    Tool,
                    base_data,
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
                    self.stderr.write(self.style.ERROR(f"    [!] Failed tool {tool_slug!r}: {exc}"))
                    continue

                if t_created:
                    tool_created += 1
                else:
                    tool_updated += 1
                    if has_version_col and tool.registry_version != REGISTRY_VERSION:
                        version_bumped += 1

        # ------------------------------------------------------------------
        # STRICT SYNC: remove orphans
        # ------------------------------------------------------------------
        deleted_tools = deleted_cats = 0
        if strict_sync:
            orphan_tools = Tool.objects.exclude(slug__in=registry_tool_slugs)
            orphan_count = orphan_tools.count()
            if orphan_count:
                names = list(orphan_tools.values_list("slug", flat=True))
                orphan_tools.delete()
                deleted_tools = orphan_count
                self.stdout.write(
                    self.style.WARNING(f"  [x] Strict-sync: deleted {orphan_count} orphan tool(s): {names}")
                )

            orphan_cats = ToolCategory.objects.exclude(slug__in=registry_cat_slugs)
            cat_count = orphan_cats.count()
            if cat_count:
                cnames = list(orphan_cats.values_list("slug", flat=True))
                orphan_cats.delete()
                deleted_cats = cat_count
                self.stdout.write(
                    self.style.WARNING(f"  [x] Strict-sync: deleted {cat_count} orphan category(ies): {cnames}")
                )

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n=== Seed complete ==="))
        self.stdout.write(
            f"Categories : +{cat_created} created, ~{cat_updated} updated"
            + (f", -{deleted_cats} deleted" if strict_sync else "")
        )
        self.stdout.write(
            f"Tools      : +{tool_created} created, ~{tool_updated - tool_created} updated"
            f", {version_bumped} version-bumped"
            + (f", -{deleted_tools} deleted" if strict_sync else "")
        )
        if skipped:
            self.stdout.write(self.style.WARNING(f"Skipped / failed: {skipped}"))
        if failed:
            for slug, msg in failed:
                self.stderr.write(self.style.ERROR(f"  Failed: {slug} — {msg}"))

        self.stdout.write(
            f"DB totals  : {ToolCategory.objects.count()} categories, "
            f"{Tool.objects.count()} tools."
        )

        # Invalidate caches
        cache.delete("tool_categories_nav_v2")
        cache.delete("tool_count_active_v1")

    # ------------------------------------------------------------------
    def _dry_run_preview(self, registry, strict_sync):
        self.stdout.write(self.style.WARNING("=== DRY RUN (no writes) ==="))
        registry_tool_slugs: set[str] = set()
        registry_cat_slugs: set[str] = set()

        for c in registry:
            tools = c.get("tools") or []
            cat_slug = c.get("slug", "")
            registry_cat_slugs.add(cat_slug)
            self.stdout.write(f"  Category: {c.get('name')} ({len(tools)} tools) [{cat_slug}]")
            for t in tools:
                ts = t.get("slug", "")
                registry_tool_slugs.add(ts)
                self.stdout.write(f"    - {t.get('name')} [{ts}]")

        if strict_sync:
            orphan_tools = Tool.objects.exclude(slug__in=registry_tool_slugs)
            orphan_cats = ToolCategory.objects.exclude(slug__in=registry_cat_slugs)
            self.stdout.write(
                self.style.WARNING(
                    f"\n[strict-sync] Would DELETE {orphan_tools.count()} orphan tools "
                    f"and {orphan_cats.count()} orphan categories."
                )
            )
            for s in orphan_tools.values_list("slug", flat=True):
                self.stdout.write(self.style.WARNING(f"  Would delete tool: {s}"))
            for s in orphan_cats.values_list("slug", flat=True):
                self.stdout.write(self.style.WARNING(f"  Would delete category: {s}"))

        self.stdout.write(self.style.SUCCESS("=== DRY RUN complete — no changes made ==="))
