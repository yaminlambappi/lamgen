"""
Deprecated: new tools now live in config/tool_categories_ecosystem.py and merge into
config/tool_categories.TOOL_CATEGORIES. Use `seed_tools` or `seed_all` instead.

This command forwards to `seed_tools` so older scripts keep working.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deprecated: forwards to seed_tools (unified registry)."

    def add_arguments(self, parser):
        parser.add_argument("--audit", action="store_true", help="Same as --dry-run on seed_tools")
        parser.add_argument("--safe", action="store_true", help="Ignored; validation always runs in seed_tools")
        parser.add_argument("--dry-run", action="store_true", help="Forwarded to seed_tools")

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "seed_new_tools is deprecated — registry is merged into config/tool_categories.py. "
                "Running seed_tools..."
            )
        )
        dry = options.get("dry_run") or options.get("audit")
        call_command("seed_tools", dry_run=dry, stdout=self.stdout, stderr=self.stderr)
