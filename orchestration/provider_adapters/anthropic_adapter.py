from .base_adapter import BaseProviderAdapter
from apps.ai_providers.services.anthropic import AnthropicProvider

class AnthropicAdapter(BaseProviderAdapter):
    def __init__(self):
        self.anthropic_service = AnthropicProvider()

    def generate(self, prompt):
        return self.anthropic_service.generate(prompt)
