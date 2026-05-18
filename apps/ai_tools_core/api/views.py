from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from apps.ai_providers.services import ProviderFactory
from ..services.prompt_manager import PromptManager
from ..services.history_manager import HistoryManager
from ..services.analytics_manager import AnalyticsManager

class BaseAIToolView(APIView):
    permission_classes = [IsAuthenticated]
    tool_slug = None # Should be overridden by subclasses

    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        provider_name = request.data.get("provider")
        stream = request.data.get("stream", False)

        if not self.tool_slug:
            return Response({"error": "Tool slug not configured"}, status=500)

        prompt = PromptManager.get_prompt(self.tool_slug, user_input)
        provider = ProviderFactory.get_provider(provider_name)

        AnalyticsManager.track_event(request.user, f"{self.tool_slug}_generation_started", {"provider": provider.provider_name})

        if stream:
            response = StreamingHttpResponse(provider.generate_stream(prompt, **request.data))
            # In a real app, you would want to save the history after the stream is finished.
            # For simplicity, we are not doing it here.
        else:
            output = provider.generate(prompt, **request.data)
            HistoryManager.save_history(request.user, self.tool_slug, prompt, output)
            response = Response({"output": output})
        
        AnalyticsManager.track_event(request.user, f"{self.tool_slug}_generation_finished", {"provider": provider.provider_name})

        return response
