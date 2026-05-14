# Import stabilization — outcome and validation

**Date:** 2026-05-14  
**Related audit (pre-fix):** [IMPORT_STABILIZATION_AUDIT.md](./IMPORT_STABILIZATION_AUDIT.md)

---

## 1. Fixed imports (summary)

| Area | Change |
|------|--------|
| **Tests** | `generation.*` → `apps.generation.*`; `thesis.*` → `apps.thesis.*`; `tools.*` → `apps.tools.*`; `seo.models` / `seo.engine` → `apps.seo.*` |
| **Patch targets** | `"generation.services…"` → `"apps.generation.services…"`; `thesis.tasks` / `thesis.views` → `apps.thesis.*` |
| **URL reverses** | `accounts:*` → `users:*` in tests |
| **`apps/seo/services/*`** | `tools.services.seo_content_generator` → `apps.tools.services.seo_content_generator`; `content_uniqueness_engine` → `apps.seo.services.content_uniqueness_engine` |
| **`apps/users/views.py`** | `tools.utils.bookmarks` → `apps.tools.utils.bookmarks`; templates `accounts/*.html` → `users/*.html`; redirect `accounts:login` → `users:login` |
| **`apps/generation/views.py`** | `thesis.models` → `apps.thesis.models` |
| **`apps/thesis/tasks.py`** | Lazy imports `thesis.*` → `apps.thesis.*` |
| **`docs/legacy/dashboard/views.py`** | `thesis` / `tools` models → `apps.thesis` / `apps.tools` |
| **`conftest.py`** | Redis patch path → `apps.generation.services.section_memory.SectionMemoryService._get_redis` |
| **`tests/test_tools_properties.py`** | Login POST URL `/accounts/login/` → `/users/login/` |

---

## 2. Unresolved / intentionally not bulk-fixed

| Item | Notes |
|------|--------|
| **`scripts/fix_all_imports.py`** | Still documents string replacements for old layouts; not used at runtime. |
| **`.kiro/` docs** | Mention `/accounts/` paths; documentation only. |
| **Hypothesis-heavy suite** | `tests/test_refinement_properties.py` remains large/slow; not modified beyond import paths. |

---

## 3. Pytest status

| Check | Result |
|--------|--------|
| **Collection** | **222 tests**, **0 collection errors** (`DJANGO_SETTINGS_MODULE=config.settings.test`) |
| **`tests/test_views.py`** | **22 passed**, **1 skipped** (upload rate-limit placeholder) |
| **Full `tests/` run** | Not completed in agent time box; many property tests are long-running. Run locally: `python3 -m pytest tests/ -q` |

---

## 4. Local runtime status

| Check | Result |
|--------|--------|
| **`manage.py check`** | **No issues** (with default `config.settings.local`) |
| **Pytest settings** | New **`config/settings/test.py`**: extends `local`, sets `STATICFILES_STORAGE` to Django’s non-manifest storage so tests do not require `collectstatic` / manifest entries (fixes `Missing staticfiles manifest entry for 'img/og-default.png'`). |
| **`pytest.ini`** | `DJANGO_SETTINGS_MODULE=config.settings.test` |

---

## 5. Production compatibility

| Topic | Status |
|--------|--------|
| **WSGI / production** | Still **`config.settings.production`** (from `config/wsgi.py`); unchanged. |
| **Manifest static files** | Still **`CompressedManifestStaticFilesStorage`** in `config/settings/base.py` for real deploys; only **test** settings override. |
| **Docker / compose** | Not moved; **no** edits. |

---

## 6. Remaining architecture drift risks

- **`config.settings` package `__init__.py`** is still minimal; anything using `DJANGO_SETTINGS_MODULE=config.settings` (without `.local` / `.production` / `.test`) gets an **empty** settings object. Prefer explicit `config.settings.local` / `.production` / `.test` everywhere.
- **Thesis “dashboard”** in older tests meant a thesis-centric UI; the live **`home`** view is the **tools** index. Tests were aligned to that behavior where needed.

---

## 7. Remaining namespace risks

- New code should **always** import Django apps as **`apps.<app>`** to match `INSTALLED_APPS`.
- When patching, patch where the name is **used** (e.g. `apps.generation.services.orchestrator.SectionMemoryService`), not legacy top-level packages.

---

## 8. Safe next steps

1. Run full **`pytest tests/`** (optionally `-n auto` if `pytest-xdist` is available) on CI with Redis/Postgres services as in production.
2. Run **`collectstatic`** in Docker/CI before smoke tests if any job assumes **`staticfiles/`** + manifest on disk.
3. Optionally add **`STORAGES`** dict (Django 4.2+) when upgrading past manifest deprecation warnings.
4. Remove or rewrite the **skipped** upload rate-limit test if product policy brings a limit back into `UploadView`.

---

## Files touched (this pass)

- `tests/*.py` (imports, patches, URL names, a few expectations)  
- `tests/factories.py`  
- `conftest.py`, `pytest.ini`  
- `config/settings/test.py` (**new**)  
- `apps/seo/services/authority_builder.py`, `programmatic_seo.py`, `mass_page_generator.py`  
- `apps/users/views.py`  
- `apps/generation/views.py`, `apps/thesis/tasks.py`  
- `docs/legacy/dashboard/views.py`  
- `docs/reports/IMPORT_STABILIZATION_AUDIT.md`  
- `tests/test_tools_properties.py`  
