# Implementation Plan: Security Audit

## Overview

Implement all security hardening controls across the Django/Celery/Redis/PostgreSQL/Nginx stack in three priority tiers. Each task builds on the previous, wiring all components together by the end of Tier 1. Tiers 2 and 3 extend the hardened baseline with additional controls.

## Tasks

- [-] 1. Tier 1 — Production Stoppers
  - [x] 1.1 Fix `GameRoomConsumer` — add authentication check before `self.accept()`
    - In `games/consumers.py`, check `self.scope['user'].is_authenticated` at the top of `connect()`
    - If unauthenticated, call `await self.close(code=4001)` and return without calling `self.accept()`
    - Emit `AuditEvent.WEBSOCKET_AUTH_FAILURE` via `AuditLogger` on rejection
    - _Requirements: 6.1, 6.4_

  - [ ]* 1.2 Write property test for WebSocket authentication rejection (Property 9)
    - **Property 9: WebSocket Authentication Rejection**
    - **Validates: Requirements 6.1, 6.4**
    - Use `hypothesis` with `@pytest.mark.django_db`; generate unauthenticated WebSocket connection attempts and assert close code is 4001

  - [x] 1.3 Fix `nginx.conf` — remove direct `/media/` serving, implement `X-Accel-Redirect`
    - Remove the `location /media/` block from `nginx.conf`
    - Add an internal `location /protected-media/` block that only responds to `X-Accel-Redirect` headers
    - Create an authenticated Django view (e.g., `media_serve`) that checks ownership, then sets `X-Accel-Redirect` header pointing to the internal Nginx path
    - Wire the new view into `urls.py` for both `/media/uploads/` and `/media/outputs/` paths
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 1.4 Fix `accounts/views.py` — session fixation and open redirect
    - Call `request.session.cycle_key()` immediately after `auth.login()` in `login_view`
    - Validate the `next` parameter: reject any value containing `://`, starting with `//`, or not starting with `/`; fall back to `settings.LOGIN_REDIRECT_URL`
    - _Requirements: 1.3, 1.4_

  - [ ]* 1.5 Write property test for open redirect prevention (Property 3)
    - **Property 3: Open Redirect Prevention**
    - **Validates: Requirements 1.4**
    - Generate external URLs (containing `://`, starting with `//`, `javascript:`, `data:`) as `next` param; assert redirect location is never an external URL

  - [ ] 1.6 Add `StartupSecurityCheck` in `config/checks.py`
    - Implement the `check_security_settings` system check as specified in the design
    - Raise `Critical` errors for: default `SECRET_KEY`, `SESSION_COOKIE_SECURE=False`, `CSRF_COOKIE_SECURE=False` when `DEBUG=False`
    - Raise `Warning` for missing `ANTHROPIC_API_KEY` and default `ADMIN_URL`
    - Register the check via `AppConfig.ready()` in `config/apps.py`
    - Add `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD` to `config/settings.py`
    - _Requirements: 2.1, 1.5, 1.6, 12.1, 12.2, 24.2, 24.3_

  - [ ] 1.7 Remove `@csrf_exempt` from `games/views.py` — implement HMAC-signed token
    - Remove `@csrf_exempt` from `create_room` and `post_signal` views
    - Implement an HMAC-signed token mechanism: generate a signed token server-side, verify it in the view before processing
    - Update the JavaScript client to include the signed token in requests
    - Document the exemption removal and compensating control in a code comment
    - _Requirements: 13.1, 13.5_

  - [ ] 1.8 Deploy `AdminIPRestrictionMiddleware` and change admin URL
    - Implement `AdminIPRestrictionMiddleware` in `config/middleware.py` as specified in the design (returns 404 for non-allowlisted IPs)
    - Add `ADMIN_URL` and `ADMIN_ALLOWED_IPS` settings sourced from environment variables
    - Update `config/urls.py` to use `path(settings.ADMIN_URL, admin.site.urls)` instead of the hardcoded `'admin/'`
    - Add `AdminIPRestrictionMiddleware` to `MIDDLEWARE` before `CommonMiddleware`
    - _Requirements: 20.1, 20.2, 7.6_

  - [ ] 1.9 Add Redis `requirepass` to `docker-compose.yml` and update `REDIS_URL`
    - Add `command: redis-server --requirepass ${REDIS_PASSWORD}` to the Redis service in `docker-compose.yml`
    - Remove any hardcoded Redis credentials; source `REDIS_PASSWORD` from environment
    - Update `REDIS_URL` in `config/settings.py` to include the password credential
    - Update `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` accordingly
    - _Requirements: 10.6, 17.5_

  - [ ] 1.10 Add non-root `appuser` to `Dockerfile`
    - Add `RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser` to `Dockerfile`
    - Add `USER appuser` directive before `ENTRYPOINT`
    - Ensure file ownership of the app directory is set to `appuser` with `chown`
    - _Requirements: 10.1_

  - [ ] 1.11 Remove hardcoded DB credentials from `docker-compose.yml`
    - Replace `POSTGRES_PASSWORD=postgres` and `POSTGRES_USER=postgres` with `${POSTGRES_PASSWORD}` and `${POSTGRES_USER}` environment variable references
    - Update `DATABASE_URL` in settings to use the same env vars
    - Add the required variables to `.env.example`
    - _Requirements: 2.5, 10.2_

  - [ ] 1.12 Deploy `SecurityHeadersMiddleware` in `config/middleware.py`
    - Implement `SecurityHeadersMiddleware` as specified in the design (CSP with per-request nonce, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`)
    - Add a CSP context processor so `request.csp_nonce` is available in templates
    - Add `config.middleware.SecurityHeadersMiddleware` to `MIDDLEWARE` after `WhiteNoiseMiddleware`, before `SessionMiddleware`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 1.13 Write property test for security headers on all HTML responses (Property 4)
    - **Property 4: Security Headers on All HTML Responses**
    - **Validates: Requirements 3.1, 3.3, 3.4, 3.5, 3.6**
    - Generate requests to a sample of HTML-returning URLs; assert all required headers are present on every response

  - [ ] 1.14 Deploy `RateLimiter` on login, register, generation submit, and thesis upload
    - Implement `require_rate_limit` decorator in `config/security/rate_limit.py` as specified in the design
    - Apply to `login_view` (10 req / 15 min per IP), `register_view` (5 req / hr per IP), `submit_job` (10 req / hr per user), `UploadView.post` (5 req / hr per user)
    - Return HTTP 429 with `Retry-After` header and `{"error": "..."}` JSON body on limit exceeded
    - _Requirements: 1.1, 1.2, 8.1, 8.2, 8.3, 8.4, 8.6_

  - [ ]* 1.15 Write property test for rate limiting (Property 1)
    - **Property 1: Rate Limiting Enforces Limits**
    - **Validates: Requirements 1.1, 1.2, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6**
    - For each rate-limited endpoint, generate exactly `limit + 1` requests from the same identifier within the window; assert the last request returns 429 with `Retry-After` header

  - [ ] 1.16 Deploy `PromptInjectionFilter` on all generation inputs
    - Implement `PromptInjectionFilter` in `config/security/prompt_injection.py` as specified in the design
    - Call `PromptInjectionFilter.filter()` in `generation/views.py` `submit_job()` on `prompt_text` before saving to `GenerationJob`
    - Call it in `generation/services/` before constructing Anthropic API payloads
    - Log `AuditEvent.PROMPT_INJECTION_DETECTED` when `was_modified=True`
    - _Requirements: 4.4, 18.1_

  - [ ]* 1.17 Write property test for prompt injection filter (Property 5)
    - **Property 5: Prompt Injection Filter Neutralises Patterns**
    - **Validates: Requirements 4.4, 18.1**
    - Generate strings containing known injection patterns (instruction override, role-switch, delimiter injection); assert `was_modified=True` and sanitised output does not contain the original pattern

  - [ ] 1.18 Enforce token budget per request in generation pipeline
    - Add `MAX_INPUT_TOKENS_PER_REQUEST = 8000` to `config/settings.py` (sourced from env var)
    - Before any Anthropic API call in `generation/services/`, estimate token count and return HTTP 400 with `{"error": "Request exceeds token budget."}` if exceeded
    - _Requirements: 18.2_

  - [ ]* 1.19 Write property test for token budget rejection (Property 15)
    - **Property 15: Token Budget Rejection**
    - **Validates: Requirements 18.2**
    - Generate generation requests where estimated token count exceeds `MAX_INPUT_TOKENS_PER_REQUEST`; assert HTTP 400 is returned before any Anthropic API call is made

  - [ ] 1.20 Deploy `CSRFAuditMiddleware` — replace `CsrfViewMiddleware`
    - Implement `CSRFAuditMiddleware` in `config/middleware.py` as specified in the design (extends `CsrfViewMiddleware`, logs `AuditEvent.CSRF_FAILURE` before raising 403)
    - Replace `django.middleware.csrf.CsrfViewMiddleware` with `config.middleware.CSRFAuditMiddleware` in `MIDDLEWARE`
    - _Requirements: 13.1, 21.1_

  - [ ] 1.21 Fix `CrawlErrorMiddleware` — sanitise `HTTP_REFERER` before logging
    - In `seo/middleware.py`, strip newline characters (`\n`, `\r`) and truncate `HTTP_REFERER` to 200 characters before writing to the crawl error log
    - _Requirements: 11.5_

  - [ ] 1.22 Add `edit_outline` payload size limit
    - In `generation/views.py` `edit_outline` view, check `len(request.body)` before calling `json.loads(request.body)`
    - Return HTTP 400 with `{"error": "Payload too large."}` if body exceeds 50 KB (51200 bytes)
    - Validate that the parsed `sections` field is a list of objects conforming to the expected schema
    - _Requirements: 4.5_

  - [ ] 1.23 Deploy `AuditLogger` for Tier 1 security events
    - Implement `AuditLogger` and `AuditEvent` enum in `config/security/audit.py` as specified in the design
    - Configure the `security.audit` logger in `LOGGING` to write JSON to `/var/log/lamgen/audit.log`
    - Wire `AuditEvent.LOGIN_SUCCESS` and `AuditEvent.LOGIN_FAILURE` into `accounts/views.py` `login_view`
    - Wire `AuditEvent.LOGOUT` into `accounts/views.py` `logout_view`
    - Wire `AuditEvent.FILE_UPLOAD` into `thesis/views.py` and `generation/views.py`
    - Wire `AuditEvent.GENERATION_SUBMIT` into `generation/views.py` `submit_job`
    - _Requirements: 21.1, 21.2_

  - [ ]* 1.24 Write property test for audit log emission (Property 14)
    - **Property 14: Audit Log Emitted for Security Events**
    - **Validates: Requirements 2.3, 21.1, 21.2**
    - For each security event type, call `AuditLogger.log()` and assert the emitted JSON record contains `event`, `timestamp`, `ip`, and `path` fields and does not contain any secret values

  - [ ] 1.25 Add WebSocket message schema validation, size limit, and room code validation
    - In `games/consumers.py`, validate room code against `[A-Z0-9]{6}` pattern in `connect()` before accepting; close with code 4000 if invalid
    - In `receive()`, check message byte length; close with code 1009 if > 65536 bytes
    - Validate parsed JSON payload has a `type` field with an allowlisted value; silently discard invalid messages
    - _Requirements: 6.2, 6.3, 6.5_

  - [ ]* 1.26 Write property test for WebSocket room code validation (Property 10)
    - **Property 10: WebSocket Room Code Validation**
    - **Validates: Requirements 6.5**
    - Generate room codes that do not match `[A-Z0-9]{6}` (wrong length, lowercase, special chars); assert connection is rejected before `self.accept()`

  - [ ]* 1.27 Write property test for WebSocket message size enforcement (Property 11)
    - **Property 11: WebSocket Message Size Enforcement**
    - **Validates: Requirements 6.3**
    - Generate messages exceeding 65536 bytes; assert connection is closed with code 1009 and message is not broadcast

  - [ ] 1.28 Set Celery `task_time_limit` and `task_soft_time_limit`
    - Add `CELERY_TASK_TIME_LIMIT = 300` and `CELERY_TASK_SOFT_TIME_LIMIT = 270` to `config/settings.py`
    - Add `CELERY_RESULT_EXPIRES = 86400` to cap result backend growth
    - Verify these settings are picked up by the Celery app configuration in `config/celery.py`
    - _Requirements: 17.3, 17.6_

  - [ ] 1.29 Checkpoint — Tier 1 complete
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 2. Tier 2 — High Risk
  - [ ] 2.1 Deploy `XSSSanitiser` on thesis preview and all markdown rendering
    - Implement `XSSSanitiser` in `config/security/xss.py` as specified in the design (bleach-based, `sanitise()` and `sanitise_minimal()`)
    - Add `bleach` to `requirements.txt` with an exact pinned version
    - Call `XSSSanitiser.sanitise()` in `thesis/views.py` `ThesisPreviewView` after `md.markdown()`
    - Call `XSSSanitiser.sanitise_minimal()` wherever thesis titles or generation prompts are rendered as HTML
    - _Requirements: 15.2, 15.3_

  - [ ]* 2.2 Write property test for XSS sanitiser (Property 13)
    - **Property 13: XSS Sanitiser Strips Disallowed Tags**
    - **Validates: Requirements 15.2, 15.3**
    - Generate HTML strings containing disallowed tags (`script`, `iframe`, `object`, `embed`, `link`, `meta`) and event handler attributes; assert none appear in sanitised output

  - [ ] 2.3 Deploy `SSRFGuard` for all outbound HTTP calls
    - Implement `SSRFGuard` in `config/security/ssrf.py` as specified in the design (blocks RFC 1918, loopback, link-local, Docker ranges)
    - Add `SSRF_ALLOWED_DOMAINS = ['api.anthropic.com']` to `config/settings.py`
    - Wrap any existing `httpx.get()` / `requests.get()` calls with `SSRFGuard.validate()` before the request
    - Emit `AuditEvent.SSRF_BLOCKED` on violation
    - _Requirements: 14.1, 14.2, 14.4, 14.5_

  - [ ]* 2.4 Write property test for SSRF guard (Property 12)
    - **Property 12: SSRF Guard Blocks Private IP Ranges**
    - **Validates: Requirements 14.1, 14.2**
    - Generate URLs resolving to private, loopback, and link-local IP addresses; assert `SSRFGuard.validate()` raises `SSRFViolation` for all of them

  - [ ] 2.5 Add per-user daily token consumption limit
    - Add `MAX_TOKENS_PER_USER_PER_DAY` setting to `config/settings.py` (sourced from env var, default 200000)
    - Track daily token usage per user in Redis with key `token_usage:{user_id}:{date}` and 48-hour TTL
    - Before each Anthropic API call, check the user's daily total; return HTTP 400 and log `AuditEvent.TOKEN_BUDGET_EXCEEDED` if exceeded
    - _Requirements: 18.3_

  - [ ] 2.6 Add Celery per-user concurrency limit (3 concurrent jobs max)
    - At the generation task enqueue point in `generation/views.py`, count active jobs for the user in the DB or Redis
    - Reject with HTTP 429 if the user already has 3 or more active generation tasks in flight
    - _Requirements: 17.4_

  - [ ] 2.7 Deploy `AuditLogger` for remaining Tier 2 security events
    - Wire `AuditEvent.CSRF_FAILURE` — already handled by `CSRFAuditMiddleware` (verify)
    - Wire `AuditEvent.SSRF_BLOCKED` into `SSRFGuard` (done in 2.3)
    - Wire `AuditEvent.OWNERSHIP_VIOLATION` into all views that return 403 on ownership check failure
    - Wire `AuditEvent.WEBSOCKET_AUTH_FAILURE` into `GameRoomConsumer` (done in 1.1, verify)
    - Wire `AuditEvent.PROMPT_INJECTION_DETECTED` into `PromptInjectionFilter` (done in 1.16, verify)
    - Wire `AuditEvent.CONTENT_POLICY_VIOLATION` into the Anthropic API error handler in `generation/services/`
    - _Requirements: 21.1, 21.3_

  - [ ] 2.8 Add `TaskArgumentValidator` at all Celery enqueue points
    - Implement `TaskArgumentValidator` in `config/security/task_validator.py` as specified in the design
    - Call `TaskArgumentValidator.validate_job_id()` before `run_generation_pipeline.delay(job_id)` in `generation/views.py`
    - Call `TaskArgumentValidator.validate_thesis_id()` before `process_thesis_task.delay(thesis_id)` in `thesis/views.py`
    - _Requirements: 17.1_

  - [ ] 2.9 Integrate `pip-audit` into CI pipeline
    - Create `.github/workflows/security.yml` (or equivalent CI config) with a `dependency-audit` job
    - Run `pip-audit -r requirements.txt --fail-on HIGH` on every pull request
    - Block merges when HIGH or CRITICAL CVEs are detected
    - _Requirements: 9.1, 9.4, 23.2_

  - [ ] 2.10 Add Nginx rate limiting at proxy layer
    - Add `limit_req_zone` and `limit_conn_zone` directives to `nginx.conf`
    - Apply `limit_req` to the login and registration location blocks
    - Set `client_body_timeout`, `client_header_timeout`, `keepalive_timeout`, and `send_timeout` to prevent slow-client attacks
    - _Requirements: 8.7, 19.5_

  - [ ] 2.11 Add Nginx TLS configuration and security headers
    - Add a port 443 `server` block with TLS termination to `nginx.conf`
    - Add a port 80 `server` block that issues a 301 redirect to HTTPS
    - Add `server_tokens off` to suppress version disclosure
    - Add `add_header X-Content-Type-Options nosniff` and `add_header X-Frame-Options SAMEORIGIN` to non-embed location blocks
    - _Requirements: 10.3, 10.4, 10.5, 3.7_

  - [ ] 2.12 Implement output PII filtering on LLM responses
    - Create `config/security/pii_filter.py` with regex patterns for email addresses, phone numbers, and credit card numbers
    - Call the PII filter on all Anthropic API responses before storing or returning them
    - _Requirements: 18.4_

  - [ ] 2.13 Add `SECURE_HSTS_PRELOAD = True` to settings
    - Set `SECURE_HSTS_PRELOAD = True` in `config/settings.py` (guarded by `not DEBUG`)
    - Verify `SECURE_HSTS_SECONDS >= 31536000` and `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` are also set
    - _Requirements: 12.2_

  - [ ] 2.14 Add dynamic ordering field allowlist validation across all querysets
    - Search the codebase for `order_by(request.GET` and `filter(**{` patterns
    - For each occurrence, define an explicit `ALLOWED_SORT_FIELDS` set and validate the user-supplied value against it before applying to the queryset
    - Default to a safe field (e.g., `-created_at`) when the supplied value is not in the allowlist
    - _Requirements: 16.2, 16.3_

  - [ ] 2.15 Checkpoint — Tier 2 complete
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Tier 3 — Medium Risk
  - [ ] 3.1 Hash pinning in `requirements.txt` using `pip-compile --generate-hashes`
    - Run `pip-compile --generate-hashes requirements.in > requirements.txt` (or equivalent)
    - Commit the updated `requirements.txt` with SHA-256 hashes for all packages
    - Update CI to install with `pip install --require-hashes -r requirements.txt`
    - _Requirements: 23.1_

  - [ ] 3.2 Multi-stage Docker build — exclude dev dependencies from production image
    - Refactor `Dockerfile` to use a multi-stage build: a `builder` stage that installs all dependencies, and a `production` stage that copies only the production packages
    - Ensure `django-debug-toolbar`, `django-extensions`, and other dev-only packages are not present in the production image
    - _Requirements: 24.4_

  - [ ] 3.3 Admin MFA readiness — integrate `django-otp`
    - Add `django-otp` and `qrcode` to `requirements.txt` with exact pinned versions
    - Add `django_otp` and `django_otp.plugins.otp_totp` to `INSTALLED_APPS`
    - Subclass `OTPAdminSite` or configure `django-otp` to require TOTP for admin login
    - _Requirements: 20.3_

  - [ ] 3.4 Admin append-only audit log for all admin actions
    - Create `AuditLogEntry` model in `config/models.py` as specified in the design
    - Create and run a migration for the `AuditLogEntry` table
    - Connect Django's `post_save` signal on `LogEntry` (from `django.contrib.admin.models`) to write to `AuditLogEntry`
    - Add a database migration that revokes `UPDATE` and `DELETE` on the `config_auditlogentry` table from the application DB user
    - _Requirements: 20.4, 21.4_

  - [ ] 3.5 Admin 30-minute inactivity session timeout
    - Add `ADMIN_SESSION_COOKIE_AGE = 1800` to `config/settings.py`
    - Implement middleware or override `AdminSite` to set a shorter session expiry for admin requests
    - _Requirements: 20.5_

  - [ ] 3.6 Automated encrypted daily database backups with 30-day retention
    - Create a `scripts/backup_db.sh` script that runs `pg_dump`, encrypts the output with AES-256 (via `openssl enc`), and writes to the backup destination
    - Add a Celery beat schedule or cron entry to run the backup script daily
    - Implement a rotation policy that deletes backups older than 30 days
    - _Requirements: 22.1, 22.2, 22.4_

  - [ ] 3.7 Data retention policy implementation
    - Document the retention policy in `docs/data-retention.md` (uploaded files: 24h post-completion; generated outputs: 30 days; user accounts: until deletion request)
    - Verify the existing `cleanup_old_generation_uploads` Celery task enforces the 24-hour retention window
    - _Requirements: 12.5, 5.5_

  - [ ] 3.8 GDPR privacy notice
    - Create a `privacy_notice` view and template accessible from all pages via a footer link
    - The notice must describe: data collected, how it is used, retention periods, and user rights under GDPR
    - _Requirements: 12.6_

  - [ ] 3.9 Secret rotation runbook and restore verification procedure
    - Create `docs/secret-rotation-runbook.md` documenting steps to rotate `SECRET_KEY`, `ANTHROPIC_API_KEY`, `DATABASE_URL`, and `REDIS_URL`, including session invalidation after `SECRET_KEY` rotation
    - Create `docs/restore-verification.md` documenting the monthly restore verification procedure
    - _Requirements: 22.3, 22.5_

  - [ ] 3.10 Startup env var validation for all required variables
    - Extend `StartupSecurityCheck` in `config/checks.py` to validate all required env vars (`ANTHROPIC_API_KEY`, `SECRET_KEY`, `ADMIN_URL`, `ADMIN_ALLOWED_IPS`, `DATABASE_URL`, `REDIS_URL`)
    - Validate that `ENVIRONMENT` variable is set and matches the expected deployment context
    - Raise `Critical` system check errors for any absent or insecure-default required variable
    - _Requirements: 24.1, 24.2, 24.3_

  - [ ] 3.11 Checkpoint — Tier 3 complete
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Property-Based Test Suite
  - [ ] 4.1 Create `tests/test_security_properties.py` with test infrastructure
    - Set up the test file with `hypothesis` imports, `@pytest.mark.django_db` fixtures, and shared test utilities (user factory, job factory)
    - Configure `@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])` as the default for all property tests
    - _Requirements: all_

  - [ ]* 4.2 Write property test for session ID rotation on login (Property 2)
    - **Property 2: Session ID Rotation on Login**
    - **Validates: Requirements 1.3**
    - For any valid user credentials, assert the session key in the response cookie differs from the session key before login

  - [ ]* 4.3 Write property test for file upload MIME type enforcement (Property 6)
    - **Property 6: File Upload MIME Type Enforcement**
    - **Validates: Requirements 4.1**
    - Generate files with MIME types not in `{application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document}`; assert upload endpoint rejects them and does not save to disk

  - [ ]* 4.4 Write property test for ownership enforcement (Property 7)
    - **Property 7: Ownership Enforcement on All User Resources**
    - **Validates: Requirements 5.2, 7.2**
    - For any two distinct users A and B, and a resource owned by A, assert a request from B returns 403 or 404 and does not return resource data

  - [ ]* 4.5 Write property test for unauthenticated access redirect (Property 8)
    - **Property 8: Unauthenticated Access Redirects to Login**
    - **Validates: Requirements 7.1, 7.5**
    - For any URL in the set of protected views, assert an unauthenticated request receives HTTP 302 to the login URL with the `next` parameter set

  - [ ]* 4.6 Write property test for file download `Content-Disposition` (Property 16)
    - **Property 16: File Download Content-Disposition**
    - **Validates: Requirements 5.4**
    - For any request to a file download endpoint, assert the response includes `Content-Disposition: attachment` and does not set `Content-Type` to an executable MIME type

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests in section 4 consolidate tests not already placed inline with their implementation tasks
- Inline property tests (1.2, 1.5, 1.13, 1.15, 1.17, 1.19, 1.24, 1.26, 1.27, 2.2, 2.4) should be written in `tests/test_security_properties.py` alongside the implementation
- All property tests use `hypothesis` (already at 6.112.1 in `requirements.txt`)
- Run property tests with `pytest tests/test_security_properties.py --hypothesis-seed=0`
