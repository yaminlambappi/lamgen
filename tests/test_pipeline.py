"""
Integration tests for the full thesis generation pipeline and cleanup task.
"""
import os
import tempfile
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from tests.factories import ThesisRequestFactory, UserFactory
from thesis.models import StatusChoices, ThesisRequest


class TestProcessThesisTask:
    """Integration test for the full pipeline with mocked services."""

    def test_pipeline_pending_to_completed(self, db, tmp_path):
        """Full pipeline: PENDING → PROCESSING → COMPLETED with all services mocked."""
        from thesis.tasks import process_thesis_task

        user = UserFactory()
        thesis = ThesisRequestFactory(user=user, status=StatusChoices.PENDING)

        # Create a fake input file
        fake_pdf = tmp_path / 'test.pdf'
        fake_pdf.write_bytes(b'%PDF-1.4\n%%EOF')

        # Patch the input_file path
        thesis.input_file.name = str(fake_pdf)
        thesis.save()

        mock_pdf_bytes = b'%PDF-1.4\nfake pdf content\n%%EOF'

        with patch('thesis.tasks.PDFService.process', return_value=['chunk1', 'chunk2']), \
             patch('thesis.tasks.LLMService') as mock_llm_cls, \
             patch('thesis.tasks.ThesisPDFGenerator.render', return_value=mock_pdf_bytes), \
             patch('thesis.tasks.set_stage'), \
             patch('os.makedirs'), \
             patch('builtins.open', MagicMock()):
            mock_llm = MagicMock()
            mock_llm.generate_thesis.return_value = '# Abstract\n\nTest thesis.'
            mock_llm_cls.return_value = mock_llm

            # Run task synchronously
            process_thesis_task(thesis.pk)

        thesis.refresh_from_db()
        assert thesis.status == StatusChoices.COMPLETED
        assert thesis.generated_thesis == '# Abstract\n\nTest thesis.'

    def test_pipeline_sets_failed_on_error(self, db, tmp_path):
        """Pipeline sets FAILED status when an error occurs."""
        from thesis.tasks import process_thesis_task

        user = UserFactory()
        thesis = ThesisRequestFactory(user=user, status=StatusChoices.PENDING)

        fake_pdf = tmp_path / 'test.pdf'
        fake_pdf.write_bytes(b'%PDF-1.4\n%%EOF')
        thesis.input_file.name = str(fake_pdf)
        thesis.save()

        with patch('thesis.tasks.PDFService.process', side_effect=Exception('PDF extraction failed')), \
             patch('thesis.tasks.set_stage'):
            process_thesis_task(thesis.pk)

        thesis.refresh_from_db()
        assert thesis.status == StatusChoices.FAILED
        assert 'PDF extraction failed' in thesis.error_message


class TestCleanupOldUploads:
    """Integration tests for the cleanup_old_uploads task."""

    def test_cleanup_deletes_old_input_files(self, db, tmp_path):
        """Old input files (>24h) are deleted and input_file set to None."""
        from thesis.tasks import cleanup_old_uploads

        user = UserFactory()
        thesis = ThesisRequestFactory(user=user)

        # Create a fake file
        fake_file = tmp_path / 'old_upload.pdf'
        fake_file.write_bytes(b'%PDF-1.4\n%%EOF')
        thesis.input_file.name = str(fake_file)
        thesis.save()

        # Backdate created_at to 25 hours ago
        old_time = timezone.now() - timedelta(hours=25)
        ThesisRequest.objects.filter(pk=thesis.pk).update(created_at=old_time)

        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            count = cleanup_old_uploads()

        assert count == 1
        thesis.refresh_from_db()
        assert not thesis.input_file

    def test_cleanup_skips_recent_uploads(self, db):
        """Recent uploads (<24h) are not deleted."""
        from thesis.tasks import cleanup_old_uploads

        user = UserFactory()
        thesis = ThesisRequestFactory(user=user)
        thesis.input_file.name = 'uploads/recent.pdf'
        thesis.save()

        with patch('os.remove') as mock_remove:
            count = cleanup_old_uploads()

        assert count == 0
        mock_remove.assert_not_called()
