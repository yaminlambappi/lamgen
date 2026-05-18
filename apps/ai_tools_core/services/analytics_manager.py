"""
AnalyticsManager — lightweight stub.

Tracks AI tool usage events. Writes to GenerationHistory when a real user is
present; silently no-ops for anonymous requests or if the DB is unavailable.
Analytics must never break the response path.
"""
import logging

logger = logging.getLogger("ai_service")


class AnalyticsManager:
    @staticmethod
    def track_event(user, event_type: str, payload: dict) -> None:
        """
        Record a tool usage event.

        Args:
            user:        Django user instance or None for anonymous.
            event_type:  String label, e.g. "tool_usage".
            payload:     Dict with keys: tool_slug, provider, latency, cost, is_successful.
        """
        try:
            # Only persist when we have an authenticated user (model requires FK)
            if not (user and getattr(user, "is_authenticated", False)):
                return

            from apps.ai_tools_core.models import GenerationHistory
            GenerationHistory.objects.create(
                user=user,
                tool_slug=payload.get("tool_slug", ""),
                prompt="",   # prompt not passed here; extend payload if needed
                output="",   # output not passed here; extend payload if needed
            )
        except Exception as exc:
            # Analytics must never propagate — log at debug level and move on.
            logger.debug("analytics_write_skipped reason=%s", exc)
