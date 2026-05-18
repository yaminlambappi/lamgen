import google.generativeai as genai
from django.conf import settings
from .base import BaseProvider

class GeminiProvider(BaseProvider):
    def __init__(self):
        super().__init__("gemini")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-pro")

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.model.generate_content(prompt)
        completion = response.text
        
        prompt_tokens = self.get_token_count(prompt)
        completion_tokens = self.get_token_count(completion)

        self.log_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

        return completion

    def generate_stream(self, prompt: str, **kwargs):
        responses = self.model.generate_content(prompt, stream=True)
        for response in responses:
            yield response.text
            
    async def generate_async(self, prompt: str, **kwargs) -> str:
        response = await self.model.generate_content_async(prompt)
        completion = response.text
        
        prompt_tokens = self.get_token_count(prompt)
        completion_tokens = self.get_token_count(completion)

        self.log_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

        return completion

    async def generate_stream_async(self, prompt: str, **kwargs):
        responses = await self.model.generate_content_async(prompt, stream=True)
        async for response in responses:
            yield response.text
