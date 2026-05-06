
from django.core.paginator import Paginator
from django.views.generic import TemplateView

from thesis.models import StatusChoices, ThesisRequest
from tools.models import ToolUsageHistory, ToolBookmark, ToolCategory, Tool
from django.db.models import Count


class DashboardView(TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        ctx['StatusChoices'] = StatusChoices

        if self.request.user.is_authenticated:
            all_requests = ThesisRequest.objects.filter(user=self.request.user)
            ctx['total_count'] = all_requests.count()
            ctx['completed_count'] = all_requests.filter(status=StatusChoices.COMPLETED).count()
            ctx['failed_count'] = all_requests.filter(status=StatusChoices.FAILED).count()
            ctx['processing_count'] = all_requests.filter(
                status__in=[StatusChoices.PENDING, StatusChoices.PROCESSING]
            ).count()

            paginator = Paginator(all_requests, 10)
            page_number = self.request.GET.get('page', 1)
            ctx['page_obj'] = paginator.get_page(page_number)

            ctx['recent_tools'] = ToolUsageHistory.objects.filter(user=self.request.user).select_related('tool').order_by('-used_at')[:5]
            ctx['favorite_tools'] = ToolBookmark.objects.filter(user=self.request.user).select_related('tool', 'tool__category')[:10]
        else:
            ctx['total_count'] = 0
            ctx['completed_count'] = 0
            ctx['failed_count'] = 0
            ctx['processing_count'] = 0
            ctx['page_obj'] = None
            ctx['recent_tools'] = []
            ctx['favorite_tools'] = []

        # Fetch all categories to render in OS panels
        ctx['categories'] = ToolCategory.objects.annotate(tool_count=Count('tools')).prefetch_related('tools')
        
        # Simple trending heuristic (just first 8 active tools for now, can be improved based on views later)
        ctx['trending'] = Tool.objects.filter(is_active=True).select_related('category')[:8]

        return ctx
