from orchestration.provider_adapters.anthropic_adapter import AnthropicAdapter
from orchestration.provider_adapters.openai_adapter import OpenAIAdapter
from orchestration.provider_adapters.gemini_adapter import GeminiAdapter
from orchestration.provider_adapters.openrouter_adapter import OpenRouterAdapter

class ProviderFactory:
    PROVIDERS = {
        "anthropic": AnthropicAdapter,
        "openai": OpenAIAdapter,
        "gemini": GeminiAdapter,
        "openrouter": OpenRouterAdapter,
    }
    DEFAULT_PROVIDER_ORDER = ["gemini", "openai", "anthropic", "openrouter"]

    @classmethod
    def get_provider(cls, provider_name: str = None):
        if not provider_name:
            provider_name = cls.DEFAULT_PROVIDER_ORDER[0]

        provider_class = cls.PROVIDERS.get(provider_name)
        if not provider_class:
            raise ValueError(f"Invalid provider: {provider_name}")
        try:
            return provider_class()
        except Exception as e:
            # In a real application, you would want to log this error.
            print(f"Provider {provider_name} failed with error: {e}")
            raise RuntimeError("AI provider failed. Please check your API keys and provider configurations.")
