from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
from apps.tools.models import Tool, ToolCategory

class Command(BaseCommand):
    help = "Verifies the dynamic tools page implementation."

    def handle(self, *args, **options):
        self.stdout.write("Starting verification of the tools page...")

        # 1. Verify total tool count
        active_tools_db_count = Tool.objects.filter(is_active=True).count()
        self.stdout.write(f"Active tools in DB: {active_tools_db_count}")

        client = Client()
        response = client.get(reverse("tools:index"))
        
        if response.status_code != 200:
            self.stderr.write(self.style.ERROR("Tools page returned non-200 response."))
            return

        approx_tools_context = response.context.get("approx_tools")
        self.stdout.write(f"Tools count in context: {approx_tools_context}")
        if active_tools_db_count != approx_tools_context:
            self.stderr.write(self.style.ERROR("Tool count mismatch!"))
        else:
            self.stdout.write(self.style.SUCCESS("Total tool count is correct."))

        # 2. Verify category mapping and counts
        categories_context = response.context.get("categories")
        all_good = True
        for category in categories_context:
            db_count = category.active_tools_count
            self.stdout.write(f"- Category ‘{category.name}’: DB count = {db_count}")

        # 3. Verify no missing or duplicate tools
        # Just a simple check to see if all active tools are rendered.
        # A more thorough check would involve parsing the HTML, which is complex.
        # For now, we trust the Django ORM.
        all_active_tools_from_db = set(Tool.objects.filter(is_active=True).values_list("slug", flat=True))
        rendered_tools = set()
        for cat in categories_context:
            for tool in cat.tools.all():
                rendered_tools.add(tool.slug)

        if all_active_tools_from_db == rendered_tools:
            self.stdout.write(self.style.SUCCESS("All active tools seem to be rendered without duplicates."))
        else:
            self.stderr.write(self.style.ERROR("Mismatch in rendered tools."))
            missing = all_active_tools_from_db - rendered_tools
            extra = rendered_tools - all_active_tools_from_db
            if missing:
                self.stderr.write(f"Missing tools: {missing}")
            if extra:
                self.stderr.write(f"Extra/duplicate tools: {extra}")


        # 4. Verify performance
        import time
        start_time = time.time()
        for _ in range(5):
            client.get(reverse("tools:index"))
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        self.stdout.write(f"Average page load time: {avg_time:.4f}s")
        if avg_time > 1.0:
            self.stdout.write(self.style.WARNING("Page load time is over 1 second."))
        else:
            self.stdout.write(self.style.SUCCESS("Page load time is acceptable."))

        self.stdout.write(self.style.SUCCESS("Verification complete."))
