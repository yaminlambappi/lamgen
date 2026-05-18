from django.urls import path
from .views import UnifiedAIToolView, AIToolRegistryView

urlpatterns = [
    # Registry — list all tools
    path("", AIToolRegistryView.as_view(), name="ai_tool_registry"),
    # Unified dispatch — all tools via slug
    path("<slug:slug>/", UnifiedAIToolView.as_view(), name="ai_tool_dispatch"),
]
