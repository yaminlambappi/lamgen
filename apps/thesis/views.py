import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .forms import UploadForm
from .models import StatusChoices, ThesisRequest
from .tasks import STAGE_PROGRESS, get_stage

logger = logging.getLogger(__name__)


class ThesisOwnerMixin:
    """Mixin that fetches a ThesisRequest and enforces ownership."""

    def get_thesis(self, pk):
        obj = get_object_or_404(ThesisRequest, pk=pk)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj


class UploadView(LoginRequiredMixin, View):
    """Handle PDF upload and ThesisRequest creation."""

    def get(self, request):
        form = UploadForm()
        return render(request, 'thesis/upload.html', {'form': form})

    def post(self, request):
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Create ThesisRequest and save file
            thesis = ThesisRequest.objects.create(
                user=request.user,
                title=form.cleaned_data['title'],
                input_file=form.cleaned_data['pdf_file'],
                status=StatusChoices.PENDING,
            )

            # Enqueue Celery task
            from .tasks import process_thesis_task
            process_thesis_task.delay(thesis.pk)

            messages.success(request, f'Your thesis "{thesis.title}" has been submitted for generation.')
            return redirect('thesis:status', pk=thesis.pk)

        return render(request, 'thesis/upload.html', {'form': form})


class ThesisStatusView(LoginRequiredMixin, ThesisOwnerMixin, View):
    """HTML status tracking page."""

    def get(self, request, pk):
        thesis = self.get_thesis(pk)
        return render(request, 'thesis/status.html', {'thesis': thesis})


class ThesisStatusJsonView(LoginRequiredMixin, ThesisOwnerMixin, View):
    """JSON endpoint for polling thesis generation status."""

    def get(self, request, pk):
        thesis = self.get_thesis(pk)

        # Determine progress from Redis stage or fall back to status
        stage = get_stage(thesis.pk)
        if stage and stage in STAGE_PROGRESS:
            progress = STAGE_PROGRESS[stage]
        elif thesis.status == StatusChoices.COMPLETED:
            progress = 100
        elif thesis.status == StatusChoices.FAILED:
            progress = 0
        elif thesis.status == StatusChoices.PROCESSING:
            progress = 10
        else:
            progress = 0

        return JsonResponse({
            'status': thesis.status,
            'progress_percentage': progress,
            'title': thesis.title,
            'error_message': thesis.error_message if thesis.status == StatusChoices.FAILED else '',
        })


class ThesisDownloadView(LoginRequiredMixin, ThesisOwnerMixin, View):
    """Serve the output PDF for download."""

    def get(self, request, pk):
        from django.http import FileResponse
        thesis = self.get_thesis(pk)
        if thesis.status != StatusChoices.COMPLETED:
            raise Http404('Thesis is not yet completed.')
        if not thesis.output_file:
            raise Http404('Output file not found.')

        safe_title = ''.join(c for c in thesis.title if c.isalnum() or c in ' -_')[:50]
        filename = f'{safe_title}.pdf' if safe_title else 'thesis.pdf'

        response = FileResponse(
            thesis.output_file.open('rb'),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ThesisPreviewView(LoginRequiredMixin, ThesisOwnerMixin, View):
    """HTML preview of the generated thesis."""

    def get(self, request, pk):
        import markdown as md
        thesis = self.get_thesis(pk)
        if thesis.status != StatusChoices.COMPLETED:
            raise Http404('Thesis is not yet completed.')

        thesis_html = md.markdown(
            thesis.generated_thesis or '',
            extensions=['extra', 'toc', 'nl2br'],
        )
        return render(request, 'thesis/preview.html', {
            'thesis': thesis,
            'thesis_html': thesis_html,
        })


class ThesisDeleteView(LoginRequiredMixin, ThesisOwnerMixin, View):
    """Delete a ThesisRequest and all associated files."""

    def delete(self, request, pk):
        import os
        thesis = self.get_thesis(pk)

        # Delete input file from disk
        if thesis.input_file:
            try:
                path = thesis.input_file.path
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning('Could not delete input file for thesis %d: %s', pk, e)

        # Delete output file from disk
        if thesis.output_file:
            try:
                path = thesis.output_file.path
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning('Could not delete output file for thesis %d: %s', pk, e)

        # Delete DB record (cascades to ThesisChunk)
        thesis.delete()
        return JsonResponse({'success': True})
