import openai
from django.conf import settings
from .base import BaseProvider

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key=None, base_url=None, timeout=None):
        super().__init__("openai")
        self.client = openai.OpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url,
            timeout=timeout or settings.AI_PROVIDER_TIMEOUT,
        )
        self.async_client = openai.AsyncOpenAI(
            api_key=api_key or settings.OPENAI_API_KEY,
            base_url=base_url,
            timeout=timeout or settings.AI_PROVIDER_TIMEOUT,
        )

    def generate(self, prompt: str, **kwargs) -> str:
        model = kwargs.get("model", "gpt-3.5-turbo")

        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        
        completion = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        self.log_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

        return completion

    def generate_stream(self, prompt: str, **kwargs):
        model = kwargs.get("model", "gpt-3.5-turbo")

        stream = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    async def generate_async(self, prompt: str, **kwargs) -> str:
        model = kwargs.get("model", "gpt-3.5-turbo")

        response = await self.async_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        
        completion = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        self.log_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

        return completion

    async def generate_stream_async(self, prompt: str, **kwargs):
        model = kwargs.get("model", "gpt-3.5-turbo")

        stream = await self.async_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
