from abc import ABC, abstractmethod
import tiktoken
from ..utils.decorators import with_retry
from ..utils.async_decorators import with_async_retry
from .cache import cache_generation, cache_generation_async
from ..models import AIProviderUsage

class BaseProvider(ABC):
    def __init__(self, provider_name):
        self.provider_name = provider_name

    @abstractmethod
    @with_retry()
    @cache_generation()
    def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    @with_retry()
    def generate_stream(self, prompt: str, **kwargs):
        pass

    @abstractmethod
    @with_async_retry()
    @cache_generation_async()
    async def generate_async(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    @with_async_retry()
    async def generate_stream_async(self, prompt: str, **kwargs):
        pass

    def get_token_count(self, text: str) -> int:
        # This is a general estimation. Each provider might have its own way of counting tokens.
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4 # Fallback to character count

    def log_usage(self, prompt_tokens: int, completion_tokens: int, cost: float = 0.0):
        AIProviderUsage.objects.create(
            provider_name=self.provider_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
        )
