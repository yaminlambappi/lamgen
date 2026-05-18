from .base_adapter import BaseProviderAdapter
from apps.ai_providers.services.gemini import GeminiProvider

class GeminiAdapter(BaseProviderAdapter):
    def __init__(self):
        self.gemini_service = GeminiProvider()

    def generate(self, prompt):
        return self.gemini_service.generate(prompt)
