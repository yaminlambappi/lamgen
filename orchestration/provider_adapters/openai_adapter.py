from .base_adapter import BaseProviderAdapter
from apps.ai_providers.services.openai import OpenAIProvider

class OpenAIAdapter(BaseProviderAdapter):
    def __init__(self):
        self.openai_service = OpenAIProvider()

    def generate(self, prompt):
        return self.openai_service.generate(prompt)
