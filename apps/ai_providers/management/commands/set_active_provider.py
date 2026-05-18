"""
Management command: set_active_provider

Sets one provider as active (health_score=1.0) and demotes all others
(health_score=0.5). Run this after deploy to ensure the correct provider
is selected by the router.

Usage:
    python manage.py set_active_provider gemini
"""
from django.core.management.base import BaseCommand, CommandError
from apps.ai_providers.models import AIProvider

VALID_PROVIDERS = ["gemini", "openai", "anthropic", "openrouter"]


class Command(BaseCommand):
    help = "Set one AI provider as active (health_score=1.0), demote all others."

    def add_arguments(self, parser):
        parser.add_argument(
            "provider",
            type=str,
            choices=VALID_PROVIDERS,
            help=f"Provider to activate. One of: {', '.join(VALID_PROVIDERS)}",
        )

    def handle(self, *args, **options):
        name = options["provider"]
        if name not in VALID_PROVIDERS:
            raise CommandError(f"Unknown provider '{name}'. Choose from: {VALID_PROVIDERS}")

        AIProvider.objects.get_or_create(name=name, defaults={"health_score": 1.0})
        AIProvider.objects.filter(name=name).update(health_score=1.0)
        AIProvider.objects.exclude(name=name).update(health_score=0.5)

        self.stdout.write(self.style.SUCCESS(f"Active provider set to '{name}'."))
