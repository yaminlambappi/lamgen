from ..models import GenerationHistory

class HistoryManager:
    @staticmethod
    def save_history(user, tool_slug, prompt, output):
        if user.is_authenticated:
            GenerationHistory.objects.create(
                user=user,
                tool_slug=tool_slug,
                prompt=prompt,
                output=output,
            )

    @staticmethod
    def get_history(user):
        if user.is_authenticated:
            return GenerationHistory.objects.filter(user=user).order_by("-created_at")
        return GenerationHistory.objects.none()
