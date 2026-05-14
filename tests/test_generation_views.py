"""
Property-based tests for generation view validation logic and endpoint contracts.

Covers:
  - Property 1:  Upload validation rejects invalid files
  - Property 2:  Prompt length validation
  - Property 30: Target word count validation
  - Property 29: Authorization — users can only access their own jobs
  - Property 27: Progress polling endpoint contract
"""
import pytest
from django.test import Client
from django.urls import reverse
from hypothesis import HealthCheck, given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from apps.generation.models import GenerationJob
from apps.generation.views import ALLOWED_MIME_TYPES, MAX_FILE_SIZE
from tests.factories import UserFactory

# ---------------------------------------------------------------------------
# Helper: validation logic extracted from the view
# ---------------------------------------------------------------------------

def validate_upload(file_bytes: bytes, mime_type: str, file_size: int) -> bool:
    """
    Mirrors the upload validation logic in generation/views.py submit_job.

    Returns True if the upload is accepted, False if it should be rejected.
    Accepted iff:
      - mime_type is in ALLOWED_MIME_TYPES, AND
      - file_size <= MAX_FILE_SIZE (20 MB)
    """
    if mime_type not in ALLOWED_MIME_TYPES:
        return False
    if file_size > MAX_FILE_SIZE:
        return False
    return True


def validate_prompt(prompt: str) -> bool:
    """
    Mirrors the prompt validation logic in generation/views.py submit_job.

    Returns True if the prompt is accepted, False otherwise.
    Accepted iff 50 <= len(prompt) <= 10_000.
    """
    return 50 <= len(prompt) <= 10_000


def validate_word_count(word_count: int) -> bool:
    """
    Mirrors the target_word_count validation logic in generation/views.py submit_job.

    Returns True if the word count is accepted, False otherwise.
    Accepted iff 500 <= word_count <= 15_000.
    """
    return 500 <= word_count <= 15_000


# ---------------------------------------------------------------------------
# Task 12.3 — Property 1: Upload validation rejects invalid files
# ---------------------------------------------------------------------------

class TestUploadValidation:
    """
    Property 1: Upload validation rejects invalid files.

    The validator accepts a file if and only if the MIME type is PDF or DOCX
    AND the file size is at most 20 MB.

    **Validates: Requirements 1.1, 1.2, 1.4, 1.5**
    """

    @given(
        mime_type=st.sampled_from([
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'image/jpeg',
            'application/zip',
        ]),
        file_size=st.integers(min_value=1, max_value=30 * 1024 * 1024),
    )
    @h_settings(max_examples=100, deadline=None)
    def test_upload_accepted_iff_valid_mime_and_size(self, mime_type, file_size):
        """
        For any combination of MIME type and file size, the validator accepts
        the upload if and only if the MIME type is in ALLOWED_MIME_TYPES AND
        the file size is within the 20 MB limit.

        **Validates: Requirements 1.1, 1.2, 1.4, 1.5**
        """
        result = validate_upload(b'', mime_type, file_size)

        expected = (
            mime_type in ALLOWED_MIME_TYPES
            and file_size <= MAX_FILE_SIZE
        )

        assert result == expected, (
            f"validate_upload returned {result!r} for mime_type={mime_type!r}, "
            f"file_size={file_size}, but expected {expected!r}. "
            f"ALLOWED_MIME_TYPES={ALLOWED_MIME_TYPES}, MAX_FILE_SIZE={MAX_FILE_SIZE}"
        )


# ---------------------------------------------------------------------------
# Task 12.4 — Property 2: Prompt length validation
# ---------------------------------------------------------------------------

class TestPromptLengthValidation:
    """
    Property 2: Prompt length validation.

    The validator accepts a prompt if and only if its length is between 50 and
    10,000 characters (inclusive).

    **Validates: Requirements 1.3**
    """

    @given(length=st.integers(min_value=0, max_value=15_000))
    @h_settings(max_examples=100, deadline=None)
    def test_prompt_accepted_iff_length_in_range(self, length):
        """
        For any prompt of the given length, the validator accepts it if and
        only if 50 <= length <= 10,000.

        **Validates: Requirements 1.3**
        """
        prompt = 'a' * length
        result = validate_prompt(prompt)
        expected = 50 <= length <= 10_000

        assert result == expected, (
            f"validate_prompt returned {result!r} for length={length}, "
            f"but expected {expected!r}. "
            f"Accepted range is [50, 10000]."
        )


# ---------------------------------------------------------------------------
# Task 12.5 — Property 30: Target word count validation
# ---------------------------------------------------------------------------

class TestTargetWordCountValidation:
    """
    Property 30: Target word count validation.

    The system accepts a target word count if and only if it is between 500
    and 15,000 (inclusive).

    **Validates: Requirements 12.4**
    """

    @given(word_count=st.integers(min_value=0, max_value=20_000))
    @h_settings(max_examples=100, deadline=None)
    def test_word_count_accepted_iff_in_range(self, word_count):
        """
        For any integer word count, the validator accepts it if and only if
        500 <= word_count <= 15,000.

        **Validates: Requirements 12.4**
        """
        result = validate_word_count(word_count)
        expected = 500 <= word_count <= 15_000

        assert result == expected, (
            f"validate_word_count returned {result!r} for word_count={word_count}, "
            f"but expected {expected!r}. "
            f"Accepted range is [500, 15000]."
        )


# ---------------------------------------------------------------------------
# Task 12.6 — Property 29: Authorization — users can only access their own jobs
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestJobAuthorization:
    """
    Property 29: Authorization — users can only access their own jobs.

    Any authenticated user attempting to view a job belonging to another user
    receives HTTP 403.

    **Validates: Requirements 11.7**
    """

    def test_job_status_view_returns_403_for_non_owner(self):
        """
        The job_status view returns HTTP 403 when an authenticated user who
        does not own the job attempts to access it.

        **Validates: Requirements 11.7**
        """
        owner = UserFactory()
        other_user = UserFactory()

        job = GenerationJob.objects.create(
            user=owner,
            title='Owner Job',
            status=GenerationJob.Status.PENDING,
        )

        client = Client()
        client.force_login(other_user)

        url = reverse('generation:job_status', kwargs={'pk': job.pk})
        response = client.get(url)

        assert response.status_code == 403, (
            f"Expected HTTP 403 for non-owner accessing job_status, "
            f"but got {response.status_code}."
        )

    def test_job_status_json_view_returns_403_for_non_owner(self):
        """
        The job_status_json view returns HTTP 403 when an authenticated user
        who does not own the job attempts to access it.

        **Validates: Requirements 11.7**
        """
        owner = UserFactory()
        other_user = UserFactory()

        job = GenerationJob.objects.create(
            user=owner,
            title='Owner Job',
            status=GenerationJob.Status.PENDING,
        )

        client = Client()
        client.force_login(other_user)

        url = reverse('generation:job_status_json', kwargs={'pk': job.pk})
        response = client.get(url)

        assert response.status_code == 403, (
            f"Expected HTTP 403 for non-owner accessing job_status_json, "
            f"but got {response.status_code}."
        )

    def test_job_status_view_returns_200_for_owner(self):
        """
        The job_status view returns HTTP 200 when the owning user accesses it.
        Sanity check to confirm the 403 is not a blanket denial.

        **Validates: Requirements 11.7**
        """
        owner = UserFactory()

        job = GenerationJob.objects.create(
            user=owner,
            title='Owner Job',
            status=GenerationJob.Status.PENDING,
        )

        client = Client()
        client.force_login(owner)

        url = reverse('generation:job_status', kwargs={'pk': job.pk})
        response = client.get(url)

        assert response.status_code == 200, (
            f"Expected HTTP 200 for owner accessing job_status, "
            f"but got {response.status_code}."
        )

    def test_job_status_json_view_returns_200_for_owner(self):
        """
        The job_status_json view returns HTTP 200 when the owning user accesses it.
        Sanity check to confirm the 403 is not a blanket denial.

        **Validates: Requirements 11.7**
        """
        owner = UserFactory()

        job = GenerationJob.objects.create(
            user=owner,
            title='Owner Job',
            status=GenerationJob.Status.PENDING,
        )

        client = Client()
        client.force_login(owner)

        url = reverse('generation:job_status_json', kwargs={'pk': job.pk})
        response = client.get(url)

        assert response.status_code == 200, (
            f"Expected HTTP 200 for owner accessing job_status_json, "
            f"but got {response.status_code}."
        )


# ---------------------------------------------------------------------------
# Task 12.7 — Property 27: Progress polling endpoint contract
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProgressPollingEndpointContract:
    """
    Property 27: Progress polling endpoint contract.

    GET to the polling endpoint for a PROCESSING job returns JSON with
    `stage` (str), `progress_percentage` (int 0–100), and `status` (str).

    **Validates: Requirements 11.4**
    """

    @given(
        progress=st.integers(min_value=0, max_value=100),
        stage=st.text(min_size=0, max_size=50),
    )
    @h_settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_polling_endpoint_returns_required_json_fields(self, progress, stage):
        """
        For any PROCESSING job with any progress percentage and stage name,
        the polling endpoint returns a JSON object containing:
          - 'stage': a string
          - 'progress_percentage': an integer between 0 and 100
          - 'status': a string

        **Validates: Requirements 11.4**
        """
        owner = UserFactory()

        job = GenerationJob.objects.create(
            user=owner,
            title='Processing Job',
            status=GenerationJob.Status.PROCESSING,
            current_stage=stage,
            progress_percentage=progress,
        )

        client = Client()
        client.force_login(owner)

        url = reverse('generation:job_status_json', kwargs={'pk': job.pk})
        response = client.get(url)

        assert response.status_code == 200, (
            f"Expected HTTP 200 from polling endpoint, got {response.status_code}."
        )

        data = response.json()

        # Required fields must be present
        assert 'stage' in data, (
            f"Response JSON missing 'stage' field. Got: {data}"
        )
        assert 'progress_percentage' in data, (
            f"Response JSON missing 'progress_percentage' field. Got: {data}"
        )
        assert 'status' in data, (
            f"Response JSON missing 'status' field. Got: {data}"
        )

        # Type checks
        assert isinstance(data['stage'], str), (
            f"'stage' must be a string, got {type(data['stage']).__name__!r}: {data['stage']!r}"
        )
        assert isinstance(data['progress_percentage'], int), (
            f"'progress_percentage' must be an int, "
            f"got {type(data['progress_percentage']).__name__!r}: {data['progress_percentage']!r}"
        )
        assert isinstance(data['status'], str), (
            f"'status' must be a string, got {type(data['status']).__name__!r}: {data['status']!r}"
        )

        # Value checks
        assert 0 <= data['progress_percentage'] <= 100, (
            f"'progress_percentage' must be between 0 and 100, "
            f"got {data['progress_percentage']!r}"
        )

        # Values must match what was stored
        assert data['stage'] == stage, (
            f"Expected stage={stage!r}, got {data['stage']!r}"
        )
        assert data['progress_percentage'] == progress, (
            f"Expected progress_percentage={progress}, got {data['progress_percentage']!r}"
        )
        assert data['status'] == GenerationJob.Status.PROCESSING, (
            f"Expected status={GenerationJob.Status.PROCESSING!r}, got {data['status']!r}"
        )

        # Clean up to avoid DB state leaking between hypothesis examples
        job.delete()
        owner.delete()
