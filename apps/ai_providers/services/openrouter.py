from django.conf import settings
from .openai import OpenAIProvider

class OpenRouterProvider(OpenAIProvider):
    def __init__(self):
        super().__init__(api_key=settings.OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        self.provider_name = "openrouter"
