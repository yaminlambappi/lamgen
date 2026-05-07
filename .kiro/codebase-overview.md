# LamGen Codebase Overview

## Project: Universal Thesis Generator / LamGen Tools

A full-stack Django web application with two main product areas:
1. **LamGen Tools** — a collection of free online tools (text, developer, SEO, etc.)
2. **AI Academic Writing** — AI-powered thesis/assignment generation from uploaded PDFs

Live at: `lamgen.lamlab.me`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Django 4.2.16 |
| Task Queue | Celery 5.3.6 |
| Broker / Cache | Redis 7 |
| Database | PostgreSQL 15 (SQLite in dev) |
| WSGI | Gunicorn 22 |
| Reverse Proxy | Nginx (Alpine) |
| PDF Extraction | PyMuPDF (fitz) 1.24.10 |
| PDF Rendering | WeasyPrint 63.1 |
| Token Counting | tiktoken 0.7.0 |
| File Validation | python-magic 0.4.27 |
| LLM — Primary | Anthropic Claude (anthropic SDK 0.40.0) |
| LLM — Alt | OpenAI-compat (openai 1.57.0), Groq 0.13.0, Google Gemini 0.8.3 |
| Static Files | WhiteNoise 6.7.0 |
| Env Config | django-environ 0.11.2 |
| Frontend | Bootstrap 5.3.2 + Bootstrap Icons + vanilla JS |
| Containerization | Docker + Compose |
| Testing | pytest-django + factory-boy + hypothesis |
| Runtime | Python 3.11 |

---

## Project Structure

```
lamgen/
├── config/               # Django project config
│   ├── settings.py       # All settings, env-driven
│   ├── urls.py           # Root URL routing
│   ├── celery.py         # Celery app init
│   ├── games.py          # Games config
│   └── tool_categories.py # Tool category definitions
├── accounts/             # Custom user auth
├── thesis/               # Legacy thesis generator (older pipeline)
├── generation/           # New AI generation pipeline (primary)
│   ├── models.py         # GenerationJob, AssignmentBrief, RubricProfile, DocumentOutline, GeneratedSection, TokenUsageLog
│   ├── views.py          # submit_job, job_status, confirm_outline, edit_outline
│   ├── tasks.py          # Celery tasks: run_generation_pipeline, continue_generation_pipeline, cleanup_old_generation_uploads
│   └── services/
│       ├── claude_service.py         # Anthropic API wrapper (mock mode, retry, budget guard)
│       ├── generation_config.py      # Runtime config resolver (token budgets, model routing)
│       ├── orchestrator.py           # Progress tracking + failure handling
│       ├── assignment_intelligence.py # Stage 1+2: document analysis → AssignmentBrief
│       ├── outline_generator.py      # Stage 3: outline generation → DocumentOutline
│       ├── section_generator.py      # Stage 6: section-by-section generation
│       ├── section_memory.py         # Redis-backed cross-section memory
│       ├── section_planner.py        # Section planning utilities
│       ├── research_context.py       # Research context injection
│       ├── author_identity.py        # Author persona / writing style constants
│       └── refinement/               # Refinement passes (humanization, review, etc.)
├── tools/                # Tools ecosystem
│   ├── models.py         # ToolCategory, Tool, ToolBookmark, ToolUsageHistory
│   ├── views.py          # Tool listing, detail, OG image
│   └── data/             # Tool data files
├── seo/                  # Programmatic SEO
│   ├── models.py         # SEOCategory, SEOPage, LongTailVariant
│   └── engine/           # SEO content generation
├── blog/                 # Blog / content articles
│   └── models.py         # ContentArticle (markdown body)
├── games/                # WebRTC peer-to-peer games
│   ├── models.py         # SignalingRoom
│   └── consumers.py      # Django Channels WebSocket consumer
├── dashboard/            # User dashboard (paginated job history)
├── templates/            # Global templates
├── static/               # CSS, JS, images
├── tests/                # All tests
│   ├── factories.py      # factory-boy factories for all models
│   ├── test_generation_*.py  # Generation pipeline tests
│   ├── test_pipeline.py
│   ├── test_refinement_properties.py
│   ├── test_tools_properties.py
│   └── test_views.py
├── conftest.py           # pytest fixtures (db access, fakeredis)
├── pytest.ini            # pytest config (80% coverage threshold)
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
├── Makefile
└── manage.py
```

---

## Key Apps & Responsibilities

### `accounts`
- Custom user model: `CustomUser(AbstractUser)` with `email` (unique), `university`, `bio`
- Standard registration/login/logout views

### `generation` (primary AI pipeline)
- **GenerationJob** — UUID PK, tracks status through: `PENDING → ANALYSING → AWAITING_OUTLINE_REVIEW → PROCESSING → COMPLETED/FAILED`
- **AssignmentBrief** — 1:1 with job; stores detected assignment type, academic level, citation style, required sections, rubric criteria
- **RubricProfile** — 1:1 with brief; JSON criteria array `[{name, weight, distinction_descriptor}]`
- **DocumentOutline** — 1:1 with job; JSON sections array `[{title, target_word_count, key_points}]`; `user_confirmed` flag
- **GeneratedSection** — FK to job; ordered sections with content, word_count, humanized flag, reviewer_score
- **TokenUsageLog** — per-call token tracking (stage, input_tokens, output_tokens, model)

**Pipeline flow:**
1. User submits form (file or prompt text) → `run_generation_pipeline` Celery task
2. Stage 1+2: `AssignmentIntelligenceEngine.analyse()` → creates `AssignmentBrief` + `RubricProfile`
3. Stage 3: `OutlineGenerationService.generate()` → creates `DocumentOutline`; job pauses at `AWAITING_OUTLINE_REVIEW`
4. User reviews/edits outline → confirms → `continue_generation_pipeline` Celery task
5. Stage 6: `SectionGenerationService.generate_all()` → creates `GeneratedSection` records
6. Job → `COMPLETED`

**Model routing:**
- Haiku: analysis (fast/cheap)
- Sonnet: outline, validation
- Opus: section writing (temperature=0.82, top_p=0.92 for natural writing)

**Generation modes:** `economy` | `standard` | `quality` — controls token budgets, model selection, context injection

### `thesis` (legacy pipeline)
- Simpler older pipeline: upload PDF → Celery task → LLM → WeasyPrint PDF
- `ThesisRequest` model with `PENDING/PROCESSING/COMPLETED/FAILED` status
- `ThesisChunk` for token-chunked source text
- Progress tracked via Redis stage keys (TTL 1hr), polled every 3s

### `tools`
- `ToolCategory` + `Tool` models with slugs, icons, gradient colors, SEO fields
- `ToolBookmark` and `ToolUsageHistory` per user
- Tools seeded via management command from `config/tool_categories.py`
- OG image generation endpoint

### `seo`
- `SEOCategory` + `SEOPage` for programmatic SEO content
- `LongTailVariant` for long-tail keyword pages per tool
- `CrawlErrorMiddleware` for 404/error tracking

### `blog`
- `ContentArticle` with markdown body, content types: tutorial/comparison/use-case/troubleshooting
- Related tools M2M

### `games`
- WebRTC signaling via `SignalingRoom` model (4-char code, offer/answer/ICE candidates)
- Django Channels WebSocket consumer

---

## URL Structure

```
/admin/                          # Django admin
/accounts/                       # Auth (login, register, logout)
/thesis/                         # Legacy thesis pipeline
/generation/                     # New generation pipeline
/games/                          # Games
/ (i18n)                         # Home / tools index
/tools/                          # Tools listing + detail
/content/                        # SEO pages
/blog/                           # Blog articles
```

---

## Configuration (Environment Variables)

Key env vars (see `.env.example`):
- `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `REDIS_URL`
- `ANTHROPIC_API_KEY`
- `CLAUDE_MODEL` (default: `claude-sonnet-4-5`)
- `CLAUDE_MAX_TOKENS` (default: 4000)
- `CLAUDE_MAX_TOKENS_PER_JOB` (default: 40000)
- `CLAUDE_MOCK_MODE` (default: False) — use for local dev without API calls
- `GENERATION_MODE` (economy/standard/quality, default: standard)
- `ASSIGNMENT_TYPE_DEFAULT`, `CITATION_STYLE_DEFAULT`, `WRITING_TONE_DEFAULT`
- `SECTION_MODE` (auto/fixed), `SECTION_COUNT_DEFAULT`
- `MEDIA_ROOT`, `SITE_URL`

---

## Testing

- Framework: `pytest-django` with `hypothesis` for property-based tests
- Coverage threshold: **80%** (enforced in CI via `--cov-fail-under=80`)
- Factories: `tests/factories.py` — UserFactory, GenerationJobFactory, AssignmentBriefFactory, etc.
- `conftest.py`: `autouse` db fixture + `fakeredis` fixture for SectionMemoryService
- Test files cover: generation pipeline, Claude service, views, tools properties, refinement properties

Run tests:
```bash
pytest --run  # or just: pytest
```

---

## Security

- CSRF on all POST/DELETE
- `LoginRequiredMixin` on all thesis/generation/dashboard views
- Object-level ownership: `ThesisOwnerMixin` (403 on cross-user access)
- File upload: extension + MIME type check via `python-magic`
- Output PDFs served via `FileResponse` (not direct media URLs)
- Secrets via env vars only
- Auto-purge input files after 24h via Celery Beat task
- Nginx: `client_max_body_size 15M`

---

## Docker / Deployment

Services in `docker-compose.yml`:
- `web` — Gunicorn (3 workers)
- `worker` — Celery worker (concurrency=2)
- `beat` — Celery Beat (scheduled tasks)
- `redis` — Redis 7 Alpine
- `db` — PostgreSQL 15 Alpine
- `nginx` — Nginx Alpine (reverse proxy + static/media)

Shared `media_data` volume for uploads/outputs across web containers.

---

## Internationalization

Supported languages: English, Bengali, Hindi, Spanish, Arabic
Locale files in `locale/`
i18n URL patterns for tools/content/blog routes
