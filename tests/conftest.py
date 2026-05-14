import os

# Ensure DJANGO_ENV is set before any Django/settings import.
# pytest.ini sets DJANGO_SETTINGS_MODULE; we mirror the environment name here.
os.environ.setdefault("DJANGO_ENV", "test")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def redis_client():
    """Provides a fakeredis client for SectionMemoryService tests."""
    import fakeredis
    from unittest.mock import patch
    fake = fakeredis.FakeRedis()
    with patch(
        "apps.generation.services.section_memory.SectionMemoryService._get_redis",
        return_value=fake,
    ):
        yield fake
