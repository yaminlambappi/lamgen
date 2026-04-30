import pytest


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def redis_client():
    """Provides a fakeredis client for SectionMemoryService tests."""
    import fakeredis
    from unittest.mock import patch
    fake = fakeredis.FakeRedis()
    with patch('generation.services.section_memory.SectionMemoryService._get_redis', return_value=fake):
        yield fake
