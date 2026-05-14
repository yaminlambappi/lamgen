"""
Property-based tests for the LamGen Tools Ecosystem.
Covers all 10 correctness properties from the design document.
"""
import json
import pytest
from hypothesis import given, settings as h_settings, HealthCheck
from hypothesis import strategies as st


# ── Property 1: Tool metadata auto-generation invariant ─────────────────────

@given(
    name=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',))),
    short_desc=st.text(min_size=0, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',))),
)
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@pytest.mark.django_db
def test_tool_metadata_autogeneration(name, short_desc):
    from apps.tools.models import Tool, ToolCategory
    cat, _ = ToolCategory.objects.get_or_create(
        slug='prop-test-cat',
        defaults={'name': 'Property Test', 'order': 999},
    )
    tool = Tool(
        name=name,
        short_desc=short_desc,
        category=cat,
        template_name='tools/generic_tool.html',
        description='test',
    )
    tool.save()
    expected_title = f'{name} — Free Online Tool | LamGen'[:70]
    assert tool.meta_title == expected_title
    assert tool.meta_description == short_desc[:160]
    assert len(tool.meta_title) <= 70
    assert len(tool.meta_description) <= 160
    tool.delete()


# ── Property 2: Tool canonical URL pattern ───────────────────────────────────

@given(
    cat_slug=st.from_regex(r'[a-z][a-z0-9\-]{2,20}', fullmatch=True),
    tool_slug=st.from_regex(r'[a-z][a-z0-9\-]{2,30}', fullmatch=True),
)
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@pytest.mark.django_db
def test_tool_canonical_url(cat_slug, tool_slug):
    from apps.tools.models import Tool, ToolCategory
    cat, _ = ToolCategory.objects.get_or_create(
        slug=cat_slug,
        defaults={'name': cat_slug, 'order': 999},
    )
    # Use a unique tool slug per test to avoid cross-category collisions
    unique_tool_slug = f'prop2-{cat_slug[:10]}-{tool_slug[:20]}'
    tool, _ = Tool.objects.get_or_create(
        slug=unique_tool_slug,
        defaults={
            'name': unique_tool_slug,
            'category': cat,
            'short_desc': 'test',
            'template_name': 'tools/generic_tool.html',
            'description': 'test',
        },
    )
    url = tool.get_absolute_url()
    assert url == f'/tools/{tool.category.slug}/{unique_tool_slug}/'


# ── Property 3: Search result bounds ────────────────────────────────────────

@given(q=st.text(min_size=0, max_size=1))
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.django_db
def test_search_short_query_returns_empty(client, q):
    response = client.get('/tools/search/', {'q': q})
    # Rate limiter may kick in during property test (100 requests from same IP)
    assert response.status_code in (200, 429)
    if response.status_code == 200:
        assert response.json()['results'] == []


@given(q=st.text(min_size=2, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N', 'Zs'))))
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@pytest.mark.django_db
def test_search_result_count_bounded(client, q):
    response = client.get('/tools/search/', {'q': q})
    assert response.status_code in (200, 429)
    if response.status_code == 200:
        assert len(response.json()['results']) <= 15


# ── Property 4: Metadata length invariants ───────────────────────────────────

@given(
    name=st.text(min_size=1, max_size=300, alphabet=st.characters(blacklist_categories=('Cs',))),
    short_desc=st.text(min_size=0, max_size=1000, alphabet=st.characters(blacklist_categories=('Cs',))),
)
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow], deadline=None)
@pytest.mark.django_db
def test_metadata_length_invariants(name, short_desc):
    from apps.tools.models import Tool, ToolCategory
    cat, _ = ToolCategory.objects.get_or_create(
        slug='meta-len-test',
        defaults={'name': 'Meta Length Test', 'order': 999},
    )
    tool = Tool(
        name=name,
        short_desc=short_desc,
        category=cat,
        template_name='tools/generic_tool.html',
        description='test',
    )
    tool.save()
    assert len(tool.meta_title) <= 70
    assert len(tool.meta_description) <= 160
    tool.delete()


# ── Property 5: Bookmark toggle idempotence ──────────────────────────────────

@pytest.mark.django_db
def test_bookmark_toggle_idempotence(client):
    from django.contrib.auth import get_user_model
    from apps.tools.models import Tool, ToolCategory
    User = get_user_model()
    user = User.objects.create_user(
        username='bm_test_user',
        password='testpass123',
        email='bm@test.com',
        university='Test University',
    )
    cat, _ = ToolCategory.objects.get_or_create(
        slug='bm-cat',
        defaults={'name': 'BM Cat', 'order': 999},
    )
    tool, _ = Tool.objects.get_or_create(
        slug='bm-tool-idempotent',
        defaults={
            'name': 'BM Tool',
            'category': cat,
            'short_desc': 'test',
            'template_name': 'tools/generic_tool.html',
            'description': 'test',
            'is_active': True,
        },
    )
    client.force_login(user)

    # Toggle ON
    r1 = client.post(
        '/tools/bookmark/save/',
        json.dumps({'tool_slug': 'bm-tool-idempotent'}),
        content_type='application/json',
    )
    assert r1.status_code == 200
    assert r1.json()['bookmarked'] is True

    # Toggle OFF — back to original state
    r2 = client.post(
        '/tools/bookmark/save/',
        json.dumps({'tool_slug': 'bm-tool-idempotent'}),
        content_type='application/json',
    )
    assert r2.status_code == 200
    assert r2.json()['bookmarked'] is False


# ── Property 6: Unauthenticated bookmark rejection ───────────────────────────

@given(tool_slug=st.from_regex(r'[a-z][a-z0-9\-]{2,20}', fullmatch=True))
@h_settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.django_db
def test_unauthenticated_bookmark_returns_401(client, tool_slug):
    response = client.post(
        '/tools/bookmark/save/',
        json.dumps({'tool_slug': tool_slug}),
        content_type='application/json',
    )
    assert response.status_code == 401
    assert response.json()['error'] == 'Login required'


# ── Property 7: Session bookmark merge completeness ──────────────────────────

@pytest.mark.django_db
def test_session_bookmark_merge(client):
    from django.contrib.auth import get_user_model
    from apps.tools.models import Tool, ToolCategory, ToolBookmark
    User = get_user_model()

    cat, _ = ToolCategory.objects.get_or_create(
        slug='merge-cat',
        defaults={'name': 'Merge Cat', 'order': 999},
    )
    slugs = [f'merge-tool-{i}' for i in range(5)]
    for slug in slugs:
        Tool.objects.get_or_create(
            slug=slug,
            defaults={
                'name': slug,
                'category': cat,
                'short_desc': 'test',
                'template_name': 'tools/generic_tool.html',
                'description': 'test',
                'is_active': True,
            },
        )

    # Set session bookmarks as guest
    session = client.session
    session['session_bookmarks'] = slugs
    session.save()

    # Login — should trigger merge
    user = User.objects.create_user(
        username='merge_test_user',
        password='testpass123',
        email='merge@test.com',
        university='Test University',
    )
    client.post('/users/login/', {'username': 'merge_test_user', 'password': 'testpass123'})

    # All 5 bookmarks should now be in DB
    db_slugs = set(
        ToolBookmark.objects.filter(user=user).values_list('tool__slug', flat=True)
    )
    for slug in slugs:
        assert slug in db_slugs, f'{slug} not merged into DB bookmarks'


# ── Property 8: SEO content determinism ─────────────────────────────────────

@given(slug=st.from_regex(r'[a-z][a-z0-9\-]{5,40}', fullmatch=True))
@h_settings(max_examples=100)
def test_seo_content_determinism(slug):
    from apps.seo.engine.content_generator import generate_items
    result1 = generate_items('captions', 'Test Topic', slug)
    result2 = generate_items('captions', 'Test Topic', slug)
    assert result1 == result2, 'generate_items must be deterministic for the same slug'


# ── Property 9: SEO content minimum count ───────────────────────────────────

@given(slug=st.from_regex(r'[a-z][a-z0-9\-]{5,40}', fullmatch=True))
@h_settings(max_examples=100)
def test_seo_content_minimum_count(slug):
    from apps.seo.engine.content_generator import generate_items
    items = generate_items('captions', 'Test Topic', slug)
    assert len(items) >= 20, f'Expected >= 20 items, got {len(items)}'


# ── Property 10: MIME validation ────────────────────────────────────────────

@given(content=st.binary(min_size=100, max_size=4096))
@h_settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_mime_validation_rejects_non_pdf_as_pdf(content):
    import io
    from apps.tools.utils.file_validation import validate_mime
    file_obj = io.BytesIO(content)
    is_valid, detected = validate_mime(file_obj, 'pdf')
    assert isinstance(is_valid, bool)
    assert isinstance(detected, str)
    # Random binary data that doesn't start with %PDF- must not be valid PDF
    if not content.startswith(b'%PDF-'):
        assert is_valid is False, f'Expected invalid PDF, got is_valid=True for detected={detected}'
