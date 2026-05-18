from .base_adapter import BaseProviderAdapter
from apps.ai_providers.services.openrouter import OpenRouterProvider

class OpenRouterAdapter(BaseProviderAdapter):
    def __init__(self):
        self.openrouter_service = OpenRouterProvider()

    def generate(self, prompt):
        return self.openrouter_service.generate(prompt)
