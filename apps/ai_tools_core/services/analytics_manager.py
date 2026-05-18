from apps.analytics.models import ToolUsage

class AnalyticsManager:
    @staticmethod
    def track_event(user, event_name, data=None):
        if event_name == "tool_usage":
            ToolUsage.objects.create(
                user=user,
                tool_slug=data.get("tool_slug"),
                provider=data.get("provider"),
                latency=data.get("latency"),
                cost=data.get("cost"),
                is_successful=data.get("is_successful"),
            )
        else:
            # For other events, we can still print them for now
            print(f"[ANALYTICS] User: {user.username if user.is_authenticated else 'Anonymous'}, Event: {event_name}, Data: {data}")
