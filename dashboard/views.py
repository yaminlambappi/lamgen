from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.views.generic import TemplateView

from thesis.models import StatusChoices, ThesisRequest


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_requests = ThesisRequest.objects.filter(user=self.request.user)

        # Stats
        ctx['total_count'] = all_requests.count()
        ctx['completed_count'] = all_requests.filter(status=StatusChoices.COMPLETED).count()
        ctx['failed_count'] = all_requests.filter(status=StatusChoices.FAILED).count()
        ctx['processing_count'] = all_requests.filter(
            status__in=[StatusChoices.PENDING, StatusChoices.PROCESSING]
        ).count()

        # Paginate
        paginator = Paginator(all_requests, 10)
        page_number = self.request.GET.get('page', 1)
        ctx['page_obj'] = paginator.get_page(page_number)
        ctx['StatusChoices'] = StatusChoices

        return ctx
