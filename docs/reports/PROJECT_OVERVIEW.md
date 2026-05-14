# Universal Thesis Generator — Project Overview Report

---

## 1. Project Title

**Universal Thesis Generator**
An AI-powered academic writing platform that transforms uploaded research PDFs into fully structured, professionally formatted thesis documents.

---

## 2. Project Overview

Universal Thesis Generator is a full-stack Django web application that automates the generation of university-standard academic assignments and theses. Users upload a source PDF (research paper, assignment brief, case study, or notes), and the system extracts, analyzes, and generates a complete written response using a multi-pass LLM pipeline. The output is delivered as a downloadable, print-ready PDF formatted to academic standards.

The system is designed for asynchronous, production-grade operation — PDF processing and LLM generation run as background Celery tasks, with real-time progress tracking delivered to the browser via a polling JSON API.

---

## 3. Purpose and Objectives

- Reduce the time and effort required to produce structured academic writing from raw research material.
- Provide a reliable, repeatable pipeline that extracts assignment requirements, rubric criteria, and case details from uploaded documents before generating targeted responses.
- Deliver output that meets university formatting standards (Times New Roman, A4, title page, table of contents, page numbers).
- Support multiple LLM providers (Anthropic Claude, OpenRouter, Groq, Google Gemini) through a unified service interface, allowing flexibility without code changes.
- Maintain strict data privacy: uploaded source files are automatically purged after 24 hours.

---

## 4. Problem the System Solves

Academic writing is time-intensive and structurally demanding. Students and researchers often have access to source material but struggle to translate it into well-structured, rubric-aligned written work. Generic AI tools produce hallucinated content and ignore document-specific requirements.

This system solves that by:

- Parsing the actual uploaded document to detect assignment type, required sections, and marking criteria before writing a single word.
- Grounding every generated sentence strictly in the uploaded content — no invented facts, no fabricated references.
- Applying a six-pass refinement pipeline (generation → refinement → humanization → evaluation → rubric alignment) to produce output that reads as naturally written academic prose.
- Delivering the result as a properly formatted PDF, not raw text.

---

## 5. Core Features and Functionalities

- **PDF Upload and Validation**: Accepts PDF files up to the configured limit. Validates both file extension and MIME type using `python-magic` to prevent spoofed uploads.
- **Asynchronous Generation Pipeline**: Celery task handles the full pipeline — PDF extraction, text chunking, LLM generation, PDF rendering — without blocking the web process.
- **Real-Time Progress Tracking**: A Redis-backed stage system stores granular pipeline progress (7 stages). A polling JSON endpoint (`/thesis/status/<id>/json/`) serves live progress to the browser every 3 seconds.
- **Multi-Pass LLM Pipeline**: Six sequential LLM passes — document analysis, per-section generation, refinement, humanization, evaluation/auto-fix, and rubric alignment — produce high-quality academic output.
- **Multi-Provider LLM Support**: Configurable via `LLM_PROVIDER` environment variable. Supports Anthropic Claude, OpenRouter, Groq, and Google Gemini with automatic client initialization and exponential-backoff retry logic.
- **Academic PDF Rendering**: WeasyPrint renders the generated markdown into a styled A4 PDF with title page, auto-generated table of contents, Times New Roman 12pt, 1.5 line height, justified text, and page numbers.
- **In-Browser Preview**: Completed theses can be previewed as rendered HTML (via `python-markdown`) before downloading.
- **Personal Dashboard**: Paginated view of all user submissions with status counts (total, completed, failed, in-progress).
- **Thesis Management**: Users can delete their own thesis records, which removes both database entries and associated files from disk.
- **Scheduled Cleanup**: Celery Beat runs an hourly task that deletes input files older than 24 hours, keeping storage lean.
- **Django Admin Interface**: Full admin panel for `ThesisRequest` and `ThesisChunk` models with filtering, search, and bulk actions.

---

## 6. User Roles and Permissions

The system implements a single authenticated user role with strict per-object ownership enforcement.

| Capability | Unauthenticated | Authenticated User |
|---|---|---|
| View landing page | ✓ | ✓ |
| Register / Login | ✓ | — |
| Upload PDF | ✗ | ✓ (own requests only) |
| View status / progress | ✗ | ✓ (own requests only) |
| Preview generated thesis | ✗ | ✓ (own requests only) |
| Download output PDF | ✗ | ✓ (own requests only) |
| Delete thesis request | ✗ | ✓ (own requests only) |
| Access dashboard | ✗ | ✓ (own data only) |
| Admin panel | ✗ | ✓ (superusers only) |

Ownership is enforced via `ThesisOwnerMixin`, which raises `PermissionDenied` (HTTP 403) if the authenticated user does not own the requested `ThesisRequest`. All thesis views inherit `LoginRequiredMixin`, redirecting unauthenticated requests to the login page.

---

## 7. System Architecture Overview

The application follows a **service-oriented monolith** pattern with clear separation between the web layer, task layer, and service layer.

```
Browser
  │
  ▼
Nginx (reverse proxy, static/media serving)
  │
  ▼
Gunicorn (3 workers) ── Django Application
  │                         │
  │                    ┌────┴────────────────────┐
  │                    │  Apps                   │
  │                    │  ├── accounts (auth)     │
  │                    │  ├── thesis (core)       │
  │                    │  └── dashboard (UI)      │
  │                    └────────────────────────-─┘
  │
  ▼
Redis ◄──── Celery Worker (process_thesis_task)
  │              │
  │         ┌────┴──────────────────────────┐
  │         │  Services                     │
  │         │  ├── PDFService (PyMuPDF)      │
  │         │  ├── LLMService (multi-prov.)  │
  │         │  └── ThesisPDFGenerator        │
  │         └───────────────────────────────┘
  │
  ▼
PostgreSQL (persistent data)
  │
  ▼
Media Volume (uploads/, outputs/)
```

**Key architectural decisions:**

- The web process never calls the LLM or renders PDFs directly. All heavy work is offloaded to Celery workers, keeping HTTP response times fast.
- Redis serves dual purpose: Celery broker/result backend and real-time stage tracking (TTL-keyed stage strings per thesis ID).
- Celery Beat runs as a separate container for scheduled maintenance tasks.
- Static files are served by WhiteNoise with compressed manifest storage, eliminating the need for a separate static file server in development.

---

## 8. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Web Framework | Django | 4.2.16 |
| Task Queue | Celery | 5.3.6 |
| Message Broker / Cache | Redis | 7 (Alpine) |
| Database | PostgreSQL | 15 (Alpine) |
| WSGI Server | Gunicorn | 22.0.0 |
| Reverse Proxy | Nginx | Alpine |
| PDF Extraction | PyMuPDF (fitz) | 1.24.10 |
| PDF Rendering | WeasyPrint | 62.3 |
| Token Counting | tiktoken | 0.7.0 |
| Markdown Processing | python-markdown | 3.7 |
| File Type Validation | python-magic | 0.4.27 |
| LLM — Anthropic | anthropic SDK | 0.34.2 |
| LLM — OpenAI-compat | openai SDK | 1.51.0 |
| LLM — Groq | groq SDK | 0.11.0 |
| LLM — Google | google-generativeai | 0.8.3 |
| Static Files | WhiteNoise | 6.7.0 |
| Environment Config | django-environ | 0.11.2 |
| Frontend CSS | Bootstrap | 5.3.2 |
| Frontend Icons | Bootstrap Icons | 1.11.3 |
| Containerization | Docker + Compose | — |
| Testing | pytest-django + factory-boy + hypothesis | — |
| Runtime | Python | 3.11 |

---

## 9. Database Design Overview

The database consists of three primary tables.

**`accounts_customuser`** (extends `AbstractUser`)
- `username`, `email` (unique), `password` — standard auth fields
- `university` (CharField) — required at registration
- `bio` (TextField) — optional profile field

**`thesis_thesisrequest`**
- `user` (FK → CustomUser, CASCADE) — ownership link
- `title` (CharField, max 500) — user-provided thesis title
- `input_file` (FileField → `uploads/`) — uploaded source PDF
- `output_file` (FileField → `outputs/`) — generated output PDF
- `generated_thesis` (TextField) — raw markdown output from LLM
- `status` (CharField, db_index) — `PENDING | PROCESSING | COMPLETED | FAILED`
- `error_message` (TextField) — populated on pipeline failure
- `created_at`, `updated_at` (DateTimeField, auto, db_index on created_at)

**`thesis_thesischunk`**
- `thesis_request` (FK → ThesisRequest, CASCADE)
- `order` (PositiveIntegerField) — chunk sequence position
- `content` (TextField) — decoded token chunk text
- `token_count` (PositiveIntegerField) — approximate word count
- Unique constraint on `(thesis_request, order)`

Indexes are placed on `status` and `created_at` to support dashboard filtering and the cleanup task's time-range query efficiently.

---

## 10. Security Features Implemented

- **CSRF Protection**: Django's `CsrfViewMiddleware` is active across all POST/DELETE endpoints. The logout action uses a POST form with CSRF token rather than a GET link.
- **Authentication Enforcement**: All thesis and dashboard views require authentication via `LoginRequiredMixin`. Unauthenticated requests are redirected to the login page.
- **Object-Level Authorization**: `ThesisOwnerMixin` enforces that users can only access their own `ThesisRequest` records. Cross-user access returns HTTP 403.
- **File Type Validation**: Upload validation checks both the file extension (`.pdf`) and the actual MIME type using `python-magic` (reads the file header bytes), preventing extension-spoofed uploads.
- **Secure File Serving**: Output PDFs are served via `FileResponse` with `Content-Disposition: attachment`, not exposed as direct media URLs.
- **Security Middleware Stack**: `SecurityMiddleware`, `XFrameOptionsMiddleware`, and `CsrfViewMiddleware` are all active.
- **Environment-Based Secrets**: `SECRET_KEY`, `DATABASE_URL`, `LLM_API_KEY`, and other sensitive values are loaded from environment variables via `django-environ`. No secrets are hardcoded.
- **Password Validation**: Django's full password validator suite is configured (similarity, minimum length, common password, numeric-only checks).
- **Unique Email Enforcement**: Registration form validates email uniqueness at the form level in addition to the database constraint.
- **Automatic File Purge**: Input PDFs are deleted from disk after 24 hours via the scheduled `cleanup_old_uploads` Celery task, limiting data retention exposure.
- **Nginx Upload Limit**: `client_max_body_size 15M` is set at the proxy layer to reject oversized uploads before they reach Django.

---

## 11. APIs and Integrations

**Internal JSON API**

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/thesis/status/<id>/json/` | GET | Required | Returns `status`, `progress_percentage`, `title`, `error_message` for polling |
| `/thesis/delete/<id>/` | DELETE | Required | Deletes thesis record and associated files; returns `{"success": true}` |

**External LLM Integrations**

The `LLMService` class abstracts four external AI providers behind a single `generate_thesis(chunks, title)` interface:

- **Anthropic Claude** (`claude-haiku-4-5-20251001`) — primary provider; called via the official `anthropic` SDK.
- **OpenRouter** — OpenAI-compatible endpoint (`openrouter/free` model); called via the `openai` SDK with a custom `base_url`.
- **Groq** (`mixtral-8x7b-32768`) — called via the `groq` SDK.
- **Google Gemini** (`gemini-2.0-flash`) — called via `google-generativeai` with system instruction injection at model initialization.

Provider selection is controlled by the `LLM_PROVIDER` environment variable. All providers share the same retry logic (3 attempts, exponential backoff starting at 1 second) and a maximum output of 8,192 tokens per call.

---

## 12. Frontend and UI/UX Approach

The frontend is server-rendered Django templates with Bootstrap 5.3 for layout and Bootstrap Icons for iconography. No JavaScript framework is used — interactivity is handled with minimal vanilla JS.

**Key UI patterns:**

- **Base template inheritance**: `base.html` provides the navbar, toast notification container, loading overlay, and footer. All pages extend it.
- **Responsive layout**: Bootstrap's grid system ensures the interface works across desktop and mobile viewports.
- **Real-time progress UI**: The status page (`status.html`) uses `status_poll.js` to poll the JSON API every 3 seconds. The script updates a Bootstrap progress bar, step indicators (with animated spinner on the active step), and status text without a page reload. On completion or failure, polling stops and the appropriate action buttons or error state are revealed.
- **Toast notifications**: Django messages are rendered as Bootstrap toasts that auto-dismiss after 5 seconds, providing non-intrusive feedback for form submissions and actions.
- **Dashboard pagination**: The dashboard paginates thesis history at 10 records per page with status badges and action links per row.
- **Preview rendering**: The `ThesisPreviewView` converts stored markdown to HTML using `python-markdown` with `extra`, `toc`, and `nl2br` extensions, rendering a readable in-browser preview before the user downloads the PDF.
- **Static file optimization**: WhiteNoise serves static files with Brotli and Gzip compression via `CompressedManifestStaticFilesStorage`, with content-hashed filenames for long-term browser caching.

---

## 13. Performance and Scalability Considerations

- **Asynchronous task execution**: The LLM pipeline (which can take several minutes) runs entirely in Celery workers, keeping the web process free to handle other requests. Worker concurrency is set to 2 per container in the Compose configuration.
- **Token-aware chunking**: `PDFService` uses `tiktoken` with the `cl100k_base` encoding to split extracted text into chunks of at most 2,000 tokens, ensuring no single LLM call exceeds context limits regardless of source document size.
- **Bulk database writes**: `ThesisChunk` records are created with `bulk_create` rather than individual inserts, reducing database round-trips during the chunking stage.
- **Selective field updates**: All `thesis.save()` calls in the pipeline use `update_fields` to write only changed columns, avoiding full-row updates on a potentially large `generated_thesis` text field.
- **Redis TTL for stage keys**: Pipeline stage keys in Redis are set with a 1-hour TTL, preventing unbounded key accumulation.
- **Horizontal scaling**: The architecture supports scaling the `web` and `worker` services independently. The shared `media_data` Docker volume allows multiple web containers to serve the same output files.
- **Nginx buffering and timeouts**: Proxy read/send timeouts are set to 120 seconds to accommodate long-running requests, with connection timeout at 60 seconds.
- **Static file caching**: WhiteNoise serves compressed, content-hashed static files with `Cache-Control: public, immutable` headers, reducing repeat load on the server.
- **Database indexing**: `status` and `created_at` fields on `ThesisRequest` are indexed, supporting efficient dashboard queries and the cleanup task's time-range filter.

---

## 14. Challenges Faced and Solutions

**Multi-provider LLM abstraction**
Different providers have incompatible SDK interfaces (chat completions vs. native messages vs. generative models). Solved by implementing a provider-dispatched `_call_api` method inside `LLMService`, with provider-specific client initialization isolated to `_init_client`. Adding a new provider requires only a new branch in each method.

**Reliable progress reporting without WebSockets**
Real-time progress from a background Celery task to the browser is non-trivial without WebSockets. Solved by writing named stage strings to Redis with a TTL at each pipeline step, and having the browser poll a lightweight JSON endpoint that reads the stage and maps it to a percentage. This avoids the complexity of Django Channels while still providing meaningful progress feedback.

**LLM output quality and consistency**
Single-pass LLM generation produces inconsistent academic quality. Solved by implementing a six-pass pipeline: initial per-section generation driven by rubric analysis, followed by sequential refinement, humanization, evaluation/auto-fix, and rubric alignment passes. Each pass has a focused prompt with strict constraints (no new facts, preserve structure, target word count).

**PDF MIME type spoofing**
File extension checks alone are insufficient for security. Solved by reading the first 2,048 bytes of the uploaded file and passing them to `python-magic` to verify the actual MIME type is `application/pdf` before accepting the upload.

**Scheduled file cleanup without a separate cron service**
Solved by using Celery Beat as a dedicated container with an hourly schedule for the `cleanup_old_uploads` task, keeping the cleanup logic inside the application codebase and avoiding external cron dependencies.

---

## 15. Future Improvements

- **User-configurable generation settings**: Allow users to select target word count, citation style (APA, Harvard, MLA), and output language before submission.
- **WebSocket-based progress**: Replace the polling mechanism with Django Channels WebSocket connections for lower-latency, push-based progress updates.
- **Multiple file uploads**: Support uploading multiple source PDFs per request, merging extracted content before generation.
- **Plagiarism and similarity scoring**: Integrate a similarity detection service to provide a confidence score on the originality of the generated output.
- **User profile management**: Add a profile edit page allowing users to update their university, bio, and email.
- **Rate limiting per user**: Implement per-user daily submission limits at the application layer (currently tested but not enforced in production views).
- **Output format options**: Support DOCX export in addition to PDF, using `python-docx`.
- **Admin analytics dashboard**: Add aggregate statistics (submissions per day, success rate, average generation time) to the Django admin.
- **S3-compatible object storage**: Replace local media volume with S3 or compatible storage (e.g., MinIO) for production deployments requiring horizontal scaling of the web tier.

---

## 16. Conclusion

Universal Thesis Generator is a production-ready Django application that demonstrates a well-structured, service-oriented architecture for AI-assisted academic writing. The system cleanly separates concerns across the web layer (Django views, templates), task layer (Celery pipeline), and service layer (PDF extraction, LLM generation, PDF rendering). Security is addressed at multiple levels — authentication, object-level authorization, file type validation, and automatic data purge. The multi-provider LLM abstraction and Redis-backed progress tracking reflect practical engineering decisions made to balance reliability, flexibility, and user experience. The codebase is covered by a comprehensive test suite (unit, integration, and pipeline tests) with an 80% coverage threshold enforced at CI level, making it suitable for academic, client, and portfolio presentation.
