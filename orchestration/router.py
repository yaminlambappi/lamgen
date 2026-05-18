import logging

from django.conf import settings

from apps.ai_providers.models import AIProvider

logger = logging.getLogger("ai_service")

# Ordered preference when health scores are tied — first provider with a
# configured credential wins.
_KEY_MAP = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def _gemini_is_configured() -> bool:
    """
    Gemini is considered configured if:
      - VERTEX_AI=true + GOOGLE_CLOUD_PROJECT_ID is set, OR
      - GEMINI_API_KEY is non-empty (any format — validation happens in the provider)
    """
    if getattr(settings, "VERTEX_AI", False) and getattr(settings, "GOOGLE_CLOUD_PROJECT_ID", ""):
        return True
    return bool(getattr(settings, "GEMINI_API_KEY", ""))


class AIRouter:
    def get_provider(self, tool_slug: str = None) -> str:
        """
        Select the best available provider for a given tool.

        Priority:
          1. Highest health_score in DB.
          2. On tie, first provider in _KEY_MAP order that has a non-empty API key.
          3. Falls back to 'gemini' if DB is empty.
        """
        providers = list(AIProvider.objects.order_by("-health_score").values("name", "health_score"))

        if not providers:
            logger.warning("router_no_providers_in_db falling_back=gemini")
            return "gemini"

        top_score = providers[0]["health_score"]
        tied = [p["name"] for p in providers if p["health_score"] == top_score]

        # Among tied providers, pick the first one that has a configured credential
        for name in _KEY_MAP:
            if name not in tied:
                continue
            if name == "gemini":
                if _gemini_is_configured():
                    logger.info("router_selected provider=%s score=%s", name, top_score)
                    return name
            else:
                key_setting = _KEY_MAP[name]
                if getattr(settings, key_setting, ""):
                    logger.info("router_selected provider=%s score=%s", name, top_score)
                    return name

        # Fallback: return highest-scored provider regardless of key presence
        selected = providers[0]["name"]
        logger.warning("router_no_key_found falling_back=%s", selected)
        return selected
