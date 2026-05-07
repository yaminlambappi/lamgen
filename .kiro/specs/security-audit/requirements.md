# Requirements Document

## Introduction

This document defines the security audit requirements for the LamGen platform prior to a live global launch. The audit covers the full Django/Celery/Redis/PostgreSQL/Nginx stack, including authentication, file upload handling, API integrations, WebSocket connections, infrastructure configuration, and dependency management. The goal is to identify and remediate all security vulnerabilities that could expose user data, enable unauthorized access, or compromise system integrity in a production global environment.

## Glossary

- **Auditor**: The security audit tooling and process that scans the codebase
- **System**: The LamGen Django web application and its supporting infrastructure
- **Validator**: The input validation layer within Django forms and views
- **Scanner**: Automated static analysis and dependency scanning tools
- **Nginx**: The reverse proxy server fronting the Django application
- **Celery_Worker**: The asynchronous task processing service
- **Redis**: The message broker and cache backend
- **WebSocket_Consumer**: The Django Channels WebSocket handler in `games/consumers.py`
- **Rate_Limiter**: The rate limiting middleware and decorator applied to API endpoints
- **Media_Server**: The Nginx location block serving files from `/media/`
- **Secret**: Any credential, API key, token, or cryptographic key used by the System

---

## Requirements

### Requirement 1: Authentication Security

**User Story:** As a security engineer, I want all authentication flows to be hardened, so that user accounts cannot be compromised through brute force, session fixation, or open redirect attacks.

#### Acceptance Criteria

1. WHEN a user submits login credentials, THE System SHALL enforce a per-IP and per-username rate limit of no more than 10 failed attempts within a 15-minute window before temporarily blocking further attempts.
2. WHEN a login attempt is rate-limited, THE System SHALL return an HTTP 429 response with a `Retry-After` header indicating when the block expires.
3. WHEN a user successfully authenticates, THE System SHALL rotate the session identifier to prevent session fixation attacks.
4. WHEN the `next` query parameter is present on the login redirect, THE Validator SHALL reject any value that does not resolve to a path on the same origin, redirecting to the default home page instead.
5. THE System SHALL set the `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, and `SESSION_COOKIE_SAMESITE` Django settings to `True`, `True`, and `"Lax"` respectively in all non-DEBUG environments.
6. THE System SHALL set `CSRF_COOKIE_SECURE` to `True` in all non-DEBUG environments.
7. WHEN a logout request is received via a method other than POST, THE System SHALL redirect to the home page without calling `logout()`, preventing CSRF-based forced logout via GET.

---

### Requirement 2: Secrets and Credentials Management

**User Story:** As a security engineer, I want all secrets to be managed securely, so that API keys and credentials are never exposed in source code, logs, or error responses.

#### Acceptance Criteria

1. THE System SHALL NOT use the default insecure `SECRET_KEY` value `"django-insecure-change-me-in-production"` in any non-DEBUG environment; the application SHALL refuse to start if `SECRET_KEY` matches the default value and `DEBUG` is `False`.
2. THE System SHALL NOT commit the `.env` file to version control; the `.gitignore` SHALL include `.env` and `.env.*` patterns (excluding `.env.example`).
3. THE System SHALL NOT log the value of `ANTHROPIC_API_KEY`, `SECRET_KEY`, `DATABASE_URL`, or `REDIS_URL` at any log level.
4. IF the `ANTHROPIC_API_KEY` setting is empty or absent at application startup in a non-DEBUG environment, THEN THE System SHALL log a startup warning and disable generation features rather than silently failing at request time.
5. THE docker-compose.yml SHALL NOT hardcode production database credentials; all credentials SHALL be supplied via environment variables or Docker secrets.
6. THE System SHALL NOT expose internal error tracebacks, stack traces, or settings values in HTTP responses when `DEBUG` is `False`.

---

### Requirement 3: HTTP Security Headers

**User Story:** As a security engineer, I want all HTTP responses to include appropriate security headers, so that browsers enforce content security policies and prevent common client-side attacks.

#### Acceptance Criteria

1. THE System SHALL include a `Content-Security-Policy` header on all HTML responses that restricts `script-src`, `style-src`, `img-src`, `connect-src`, and `frame-ancestors` to explicitly allowlisted origins.
2. THE System SHALL set `SECURE_HSTS_SECONDS` to a minimum of 31536000 (one year) and `SECURE_HSTS_INCLUDE_SUBDOMAINS` to `True` in all non-DEBUG environments.
3. THE System SHALL set `X-Content-Type-Options: nosniff` on all responses.
4. THE System SHALL set `Referrer-Policy: strict-origin-when-cross-origin` on all responses.
5. THE System SHALL set `Permissions-Policy` to disable access to camera, microphone, and geolocation APIs on all HTML responses.
6. WHEN the `embed_view` sets `X-Frame-Options: ALLOWALL`, THE System SHALL scope this override to only the `/embed/` URL namespace and SHALL NOT apply it globally.
7. THE Nginx configuration SHALL add security headers at the proxy layer as a defence-in-depth measure, including `X-Frame-Options: SAMEORIGIN` for non-embed routes.

---

### Requirement 4: Input Validation and Injection Prevention

**User Story:** As a security engineer, I want all user-supplied input to be validated and sanitised, so that injection attacks cannot compromise the database, file system, or AI prompts.

#### Acceptance Criteria

1. WHEN a file is uploaded via the thesis or generation upload forms, THE Validator SHALL verify the MIME type using `python-magic` against the allowlist before saving the file to disk.
2. WHEN a file is uploaded, THE Validator SHALL enforce a maximum file size of 20 MB at the Django layer in addition to the Nginx `client_max_body_size` directive.
3. WHEN a file is saved to disk, THE System SHALL generate a UUID-based filename and SHALL NOT preserve the original user-supplied filename in the storage path.
4. WHEN user-supplied text is included in a prompt sent to the Anthropic API, THE System SHALL sanitise the input to remove or escape prompt-injection patterns (e.g., instruction override sequences such as "Ignore previous instructions").
5. WHEN the `edit_outline` endpoint receives a JSON body, THE Validator SHALL enforce a maximum payload size of 50 KB and SHALL validate that the `sections` field is a list of objects conforming to the expected schema before persisting.
6. THE System SHALL use Django ORM parameterised queries exclusively and SHALL NOT construct raw SQL strings from user-supplied input.
7. WHEN the search endpoint receives a query parameter `q`, THE Validator SHALL strip or reject any HTML or script tags before processing.

---

### Requirement 5: File Upload and Media Serving Security

**User Story:** As a security engineer, I want uploaded files and generated outputs to be served securely, so that users cannot access other users' files or execute uploaded content.

#### Acceptance Criteria

1. THE Media_Server SHALL NOT serve files from the `/media/uploads/` path directly via Nginx; uploaded source files SHALL only be accessible through authenticated Django views that enforce ownership checks.
2. WHEN a user requests a generated output file (PDF or DOCX), THE System SHALL verify that the requesting user is the owner of the associated job or thesis record before serving the file.
3. THE System SHALL store uploaded files outside the web root or in a path not directly routable by Nginx without authentication.
4. WHEN serving a generated file for download, THE System SHALL set `Content-Disposition: attachment` and SHALL NOT set `Content-Type` to any executable MIME type.
5. THE System SHALL implement a periodic cleanup task that deletes uploaded source files from disk after a configurable retention period (default 24 hours post-completion), and this task SHALL already exist as `cleanup_old_generation_uploads`.

---

### Requirement 6: WebSocket Security

**User Story:** As a security engineer, I want WebSocket connections to be authenticated and validated, so that unauthenticated users cannot join game rooms or inject arbitrary messages.

#### Acceptance Criteria

1. WHEN a WebSocket connection is initiated to the `GameRoomConsumer`, THE WebSocket_Consumer SHALL verify that the connecting user is authenticated before calling `self.accept()`; unauthenticated connections SHALL be closed with code 4001.
2. WHEN a WebSocket message is received, THE WebSocket_Consumer SHALL validate that the parsed JSON payload conforms to an expected schema (containing at minimum a `type` field with an allowlisted value) before broadcasting to the room group.
3. WHEN a WebSocket message is received, THE WebSocket_Consumer SHALL enforce a maximum message size of 64 KB and SHALL close the connection with code 1009 if the limit is exceeded.
4. THE System SHALL restrict WebSocket upgrade requests to authenticated sessions by configuring Django Channels middleware to check session authentication before the consumer is instantiated.
5. WHEN a room code is provided in the WebSocket URL, THE WebSocket_Consumer SHALL validate that the room code matches the pattern `[A-Z0-9]{6}` and SHALL reject connections with invalid room codes.

---

### Requirement 7: API and Endpoint Authorization

**User Story:** As a security engineer, I want all API endpoints to enforce proper authorization, so that users can only access and modify their own resources.

#### Acceptance Criteria

1. THE System SHALL apply `@login_required` or `LoginRequiredMixin` to every view that reads or writes user-specific data, including all generation, thesis, and dashboard views.
2. WHEN a user requests a resource (job, thesis, outline) by ID, THE System SHALL verify that the `user` foreign key on the record matches `request.user` and SHALL return HTTP 403 if it does not.
3. THE `record_usage` endpoint SHALL enforce CSRF protection; it SHALL NOT be exempted from `CsrfViewMiddleware`.
4. THE `toggle_bookmark` endpoint SHALL enforce CSRF protection for authenticated users.
5. WHEN an unauthenticated user accesses a protected endpoint, THE System SHALL redirect to the login page with the `next` parameter set to the originally requested URL.
6. THE Django admin interface SHALL be accessible only from allowlisted IP addresses or via an additional authentication layer in production.

---

### Requirement 8: Rate Limiting and Denial-of-Service Protection

**User Story:** As a security engineer, I want rate limiting applied consistently across all public and authenticated endpoints, so that the platform is protected against abuse and denial-of-service attacks.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL be applied to the login endpoint with a limit of no more than 10 requests per 15-minute window per IP address.
2. THE Rate_Limiter SHALL be applied to the registration endpoint with a limit of no more than 5 requests per hour per IP address.
3. THE Rate_Limiter SHALL be applied to the generation job submission endpoint with a limit of no more than 10 jobs per hour per authenticated user.
4. THE Rate_Limiter SHALL be applied to the thesis upload endpoint with a limit of no more than 5 uploads per hour per authenticated user.
5. THE Rate_Limiter SHALL be applied to the search endpoint with a limit of no more than 60 requests per minute per IP address (already partially implemented).
6. WHEN a rate limit is exceeded, THE System SHALL return HTTP 429 with a `Retry-After` header and a JSON body containing a human-readable `error` message.
7. THE Nginx configuration SHALL include connection and request rate limiting at the proxy layer as a defence-in-depth measure against volumetric attacks.

---

### Requirement 9: Dependency Vulnerability Management

**User Story:** As a security engineer, I want all third-party dependencies to be audited for known vulnerabilities, so that the platform does not ship with exploitable packages.

#### Acceptance Criteria

1. THE Scanner SHALL audit all packages listed in `requirements.txt` against the CVE database using `pip-audit` or an equivalent tool and SHALL produce a report of all HIGH and CRITICAL severity findings.
2. WHEN a HIGH or CRITICAL vulnerability is identified in a dependency, THE System SHALL either upgrade to a patched version or document a written risk acceptance with a remediation timeline before launch.
3. THE System SHALL pin all dependency versions to exact versions (using `==`) in `requirements.txt` to prevent unexpected upgrades introducing vulnerabilities; the current `requirements.txt` already uses exact pinning and SHALL be maintained.
4. THE Scanner SHALL be integrated into the CI/CD pipeline to run on every pull request and block merges when HIGH or CRITICAL vulnerabilities are detected.
5. THE System SHALL use the latest stable patch release of Django 4.2.x (currently `4.2.16`) and SHALL document a plan to upgrade to a supported LTS version before the current LTS support window closes.

---

### Requirement 10: Infrastructure and Container Security

**User Story:** As a security engineer, I want the Docker and Nginx configuration to follow security best practices, so that the production infrastructure does not expose unnecessary attack surface.

#### Acceptance Criteria

1. THE Dockerfile SHALL run the application as a non-root user; a dedicated `appuser` SHALL be created and the `USER` directive SHALL be set before the `ENTRYPOINT`.
2. THE docker-compose.yml SHALL NOT expose the PostgreSQL port (5432) or Redis port (6379) to the host network; these services SHALL only be accessible within the Docker internal network.
3. THE Nginx configuration SHALL listen on port 443 with TLS termination in production; the port 80 server block SHALL redirect all HTTP traffic to HTTPS with a 301 status code.
4. THE Nginx configuration SHALL set `server_tokens off` to suppress version disclosure in response headers and error pages.
5. THE Nginx configuration SHALL add `add_header X-Content-Type-Options nosniff` and `add_header X-Frame-Options SAMEORIGIN` to all non-embed location blocks.
6. THE Redis service SHALL be configured with a password (`requirepass`) in production and the `REDIS_URL` SHALL include the password credential.
7. THE System SHALL set `SECURE_PROXY_SSL_HEADER` to `('HTTP_X_FORWARDED_PROTO', 'https')` (already present) and SHALL set `USE_X_FORWARDED_HOST` to `True` only if the Nginx proxy is the sole entry point.

---

### Requirement 11: Error Handling and Information Leakage

**User Story:** As a security engineer, I want error responses to be sanitised, so that internal implementation details are not disclosed to potential attackers.

#### Acceptance Criteria

1. WHEN an unhandled exception occurs in a view, THE System SHALL return a generic HTTP 500 response without stack traces, file paths, or settings values when `DEBUG` is `False`.
2. WHEN a `GenerationJob` or `ThesisRequest` fails, THE System SHALL store the error message in the database but SHALL NOT expose the raw exception message to the end user; a generic user-facing message SHALL be shown instead.
3. THE System SHALL configure Django's logging to route `ERROR` and above to a structured log sink (file or external service) and SHALL NOT log sensitive fields such as passwords, API keys, or full file paths containing user identifiers.
4. WHEN a 404 response is generated, THE System SHALL NOT disclose whether a resource exists but belongs to another user versus genuinely not existing; both cases SHALL return HTTP 404.
5. THE `CrawlErrorMiddleware` SHALL sanitise the `HTTP_REFERER` header value before writing it to the crawl error log to prevent log injection.

---

### Requirement 12: Data Protection and Privacy

**User Story:** As a security engineer, I want user data to be protected at rest and in transit, so that the platform complies with data protection obligations for a global audience.

#### Acceptance Criteria

1. THE System SHALL enforce HTTPS for all traffic in production by setting `SECURE_SSL_REDIRECT` to `True` in non-DEBUG environments.
2. THE System SHALL set `SECURE_HSTS_SECONDS` to at least 31536000 and `SECURE_HSTS_PRELOAD` to `True` to enable HSTS preloading.
3. THE System SHALL NOT store plaintext passwords; Django's `AbstractUser` with `PBKDF2PasswordHasher` (default) SHALL be used and SHALL remain the active password hasher.
4. WHEN a user deletes a thesis record via `ThesisDeleteView`, THE System SHALL delete both the input and output files from disk within the same request, not deferred to a background task.
5. THE System SHALL provide a documented data retention policy specifying how long uploaded files, generated outputs, and user account data are retained before deletion.
6. WHERE the platform serves users in the European Union, THE System SHALL include a privacy notice accessible from all pages describing what data is collected, how it is used, and the user's rights under GDPR.

---

### Requirement 13: CSRF Protection Audit

**User Story:** As a security engineer, I want every state-changing endpoint to enforce CSRF protection, so that cross-site request forgery attacks cannot be executed against authenticated users.

#### Acceptance Criteria

1. THE System SHALL audit every POST, PUT, PATCH, and DELETE endpoint to confirm that `CsrfViewMiddleware` is active and no view is decorated with `@csrf_exempt` without documented justification and compensating controls.
2. WHEN a POST endpoint is consumed by JavaScript (AJAX/fetch), THE System SHALL use the `X-CSRFToken` header strategy and SHALL document the token acquisition pattern in a shared utility.
3. THE System SHALL enforce CSRF validation on all WebSocket upgrade handshakes by verifying the session-bound CSRF token before accepting the connection.
4. THE System SHALL NOT use `SameSite=None` on the CSRF cookie unless cross-origin embedding is explicitly required and the endpoint is scoped to the `/embed/` namespace.
5. THE System SHALL produce a complete inventory of all `@csrf_exempt` usages in the codebase; each exemption SHALL have a written justification and an alternative compensating control (e.g., signed token, HMAC verification).

---

### Requirement 14: SSRF Protection

**User Story:** As a security engineer, I want all outbound HTTP requests initiated by the server to be restricted to allowlisted destinations, so that attackers cannot use the platform to probe internal infrastructure or exfiltrate data via server-side request forgery.

#### Acceptance Criteria

1. WHEN the System makes any outbound HTTP request (e.g., fetching a URL supplied by a user or a third-party webhook), THE System SHALL validate the resolved IP address against a blocklist that includes all RFC 1918 private ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), loopback (127.0.0.0/8), link-local (169.254.0.0/16), and the Docker internal network range before completing the request.
2. THE System SHALL maintain an explicit allowlist of permitted external domains for outbound requests; any domain not on the allowlist SHALL be rejected with a logged security event.
3. WHEN parsing uploaded PDF or image files, THE System SHALL disable external entity resolution (XXE) and SHALL NOT follow embedded URLs or remote resource references within the document.
4. THE System SHALL enforce a connection timeout of no more than 10 seconds and a read timeout of no more than 30 seconds on all outbound HTTP requests to prevent slow-loris-style resource exhaustion.
5. THE System SHALL resolve hostnames to IP addresses before making requests and SHALL re-validate the resolved IP after DNS resolution to prevent DNS rebinding attacks.

---

### Requirement 15: XSS Protection

**User Story:** As a security engineer, I want all user-supplied content to be safely escaped or sanitised before rendering, so that stored, reflected, and DOM-based XSS attacks cannot execute in users' browsers.

#### Acceptance Criteria

1. THE System SHALL audit all Django templates to confirm that user-supplied variables are rendered with Django's auto-escaping active and that no template uses `{{ variable | safe }}` or `{% autoescape off %}` without documented justification.
2. WHEN user-supplied content is rendered as HTML (e.g., thesis titles, generation prompts displayed back to the user), THE System SHALL use `bleach` or an equivalent allowlist-based HTML sanitiser to strip disallowed tags and attributes before rendering.
3. WHEN markdown content is rendered to HTML (e.g., generated thesis sections), THE System SHALL sanitise the resulting HTML output using an allowlist sanitiser after markdown-to-HTML conversion, before serving to the browser.
4. THE System SHALL set `Content-Security-Policy` to disallow inline scripts (`script-src` without `'unsafe-inline'`) and SHALL use nonces or hashes for any legitimate inline scripts.
5. WHEN JSON data is embedded in a `<script>` tag within a Django template (e.g., for passing server-side data to JavaScript), THE System SHALL use `json_script` template filter rather than raw `{{ variable | safe }}` interpolation.
6. THE System SHALL audit all JavaScript files for DOM XSS sinks (`innerHTML`, `document.write`, `eval`, `setTimeout` with string argument) and SHALL replace unsafe patterns with safe DOM manipulation APIs.

---

### Requirement 16: SQL Injection and ORM Safety

**User Story:** As a security engineer, I want all database interactions to use parameterised queries, so that SQL injection attacks cannot manipulate the database through user-supplied input.

#### Acceptance Criteria

1. THE System SHALL audit the entire codebase for any use of `raw()`, `RawSQL()`, `extra()`, or direct string formatting into SQL and SHALL replace all such usages with ORM equivalents or properly parameterised `raw()` calls with explicit `params` argument.
2. WHEN dynamic ordering is applied to a queryset (e.g., `order_by(request.GET['sort'])`), THE Validator SHALL validate the ordering field against an explicit allowlist of permitted field names before applying it to the queryset.
3. WHEN queryset filtering uses user-supplied field names (e.g., `filter(**{user_field: value})`), THE Validator SHALL validate the field name against an allowlist before constructing the filter kwargs.
4. THE System SHALL audit all uses of `annotate()`, `aggregate()`, and `values()` with user-supplied arguments to confirm no unsanitised input reaches the SQL layer.
5. THE System SHALL configure the database user used by the Django application to have only SELECT, INSERT, UPDATE, DELETE privileges and SHALL NOT grant DDL privileges (CREATE, DROP, ALTER) to the application database user.

---

### Requirement 17: Celery and Task Queue Security

**User Story:** As a security engineer, I want the Celery task queue to be hardened against abuse, so that attackers cannot inject malicious tasks, exhaust worker resources, or replay task messages.

#### Acceptance Criteria

1. WHEN a Celery task is enqueued with user-supplied arguments, THE System SHALL validate and sanitise all task arguments at the point of enqueueing, before the task is serialised to the queue.
2. THE System SHALL configure Celery to use JSON serialisation exclusively (`task_serializer = 'json'`, `accept_content = ['json']`) and SHALL NOT use pickle serialisation, which allows arbitrary code execution.
3. THE System SHALL set a maximum task execution time (`task_time_limit`) of no more than 300 seconds and a soft time limit (`task_soft_time_limit`) of 270 seconds to prevent runaway tasks from exhausting worker resources.
4. THE System SHALL configure per-user rate limits on generation tasks to prevent a single user from monopolising the worker pool; no user SHALL be able to have more than 3 concurrent generation tasks in flight.
5. THE Redis broker SHALL be configured with authentication (`requirepass`) and the Celery broker URL SHALL include the password credential; the broker SHALL NOT be accessible from outside the Docker internal network.
6. THE System SHALL implement task result expiry (`result_expires`) of no more than 24 hours to prevent unbounded growth of the result backend.
7. WHEN a task fails with an unhandled exception, THE Celery_Worker SHALL log the error with structured fields (task ID, task name, user ID if available) but SHALL NOT log task argument values that may contain sensitive user data.

---

### Requirement 18: AI/LLM Abuse Protection

**User Story:** As a security engineer, I want the AI generation pipeline to be protected against jailbreaking, prompt injection, token exhaustion, and model abuse, so that the platform cannot be weaponised to generate harmful content or incur runaway API costs.

#### Acceptance Criteria

1. WHEN user-supplied text is included in a prompt sent to the Anthropic API, THE System SHALL apply a multi-layer prompt injection filter that detects and neutralises instruction override patterns, role-switching attempts, and delimiter injection before the prompt is dispatched.
2. THE System SHALL enforce a maximum input token budget per generation request (e.g., 8,000 tokens) and SHALL reject requests that exceed this budget with an HTTP 400 response before making any API call.
3. THE System SHALL enforce a per-user daily token consumption limit and SHALL disable generation for a user who exceeds the limit until the next UTC day, logging the event as a security alert.
4. THE System SHALL implement output filtering on all LLM responses to detect and redact content that matches patterns for PII (email addresses, phone numbers, credit card numbers) before storing or returning the response.
5. THE System SHALL log all generation requests with a truncated prompt hash (not the full prompt), the model used, token counts, and the user ID to enable abuse investigation without storing sensitive prompt content.
6. THE System SHALL implement a prompt isolation strategy that uses system-prompt separation to prevent user content from overriding system instructions, using the Anthropic API's `system` parameter exclusively for system instructions.
7. WHEN the Anthropic API returns an error indicating content policy violation, THE System SHALL log the event as a security alert and SHALL increment the user's violation counter; users exceeding 3 violations in 24 hours SHALL have generation temporarily suspended.

---

### Requirement 19: Resource Exhaustion and DoS Protection

**User Story:** As a security engineer, I want hard resource limits enforced at every layer, so that a single user or request cannot exhaust server CPU, RAM, or disk resources.

#### Acceptance Criteria

1. THE System SHALL enforce a hard upload size cap of 20 MB at the Django middleware layer (before the view is invoked) in addition to the Nginx `client_max_body_size` directive, rejecting oversized requests with HTTP 413.
2. WHEN a PDF or document file is parsed (e.g., for thesis processing), THE System SHALL enforce a maximum page count of 500 pages and a maximum extracted text size of 5 MB; files exceeding these limits SHALL be rejected before processing begins.
3. THE System SHALL set a per-request CPU timeout using `signal.alarm` or an equivalent mechanism for synchronous processing tasks, terminating requests that exceed 60 seconds of processing time.
4. THE System SHALL limit generation concurrency to a configurable maximum number of simultaneous active generation jobs per deployment (default: 20), returning HTTP 503 with a `Retry-After` header when the limit is reached.
5. THE Nginx configuration SHALL set `client_body_timeout`, `client_header_timeout`, `keepalive_timeout`, and `send_timeout` to prevent slow-client attacks.
6. THE System SHALL implement exponential backoff and a circuit breaker pattern for calls to the Anthropic API, preventing cascading failures from propagating to the user-facing request pool.

---

### Requirement 20: Admin Panel Hardening

**User Story:** As a security engineer, I want the Django admin interface to be hardened with URL obfuscation, IP restriction, MFA-readiness, and action logging, so that it cannot be discovered or accessed by unauthorised parties.

#### Acceptance Criteria

1. THE Django admin URL SHALL be changed from the default `/admin/` path to a non-guessable path configured via an environment variable; the default path SHALL return HTTP 404.
2. THE System SHALL restrict access to the admin interface to requests originating from allowlisted IP addresses or CIDR ranges, configured via an environment variable; requests from non-allowlisted IPs SHALL receive HTTP 404 (not 403, to avoid disclosing the admin path).
3. THE System SHALL be architected to support MFA for admin users; the admin authentication flow SHALL be compatible with `django-otp` or an equivalent TOTP library without requiring a full authentication rewrite.
4. THE System SHALL log all Django admin actions (create, update, delete) to a structured audit log including the admin user ID, action type, affected model, object ID, and timestamp; this log SHALL be append-only and SHALL NOT be accessible via the admin interface itself.
5. THE admin interface SHALL enforce a separate, shorter session timeout (30 minutes of inactivity) compared to the standard user session.

---

### Requirement 21: Audit Logging and Security Event Tracking

**User Story:** As a security engineer, I want a comprehensive, tamper-evident audit log of all security-relevant events, so that incidents can be investigated and compliance obligations can be met.

#### Acceptance Criteria

1. THE System SHALL emit structured audit log events (JSON format) for the following security-relevant actions: user login (success/failure), user logout, password change, account deletion, file upload, generation job submission, admin action, rate limit trigger, and CSRF validation failure.
2. WHEN a login attempt fails, THE System SHALL log the username attempted (truncated to 64 characters), the source IP address, the user agent, and a timestamp; it SHALL NOT log the submitted password.
3. THE System SHALL track and log suspicious generation patterns, including: more than 5 generation requests within 60 seconds from a single user, generation requests containing known jailbreak patterns, and generation requests that trigger Anthropic content policy violations.
4. THE audit log SHALL be written to a separate log sink from the application log and SHALL be configured as append-only; the application database user SHALL NOT have DELETE or UPDATE privileges on the audit log table.
5. THE System SHALL retain audit logs for a minimum of 90 days and SHALL provide a mechanism to export audit logs in a machine-readable format for compliance review.

---

### Requirement 22: Backup and Disaster Recovery

**User Story:** As a security engineer, I want database backups to be encrypted, regularly tested, and recoverable, so that data loss or ransomware cannot permanently destroy user data.

#### Acceptance Criteria

1. THE System SHALL implement automated daily database backups using `pg_dump` or an equivalent mechanism; backups SHALL be encrypted at rest using AES-256 before being written to the backup destination.
2. THE System SHALL retain daily backups for a minimum of 30 days and weekly backups for a minimum of 12 weeks.
3. THE System SHALL implement a documented restore verification procedure that is executed at least monthly; the procedure SHALL confirm that a backup can be restored to a staging environment and that data integrity checks pass.
4. THE System SHALL implement a DB snapshot rotation policy that automatically deletes backups older than the retention window to prevent unbounded storage growth.
5. THE System SHALL document a secret recovery plan specifying how to rotate all secrets (SECRET_KEY, ANTHROPIC_API_KEY, DATABASE_URL, REDIS_URL) in the event of a credential compromise, including the steps to invalidate all active sessions after SECRET_KEY rotation.

---

### Requirement 23: Supply Chain Security

**User Story:** As a security engineer, I want the software supply chain to be hardened against dependency confusion, typosquatting, and malicious package injection, so that the build pipeline cannot be compromised through third-party packages.

#### Acceptance Criteria

1. THE System SHALL pin all Python dependencies to exact versions with SHA-256 hashes in `requirements.txt` (using `pip-compile --generate-hashes` or equivalent) to prevent tampered packages from being installed.
2. THE CI/CD pipeline SHALL run `pip-audit` or `safety check` on every pull request and SHALL block merges when packages with HIGH or CRITICAL CVEs are detected.
3. THE CI/CD pipeline SHALL integrate GitHub secret scanning (or equivalent) to detect accidental commits of API keys, tokens, or credentials; the pipeline SHALL block merges when secrets are detected.
4. THE System SHALL validate that all packages are sourced from PyPI (the official index) and SHALL configure `pip` with `--index-url https://pypi.org/simple/` and `--no-index` for any packages sourced from private indexes.
5. THE System SHALL document a process for reviewing the changelog and diff of any dependency upgrade before merging, with particular scrutiny for packages with access to the file system, network, or subprocess execution.

---

### Requirement 24: Production Environment Isolation

**User Story:** As a security engineer, I want development, staging, and production environments to be strictly isolated, so that debug tooling, test credentials, and development shortcuts cannot leak into production.

#### Acceptance Criteria

1. THE System SHALL use separate environment variable files (`.env.development`, `.env.staging`, `.env.production`) and SHALL validate at startup that the `ENVIRONMENT` variable matches the expected value for the deployment context.
2. THE System SHALL enforce that `DEBUG = False` in all staging and production environments; the application SHALL refuse to start if `DEBUG = True` and `ENVIRONMENT` is not `development`.
3. THE System SHALL validate all required environment variables at startup using a startup check (e.g., Django system check framework) and SHALL refuse to start with a descriptive error if any required variable is absent or set to a known-insecure default value.
4. THE System SHALL NOT include `django-debug-toolbar`, `django-extensions`, or any other development-only package in the production Docker image; the Dockerfile SHALL use a multi-stage build to exclude dev dependencies.
5. THE System SHALL ensure that test fixtures, seed data scripts, and factory functions are not importable or executable in the production environment.
