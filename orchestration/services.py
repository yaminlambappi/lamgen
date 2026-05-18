import time
from apps.ai_providers.services.factory import ProviderFactory
from apps.ai_tools_core.services.prompt_manager import PromptManager
from apps.ai_tools_core.services.analytics_manager import AnalyticsManager
from orchestration.router import AIRouter
from orchestration.parsers import ResponseParser
from orchestration.validators import ResponseValidator
from orchestration.cache import CacheManager
from structured_outputs.schemas import get_schema

class AIOrchestrator:
    def __init__(self, tool_slug, user_input, user=None):
        self.tool_slug = tool_slug
        self.user_input = user_input
        self.user = user

    def execute(self):
        prompt = PromptManager.get_prompt(self.tool_slug, self.user_input)

        router = AIRouter()
        provider_name = router.get_provider(self.tool_slug)
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.info(f"PROVIDER NAME: {provider_name}")
        logging.info(f"PROMPT: {prompt}")
        provider = ProviderFactory.get_provider(provider_name)

        cache_manager = CacheManager()
        cache_key = f"{self.tool_slug}_{self.user_input}"
        cached_output = cache_manager.get(cache_key)

        if cached_output:
            return cached_output

        start_time = time.time()
        output = provider.generate(prompt)
        latency = int((time.time() - start_time) * 1000)

        parser = ResponseParser()
        parsed_output = parser.parse(output)

        schema = get_schema(self.tool_slug)
        if not schema:
            # Handle schema not found
            return {"error": f"Schema for tool \'{self.tool_slug}\' not found."}

        validator = ResponseValidator(schema)
        is_valid, error = validator.validate(parsed_output)

        if not is_valid:
            AnalyticsManager.track_event(
                self.user,
                "tool_usage",
                {
                    "tool_slug": self.tool_slug,
                    "provider": provider_name,
                    "latency": latency,
                    "cost": 0,  # a supposer
                    "is_successful": False,
                },
            )
            # Handle validation error
            return {"error": error}

        AnalyticsManager.track_event(
            self.user,
            "tool_usage",
            {
                "tool_slug": self.tool_slug,
                "provider": provider_name,
                "latency": latency,
                "cost": 0,  # a supposer
                "is_successful": True,
            },
        )

        cache_manager.set(cache_key, parsed_output)

        return parsed_output
