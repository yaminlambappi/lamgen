"""
Management command: seed_tools
Idempotently seeds ToolCategory and Tool records from config/tool_categories.py.
Usage: python manage.py seed_tools [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from tools.models import ToolCategory, Tool


class Command(BaseCommand):
    help = 'Seed tool categories and tools from TOOL_CATEGORIES config (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        try:
            from config.tool_categories import TOOL_CATEGORIES
        except ImportError:
            self.stderr.write(self.style.ERROR('config/tool_categories.py not found.'))
            return

        cat_created = cat_updated = tool_created = tool_updated = 0

        for cat_data in TOOL_CATEGORIES:
            tools_list = cat_data.pop('tools', [])
            cat_slug = cat_data['slug']

            if dry_run:
                self.stdout.write(f'[DRY RUN] Category: {cat_data["name"]} ({len(tools_list)} tools)')
                for t in tools_list:
                    self.stdout.write(f'  - {t["name"]} ({t["slug"]})')
                cat_data['tools'] = tools_list
                continue

            category, created = ToolCategory.objects.update_or_create(
                slug=cat_slug,
                defaults={**{k: v for k, v in cat_data.items() if k != 'slug'}, 'is_active': True},
            )
            if created:
                cat_created += 1
                self.stdout.write(f'  Created category: {category.name}')
            else:
                cat_updated += 1

            for tool_data in tools_list:
                tool_slug = tool_data.pop('slug')
                tool_data['category'] = category
                # Ensure description field exists
                if 'description' not in tool_data:
                    tool_data['description'] = tool_data.get('short_desc', '')

                tool, t_created = Tool.objects.update_or_create(
                    slug=tool_slug,
                    defaults=tool_data,
                )
                if t_created:
                    tool_created += 1
                else:
                    tool_updated += 1

            # Restore tools list for next iteration (pop mutates)
            cat_data['tools'] = tools_list

        if not dry_run:
            cache.delete('tool_categories_nav_v2')
            self.stdout.write(self.style.SUCCESS(
                f'Done. Categories: +{cat_created} created, ~{cat_updated} updated. '
                f'Tools: +{tool_created} created, ~{tool_updated} updated.'
            ))
