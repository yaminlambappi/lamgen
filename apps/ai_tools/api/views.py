"""
Unified AI Tool API views.

All AI tools are served through a single endpoint:
  POST /api/tools/<slug>/

Request body (JSON):
  {
    "prompt": "<user input>",       # required
    "provider": "gemini"            # optional — overrides auto-selection
  }

Response (success):
  {
    "ok": true,
    "slug": "<slug>",
    "result": <string | object>,
    "format": "text" | "json",
    "latency_ms": 123,
    "cached": false
  }

Response (error):
  {
    "ok": false,
    "code": "tool_not_found" | "validation_error" | "rate_limited" | "provider_error" | ...,
    "message": "<human-readable explanation>"
  }
"""

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.ai_tools.registry import get_tool, get_all_tools, get_tools_by_category, list_slugs
from orchestration.ai_service import AIService, AIServiceError

logger = logging.getLogger("ai_service")


class UnifiedAIToolView(APIView):
    """
    Single dispatch view for every registered AI tool.
    Route: POST /api/tools/<slug>/
    """
    permission_classes = [AllowAny]

    def post(self, request, slug: str, *args, **kwargs):
        service = AIService(user=request.user)
        try:
            result = service.execute(slug, request.data)
            return Response(result, status=200)
        except AIServiceError as exc:
            logger.warning(
                "tool_request_failed slug=%s code=%s message=%s user=%s",
                slug, exc.code, exc.message,
                getattr(request.user, "id", "anon"),
            )
            return Response(
                {"ok": False, "code": exc.code, "message": exc.message},
                status=exc.status,
            )
        except Exception as exc:
            logger.exception("unexpected_error slug=%s", slug)
            return Response(
                {"ok": False, "code": "internal_error", "message": "An unexpected error occurred."},
                status=500,
            )


class AIToolRegistryView(APIView):
    """
    GET /api/tools/
    Returns the full list of registered AI tools with their metadata.
    Supports ?category=<category> filter.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        category = request.query_params.get("category")
        if category:
            tools = get_tools_by_category(category)
        else:
            tools = get_all_tools()

        # Expose only the fields safe/useful for the client
        serialized = [
            {
                "slug": t["slug"],
                "name": t["name"],
                "category": t["category"],
                "input_fields": t.get("input_fields", []),
                "response_format": t.get("response_format", "text"),
            }
            for t in tools
        ]
        return Response({"ok": True, "count": len(serialized), "tools": serialized})
