from apps.ai_providers.models import AIProvider

class AIRouter:
    def get_provider(self, tool_slug):
        # For now, select the provider with the highest health score
        best_provider = AIProvider.objects.order_by("-health_score").first()
        if best_provider:
            return best_provider.name
        return "default"
