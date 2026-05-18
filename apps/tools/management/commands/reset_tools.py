"""
Management command: reset_tools

Clears all Tool and ToolCategory records, then re-runs seed_tools --strict-sync
for a clean-slate tool state.

Usage:
    python manage.py reset_tools           # prompts for confirmation
    python manage.py reset_tools --yes     # skip prompt (CI/CD use only)

WARNING: This deletes all tool data. Run verify_tools after to confirm parity.
"""
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.tools.models import Tool, ToolCategory


class Command(BaseCommand):
    help = (
        "DANGER: Wipes all Tool and ToolCategory rows and re-seeds from the registry. "
        "Pass --yes to skip the confirmation prompt (for CI/CD pipelines)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Skip confirmation prompt. Required in non-interactive environments.",
        )

    def handle(self, *args, **options):
        yes = options["yes"]

        # ------------------------------------------------------------------
        # Safety guard: require explicit --yes in production environments
        # ------------------------------------------------------------------
        django_env = os.environ.get("DJANGO_SETTINGS_MODULE", "")
        is_production = "production" in django_env or os.environ.get("LAMGEN_ENV", "") == "production"

        if is_production and not yes:
            self.stderr.write(
                self.style.ERROR(
                    "ABORTED: reset_tools detected a production environment.\n"
                    "Pass --yes explicitly to confirm you want to wipe and reseed tools in production."
                )
            )
            return

        if not yes:
            tool_count = Tool.objects.count()
            cat_count = ToolCategory.objects.count()
            self.stdout.write(
                self.style.WARNING(
                    f"\nThis will DELETE {tool_count} tool(s) and {cat_count} category(ies) "
                    "from the database, then re-seed from the registry.\n"
                )
            )
            confirm = input("Type 'yes' to continue, anything else to abort: ").strip().lower()
            if confirm != "yes":
                self.stdout.write("Aborted.")
                return

        # ------------------------------------------------------------------
        # Wipe
        # ------------------------------------------------------------------
        deleted_tools, _ = Tool.objects.all().delete()
        deleted_cats, _ = ToolCategory.objects.all().delete()
        self.stdout.write(
            self.style.WARNING(
                f"Deleted {deleted_tools} tool(s) and {deleted_cats} category(ies)."
            )
        )

        # ------------------------------------------------------------------
        # Reseed with strict sync
        # ------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("Re-seeding from registry (--strict-sync)..."))
        call_command("seed_tools", strict_sync=True)

        self.stdout.write(self.style.SUCCESS("\nreset_tools complete. Run verify_tools to confirm parity."))
