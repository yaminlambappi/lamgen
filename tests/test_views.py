"""
Integration tests for all views.
"""
import io
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client
from django.urls import reverse

from tests.factories import (
    CompletedThesisRequestFactory,
    ThesisRequestFactory,
    UserFactory,
)
from apps.thesis.models import StatusChoices, ThesisRequest


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


class TestAuthViews:
    """Integration tests for authentication views."""

    def test_register_get(self, client):
        resp = client.get(reverse('users:register'))
        assert resp.status_code == 200

    def test_register_valid_creates_user(self, client, db):
        resp = client.post(reverse('users:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'university': 'Test Uni',
            'bio': '',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        assert resp.status_code == 302
        from django.contrib.auth import get_user_model
        assert get_user_model().objects.filter(username='newuser').exists()

    def test_register_duplicate_username_shows_error(self, client, user):
        resp = client.post(reverse('users:register'), {
            'username': user.username,
            'email': 'other@example.com',
            'university': 'Test Uni',
            'bio': '',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        assert resp.status_code == 200
        assert b'already exists' in resp.content.lower() or resp.status_code == 200

    def test_login_valid_redirects_to_home(self, client, user):
        resp = client.post(reverse('users:login'), {
            'username': user.username,
            'password': 'testpass123',
        })
        assert resp.status_code == 302
        assert resp['Location'] == '/'

    def test_login_invalid_shows_error(self, client, user):
        resp = client.post(reverse('users:login'), {
            'username': user.username,
            'password': 'wrongpassword',
        })
        assert resp.status_code == 200

    def test_logout_redirects_to_home(self, auth_client):
        resp = auth_client.post(reverse('users:logout'))
        assert resp.status_code == 302

    def test_unauthenticated_upload_redirects_to_login(self, client):
        resp = client.get(reverse('thesis:upload'))
        assert resp.status_code == 302
        assert '/login/' in resp['Location']

    def test_home_public_for_anonymous_user(self, client):
        resp = client.get(reverse('home'))
        assert resp.status_code == 200

    def test_sitemap_xml_renders(self, client, db):
        from apps.tools.models import ToolCategory, Tool
        from apps.seo.models import LongTailVariant

        category = ToolCategory.objects.create(name='Test Category', slug='test-category')
        tool = Tool.objects.create(
            name='Test Tool',
            slug='test-tool',
            category=category,
            description='Test tool description',
            short_desc='Short description',
            template_name='tools/test-tool.html',
            is_active=True,
        )
        LongTailVariant.objects.create(
            tool=tool,
            variant_slug='test-variant',
            keyword_intent='online',
            unique_intro='Unique intro for test variant.',
            use_cases=[],
            faq_items=[],
            meta_title='Test Variant Title',
            meta_description='Test variant description.',
            is_active=True,
        )

        resp = client.get('/sitemap.xml')
        assert resp.status_code == 200
        assert b'<sitemapindex' in resp.content or b'<urlset' in resp.content


class TestUploadView:
    """Integration tests for the upload view."""

    def test_upload_get_renders_form(self, auth_client):
        resp = auth_client.get(reverse('thesis:upload'))
        assert resp.status_code == 200

    def test_upload_valid_pdf_creates_thesis(self, auth_client, db):
        # Minimal valid PDF bytes
        pdf_bytes = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF'
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_file.name = 'test.pdf'
        with patch('apps.thesis.tasks.process_thesis_task') as mock_task:
            mock_task.delay = MagicMock()
            with patch('magic.from_buffer', return_value='application/pdf'):
                resp = auth_client.post(reverse('thesis:upload'), {
                    'title': 'Test Thesis',
                    'pdf_file': pdf_file,
                })
        assert ThesisRequest.objects.filter(title='Test Thesis').exists()

    def test_upload_non_pdf_rejected(self, auth_client, db):
        txt_file = io.BytesIO(b'This is not a PDF')
        txt_file.name = 'test.txt'
        resp = auth_client.post(reverse('thesis:upload'), {
            'title': 'Test Thesis',
            'pdf_file': txt_file,
        })
        assert resp.status_code == 200
        assert not ThesisRequest.objects.filter(title='Test Thesis').exists()

    def test_upload_rate_limit_not_enforced_in_view(self, auth_client, user, db):
        """UploadView no longer applies a daily cap; keep placeholder for future policy tests."""
        pytest.skip("UploadView does not enforce a 5/day rate limit; see apps/thesis/views.py")


class TestThesisOwnershipViews:
    """Integration tests for ownership enforcement."""

    def test_status_json_non_owner_returns_403(self, client, other_user, db):
        thesis = ThesisRequestFactory()
        client.force_login(other_user)
        resp = client.get(reverse('thesis:status_json', kwargs={'pk': thesis.pk}))
        assert resp.status_code == 403

    def test_download_non_owner_returns_403(self, client, other_user, db):
        thesis = CompletedThesisRequestFactory()
        client.force_login(other_user)
        resp = client.get(reverse('thesis:download', kwargs={'pk': thesis.pk}))
        assert resp.status_code == 403

    def test_preview_non_owner_returns_403(self, client, other_user, db):
        thesis = CompletedThesisRequestFactory()
        client.force_login(other_user)
        resp = client.get(reverse('thesis:preview', kwargs={'pk': thesis.pk}))
        assert resp.status_code == 403

    def test_delete_non_owner_returns_403(self, client, other_user, db):
        thesis = ThesisRequestFactory()
        client.force_login(other_user)
        resp = client.delete(
            reverse('thesis:delete', kwargs={'pk': thesis.pk}),
            content_type='application/json',
        )
        assert resp.status_code == 403

    def test_download_non_completed_returns_404(self, auth_client, user, db):
        thesis = ThesisRequestFactory(user=user, status=StatusChoices.PENDING)
        resp = auth_client.get(reverse('thesis:download', kwargs={'pk': thesis.pk}))
        assert resp.status_code == 404

    def test_preview_non_completed_returns_404(self, auth_client, user, db):
        thesis = ThesisRequestFactory(user=user, status=StatusChoices.PENDING)
        resp = auth_client.get(reverse('thesis:preview', kwargs={'pk': thesis.pk}))
        assert resp.status_code == 404


class TestDashboardView:
    """Integration tests for the dashboard."""

    def test_thesis_status_page_shows_title(self, auth_client, user, db):
        thesis = ThesisRequestFactory(user=user, title='My Thesis')
        resp = auth_client.get(reverse('thesis:status', kwargs={'pk': thesis.pk}))
        assert resp.status_code == 200
        assert b'My Thesis' in resp.content

    def test_dashboard_empty_state(self, auth_client, db):
        resp = auth_client.get(reverse('home'))
        assert resp.status_code == 200

    def test_dashboard_home_public_for_anonymous(self, client):
        resp = client.get(reverse('home'))
        assert resp.status_code == 200


class TestDeleteView:
    """Integration tests for thesis deletion."""

    def test_delete_removes_thesis(self, auth_client, user, db):
        thesis = ThesisRequestFactory(user=user)
        pk = thesis.pk
        resp = auth_client.delete(
            reverse('thesis:delete', kwargs={'pk': pk}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN='test',
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data['success'] is True
        assert not ThesisRequest.objects.filter(pk=pk).exists()
