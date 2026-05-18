import anthropic
from django.conf import settings
from .base import BaseProvider

class AnthropicProvider(BaseProvider):
    def __init__(self, timeout=None):
        super().__init__("anthropic")
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=timeout or settings.AI_PROVIDER_TIMEOUT,
        )
        self.async_client = anthropic.AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=timeout or settings.AI_PROVIDER_TIMEOUT,
        )

    def generate(self, prompt: str, **kwargs) -> str:
        model = kwargs.get("model", settings.CLAUDE_MODEL)
        max_tokens = kwargs.get("max_tokens", settings.CLAUDE_MAX_TOKENS)

        message = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        completion = "".join([block.text for block in message.content])
        prompt_tokens = message.usage.input_tokens
        completion_tokens = message.usage.output_tokens

        self.log_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

        return completion

    def generate_stream(self, prompt: str, **kwargs):
        model = kwargs.get("model", settings.CLAUDE_MODEL)
        max_tokens = kwargs.get("max_tokens", settings.CLAUDE_MAX_TOKENS)

        with self.client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        ) as stream:
            for text in stream.text_stream:
                yield text

    async def generate_async(self, prompt: str, **kwargs) -> str:
        model = kwargs.get("model", settings.CLAUDE_MODEL)
        max_tokens = kwargs.get("max_tokens", settings.CLAUDE_MAX_TOKENS)

        message = await self.async_client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        completion = "".join([block.text for block in message.content])
        prompt_tokens = message.usage.input_tokens
        completion_tokens = message.usage.output_tokens

        self.log_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

        return completion

    async def generate_stream_async(self, prompt: str, **kwargs):
        model = kwargs.get("model", settings.CLAUDE_MODEL)
        max_tokens = kwargs.get("max_tokens", settings.CLAUDE_MAX_TOKENS)

        async with self.async_client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        ) as stream:
            async for text in stream.text_stream:
                yield text
