
from django.core.management.base import BaseCommand
from apps.ai_tools.services.career_tool_service import CareerToolService
from apps.ai_tools.services.writing_tool_service import WritingToolService
from apps.ai_tools.services.seo_tool_service import SEOToolService
from apps.ai_tools.services.social_tool_service import SocialToolService
from apps.ai_tools.services.developer_tool_service import DeveloperToolService
from apps.ai_tools.services.education_tool_service import EducationToolService
from apps.ai_tools.services.base_tool_service import BaseToolService
from ai_tool_filter import get_ai_tools_only

class Command(BaseCommand):
    help = "Verifies all AI tools by calling their services directly."

    def handle(self, *args, **options):
        ai_tools = get_ai_tools_only()

        for tool_slug in ai_tools:
            self.stdout.write(f"Verifying tool: {tool_slug}")
            service, payload = self.get_service_and_payload(tool_slug)

            if service:
                try:
                    result = service.execute(tool_slug, payload)
                    self.stdout.write(self.style.SUCCESS(f"  Result: {result}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error: {e}"))
            else:
                self.stdout.write(self.style.WARNING("  No service found"))

    def get_service_and_payload(self, tool_slug):
        # This is a simplified version. A more robust solution would
        # map tool slugs to services and payloads more dynamically.
        if tool_slug in ["ai-resume-builder", "ats-checker", "cover-letter-generator"]:
            return CareerToolService(user=None), {"prompt": "hello"}
        elif tool_slug in ["linkedin-headline-generator", "linkedin-post-generator"]:
            return SocialToolService(user=None), {"prompt": "hello"}
        # Add other services here
        
        return None, None
