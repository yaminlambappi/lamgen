from django.core.management.base import BaseCommand
from apps.ai_providers.models import AIProvider

class Command(BaseCommand):
    help = "Populates the database with available AI providers."

    def handle(self, *args, **options):
        providers = {
            "gemini": {"health_score": 1}, 
            "openai": {}, 
            "anthropic": {}, 
            "openrouter": {}
        }

        AIProvider.objects.filter(name="default").delete()
        for provider_name, defaults in providers.items():
            AIProvider.objects.get_or_create(name=provider_name, defaults=defaults)

        self.stdout.write(self.style.SUCCESS("Successfully populated AI providers."))
