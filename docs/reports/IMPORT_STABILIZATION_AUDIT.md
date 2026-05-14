# Import stabilization audit (pre-fix)

**Date:** 2026-05-14  
**Scope:** Pytest collection, `tests/`, `apps/` SEO helpers, Celery task imports, `conftest.py`, `pytest.ini`.  
**Excluded:** Architectural refactors, URL patterns, Docker, settings package layout.

## 1. Pytest / Django settings

| Finding | Risk | Notes |
|--------|------|--------|
| `pytest.ini` sets `DJANGO_SETTINGS_MODULE = config.settings` | **High** | `config.settings` package `__init__.py` is empty; `INSTALLED_APPS` length is 0 under that module. Tests need `config.settings.local` (same as `manage.py` default) for parity with real app config. |

## 2. `conftest.py`

| Finding | Risk | Notes |
|--------|------|--------|
| Patch target `generation.services.section_memory.SectionMemoryService._get_redis` | **High** | Module lives under `apps.generation`; patch path must use `apps.generation.services.section_memory`. |

## 3. Tests — legacy top-level packages

These packages no longer exist on `PYTHONPATH`; code lives under `apps.*`.

| Pattern | Example files | Resolution |
|--------|---------------|------------|
| `from generation.*` | `tests/factories.py`, `test_generation_*.py`, `test_static_analyser.py`, `test_refinement_properties.py`, `test_pipeline.py` (via factories) | → `from apps.generation.*` |
| `from thesis.*` | `tests/factories.py`, `test_views.py`, `test_pipeline.py`, `test_services.py` | → `from apps.thesis.*` |
| `from tools.*` | `test_tools_properties.py`, `test_islamic_panel.py`, `test_quran_dataset.py`, `test_views.py` | → `from apps.tools.*` |
| `from seo.*` (models/engine) | `test_tools_properties.py`, `test_views.py` | → `from apps.seo.*` |

## 4. Tests — `unittest.mock.patch` targets

Patch strings must match **imported** module paths at runtime (where the name is bound), typically `apps.*` for app code.

| Pattern | Files | Resolution |
|--------|-------|------------|
| `"generation.services.` | Several `test_generation_*.py`, `test_refinement_properties.py`, `test_generation_intelligence.py` | → `"apps.generation.services.` |
| `'thesis.tasks.` / `'thesis.views.` | `test_pipeline.py`, `test_views.py` | → `'apps.thesis.tasks.` / `'apps.thesis.views.` |

## 5. Tests — URL reverse namespaces

| Finding | Risk | Notes |
|--------|------|--------|
| `reverse('accounts:…')` | **Medium** | `apps.users.urls` defines `app_name = 'users'`. Reverse names must be `users:register`, `users:login`, `users:logout`. |

## 6. Application code (non-test)

| File | Stale import | Correct target |
|------|----------------|----------------|
| `apps/seo/services/authority_builder.py` | `tools.services.seo_content_generator` | `apps.tools.services.seo_content_generator` |
| `apps/seo/services/authority_builder.py` | `tools.services.content_uniqueness_engine` | `apps.seo.services.content_uniqueness_engine` |
| `apps/seo/services/programmatic_seo.py`, `mass_page_generator.py` | `tools.services.seo_content_generator` | `apps.tools.services.seo_content_generator` |
| `apps/users/views.py` | `tools.utils.bookmarks` | `apps.tools.utils.bookmarks` |
| `apps/generation/views.py` | `thesis.models` | `apps.thesis.models` |
| `apps/thesis/tasks.py` | `thesis.*` (lazy imports inside tasks) | `apps.thesis.*` |

## 7. Legacy / docs

| File | Action |
|------|--------|
| `docs/legacy/dashboard/views.py` | Align `thesis` / `tools` imports to `apps.thesis` / `apps.tools` for consistency (not on runtime path). |

## 8. Known test semantics (post-import)

| Test | Note |
|------|------|
| `test_login_valid_redirects_to_dashboard` | `LOGIN_REDIRECT_URL` is `/` in settings; assertion expecting `/dashboard/` likely **wrong** vs current product behavior — adjust to `/` after import fixes if still failing. |
| `test_unauthenticated_dashboard_redirects_to_login` vs `test_dashboard_unauthenticated_redirects` | May disagree on whether `home` is public; resolve against actual `apps.tools.views.index` behavior after collection passes. |

## 9. Circular imports

No systematic circular-import failure observed at collection stage; only `ModuleNotFoundError`.

---

## Resolution (post-fix, 2026-05-14)

- All findings in sections 1–7 of this audit were addressed with **minimal** edits (see `docs/reports/IMPORT_STABILIZATION_OUTCOME.md`).
- Pytest now uses **`config.settings.test`**; production remains **`config.settings.production`** via WSGI.

*End of document.*
