import logging
from .provider import generate_ai_response
from django.core.cache import cache

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def execute_prompt(tool_slug: str, context: dict, prompt_template: str) -> str:
        """
        Executes a prompt through the centralized AI provider.
        Supports caching and structured output.
        """
        try:
            # Build the prompt
            prompt = prompt_template.format(**context)
            
            # Simple caching for identical requests
            cache_key = f"ai_response_{hash(prompt)}"
            cached = cache.get(cache_key)
            if cached:
                return cached
                
            response_text = generate_ai_response(prompt)
            
            # Cache successful response for 1 hour
            cache.set(cache_key, response_text, 3600)
            return response_text
            
        except Exception as e:
            logger.error(f"AI Service Execution Failed for {tool_slug}: {str(e)}")
            return "An error occurred while generating the AI response. Please try again later."
