# Design Document: Security Audit

## Overview

This document defines the technical design for hardening the LamGen platform prior to global production launch. The audit covers the full Django 4.2 / Celery 5.3 / Redis 7 / PostgreSQL 15 / Nginx stack, including authentication flows, file upload handling, WebSocket connections, AI generation pipeline, admin interface, and infrastructure configuration.

The design is grounded in a thorough scan of the actual codebase. Key findings that drive the architecture:

- `games/consumers.py`: `GameRoomConsumer.connect()` calls `self.accept()` unconditionally — **no authentication check**. This is a production-stopper.
- `nginx.conf`: `location /media/` serves all files under `/media/` directly, including `/media/uploads/` — **unauthenticated file access**. Production-stopper.
- `games/views.py`: `create_room`, `post_signal` are decorated with `@csrf_exempt` — **CSRF bypass** on state-changing endpoints.
- `accounts/views.py`: `login_view` has no rate limiting, no session fixation protection (no `request.session.cycle_key()`).
- `config/settings.py`: `SECRET_KEY` defaults to `"django-insecure-change-me-in-production"` with no startup guard. No `SESSION_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, or `Content-Security-Policy` configured.
- `docker-compose.yml`: PostgreSQL and Redis use hardcoded credentials (`postgres`/`postgres`). Redis has no `requirepass`. Both ports are not exposed to host (correct), but credentials are hardcoded.
- `Dockerfile`: Runs as root — no `USER` directive.
- `config/asgi.py`: ASGI application does not include Django Channels — WebSocket routing is incomplete/missing from the ASGI config.
- `generation/views.py`: `edit_outline` has no payload size limit before `json.loads(request.body)`.
- `seo/middleware.py`: `CrawlErrorMiddleware` writes the raw `HTTP_REFERER` header to a log file without sanitisation — **log injection**.
- No `Content-Security-Policy`, `Permissions-Policy`, `Referrer-Policy`, or `HSTS` headers anywhere in the stack.
- No prompt injection filtering in the generation pipeline.
- No SSRF guard on outbound HTTP calls.
- `tools/utils/rate_limit.py`: Rate limiting exists for the search endpoint only; login, registration, and generation endpoints are unprotected.


---

## Threat Model

### Threat Actors

| Actor | Capabilities | Goals |
|---|---|---|
| **External Attacker** | Unauthenticated HTTP/WebSocket access, automated scanners, public internet | Account takeover, data exfiltration, DoS, API cost exhaustion, XSS payload delivery |
| **Authenticated User** | Valid session, access to own resources, ability to craft malicious inputs | Access other users' files, exhaust AI token budget, inject prompts to manipulate LLM output, CSRF against other users |
| **Malicious Insider** | Admin credentials, database access, server access | Exfiltrate user data, tamper with audit logs, plant backdoors |
| **Compromised Dependency** | Code execution within the Python process, access to environment variables | Exfiltrate `ANTHROPIC_API_KEY`, `SECRET_KEY`, `DATABASE_URL`; establish persistence |
| **Rogue AI Prompt** | Ability to craft text that is included in Anthropic API calls | Override system instructions, extract system prompt, generate harmful content, cause policy violations |

### Threat Scenarios

1. **Unauthenticated WebSocket join**: Any visitor can connect to `ws/games/<any_code>/` and receive all game room messages, inject arbitrary payloads into the room broadcast.
2. **Direct media file access**: Any visitor can fetch `/media/uploads/<filename>` directly via Nginx, bypassing Django ownership checks entirely.
3. **CSRF on signaling endpoints**: `create_room` and `post_signal` are `@csrf_exempt` — a malicious page can create rooms and inject WebRTC signaling data on behalf of authenticated users.
4. **Session fixation**: Login does not call `request.session.cycle_key()`, allowing an attacker who plants a session cookie to hijack the session after the victim logs in.
5. **Open redirect**: `login_view` passes `request.GET.get('next', 'home')` directly to `redirect()` without validation — any external URL can be used as a redirect target.
6. **Prompt injection**: User-supplied text in thesis titles and assignment prompts is passed directly to the Anthropic API without sanitisation.
7. **Token exhaustion**: No per-user daily token limit; a single user can submit unlimited generation jobs, incurring unbounded API costs.
8. **Log injection**: `CrawlErrorMiddleware` writes raw `HTTP_REFERER` to a log file — an attacker can inject newlines to forge log entries.
9. **Default SECRET_KEY in production**: If `.env` is missing or misconfigured, the app starts with the insecure default key, making all sessions and CSRF tokens forgeable.
10. **Pickle deserialization**: While Celery is configured for JSON, the `CELERY_ACCEPT_CONTENT` setting must be enforced to prevent pickle-based RCE if the broker is compromised.

---

## Attack Surface Map

### HTTP Endpoints

| Endpoint | Auth Required | CSRF | Rate Limited | Risk |
|---|---|---|---|---|
| `POST /accounts/login/` | No | Yes | **No** | CRITICAL — brute force |
| `POST /accounts/register/` | No | Yes | **No** | HIGH — account spam |
| `POST /accounts/logout/` | No | Yes | No | LOW |
| `GET/POST /generation/submit/` | Yes | Yes | **No** | HIGH — token exhaustion |
| `GET /generation/<pk>/status/` | Yes | N/A | No | LOW |
| `GET /generation/<pk>/status.json` | Yes | N/A | No | LOW |
| `POST /generation/<pk>/confirm-outline/` | Yes | Yes | No | LOW |
| `POST /generation/<pk>/edit-outline/` | Yes | Yes | **No size limit** | HIGH — DoS |
| `GET/POST /thesis/upload/` | Yes | Yes | **No** | HIGH — token exhaustion |
| `GET /thesis/<pk>/status/` | Yes | N/A | No | LOW |
| `GET /thesis/<pk>/download/` | Yes | N/A | No | MEDIUM |
| `DELETE /thesis/<pk>/delete/` | Yes | Yes | No | LOW |
| `GET /tools/search/` | No | N/A | Yes (60/min) | LOW |
| `POST /tools/toggle-bookmark/` | Optional | **No for guests** | No | MEDIUM |
| `POST /tools/record-usage/` | Optional | Yes | No | LOW |
| `GET /admin/` | Yes (staff) | Yes | **No IP restriction** | CRITICAL |
| `POST /games/create-room/` | No | **@csrf_exempt** | No | HIGH |
| `POST /games/signal/<code>/` | No | **@csrf_exempt** | No | HIGH |
| `GET /games/signal/<code>/` | No | N/A | No | MEDIUM |
| `GET /media/uploads/*` | **None (Nginx)** | N/A | No | CRITICAL |
| `GET /media/outputs/*` | **None (Nginx)** | N/A | No | HIGH |

### WebSocket Connections

| Endpoint | Auth Check | Message Validation | Size Limit |
|---|---|---|---|
| `ws/games/<room_code>/` | **None** | **None** | **None** |

### File Upload Handlers

| Handler | MIME Check | Size Check | UUID Rename |
|---|---|---|---|
| `generation/submit_job` (POST) | Yes (python-magic) | Yes (20MB) | **No — Django FileField default** |
| `thesis/UploadView` (POST) | Via form validation | Via form | **No — Django FileField default** |

### Celery Task Inputs

| Task | Argument Validation | Serializer |
|---|---|---|
| `run_generation_pipeline(job_id)` | UUID only — safe | JSON |
| `continue_generation_pipeline(job_id)` | UUID only — safe | JSON |
| `process_thesis_task(thesis_id)` | Integer only — safe | JSON |
| `cleanup_old_generation_uploads()` | No args | JSON |
| `cleanup_old_uploads()` | No args | JSON |

### Admin Interface

- URL: `/admin/` (default, guessable)
- No IP restriction middleware
- No MFA
- No separate session timeout

### Nginx Proxy

- Port 80 only (no TLS termination in current config)
- `location /media/` serves all files including `/media/uploads/` without auth
- No `server_tokens off`
- No security headers (`X-Content-Type-Options`, `X-Frame-Options`, etc.)
- No rate limiting at proxy layer

### Outbound HTTP Calls

- Anthropic API calls via `anthropic` SDK — no SSRF guard needed (fixed endpoint)
- No user-supplied URLs currently trigger outbound requests, but the architecture must guard against future additions
- PDF parsing via PyMuPDF — external entity resolution risk

---

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│  PUBLIC INTERNET (UNTRUSTED)                                    │
│  - All HTTP/WebSocket requests                                  │
│  - User-supplied file content                                   │
│  - User-supplied text (prompts, titles, search queries)         │
└──────────────────────┬──────────────────────────────────────────┘
                       │ TLS (must be enforced)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  NGINX PROXY (SEMI-TRUSTED)                                     │
│  - Terminates TLS                                               │
│  - Rate limits volumetric attacks                               │
│  - Adds defence-in-depth security headers                       │
│  - MUST NOT serve /media/uploads/ directly                      │
│  - Trusted for X-Forwarded-For (sole entry point)               │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP (internal Docker network)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  DJANGO APPLICATION (TRUSTED — our code)                        │
│  - Enforces authentication and authorisation                    │
│  - Validates all inputs                                         │
│  - Enforces CSRF, rate limits, ownership checks                 │
│  - Sanitises outputs (XSS, log injection)                       │
│  - Emits audit log events                                       │
└──────────┬───────────────────────┬──────────────────────────────┘
           │                       │
           ▼                       ▼
┌──────────────────┐   ┌───────────────────────────────────────┐
│  CELERY WORKERS  │   │  REDIS BROKER/CACHE (SEMI-TRUSTED)    │
│  (TRUSTED)       │   │  - Must require password auth         │
│  - Validates     │   │  - Not exposed outside Docker network │
│    task args     │   │  - Stores session data, rate limit    │
│  - JSON only     │   │    counters, task results             │
│  - Time limits   │   └───────────────────────────────────────┘
└──────────┬───────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  POSTGRESQL (TRUSTED)                                           │
│  - Not exposed outside Docker network                           │
│  - App user has SELECT/INSERT/UPDATE/DELETE only                │
│  - Audit log table: no DELETE/UPDATE for app user               │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  ANTHROPIC API (EXTERNAL — UNTRUSTED RESPONSES)                 │
│  - Fixed endpoint — no SSRF risk from this call                 │
│  - Responses must be treated as untrusted content               │
│  - Output must be PII-filtered before storage                   │
│  - API key must never be logged                                 │
└─────────────────────────────────────────────────────────────────┘
```

**What is trusted at each boundary:**

- **Nginx → Django**: `X-Forwarded-For` is trusted (Nginx is the sole entry point). `X-Forwarded-Proto` is trusted (already configured via `SECURE_PROXY_SSL_HEADER`). All other headers are untrusted.
- **Django → Celery**: Task arguments are trusted only after validation at the enqueue point. The broker itself is semi-trusted (must be password-protected).
- **Django → PostgreSQL**: ORM queries are trusted. Raw SQL with user input is never trusted.
- **Django → Anthropic**: The API endpoint is trusted. The response content is untrusted (must be PII-filtered and output-sanitised).
- **Celery → Django DB**: Workers use the same Django ORM — same trust rules apply.


---

## Risk Severity Matrix

Each of the 24 requirement domains is classified by **Likelihood × Impact**.

| # | Domain | Likelihood | Impact | Severity | Current State | Justification |
|---|---|---|---|---|---|---|
| 1 | Authentication Security | HIGH | CRITICAL | **CRITICAL** | No rate limit, no session fixation fix, open redirect | Login brute force is trivially automated; session fixation enables account takeover |
| 2 | Secrets Management | HIGH | CRITICAL | **CRITICAL** | Default SECRET_KEY in settings.py, hardcoded DB creds in docker-compose | Leaked SECRET_KEY forges all sessions and CSRF tokens; leaked DB URL gives full data access |
| 3 | HTTP Security Headers | HIGH | HIGH | **HIGH** | No CSP, no HSTS, no Permissions-Policy anywhere | Missing CSP enables XSS; missing HSTS enables SSL stripping on first visit |
| 4 | Input Validation | MEDIUM | HIGH | **HIGH** | MIME check exists; no prompt injection filter; no payload size limit on edit_outline | Prompt injection can manipulate LLM output; oversized payloads can DoS workers |
| 5 | File Upload/Media Serving | HIGH | CRITICAL | **CRITICAL** | Nginx serves /media/ including /media/uploads/ without auth | Any user can access any other user's uploaded documents directly |
| 6 | WebSocket Security | HIGH | CRITICAL | **CRITICAL** | No auth check before accept(); no message validation; no size limit | Unauthenticated users can join any game room and inject arbitrary messages |
| 7 | API/Endpoint Authorization | LOW | HIGH | **HIGH** | @login_required present on generation/thesis views; games signaling is @csrf_exempt | CSRF-exempt endpoints allow cross-site state changes |
| 8 | Rate Limiting / DoS | HIGH | HIGH | **HIGH** | Only search endpoint has rate limiting | Login, registration, generation endpoints are fully unprotected |
| 9 | Dependency Vulnerabilities | MEDIUM | HIGH | **HIGH** | No pip-audit in CI; packages pinned but no hash verification | Known CVEs in dependencies can be exploited without detection |
| 10 | Infrastructure/Container | MEDIUM | HIGH | **HIGH** | Root user in Docker; hardcoded DB creds; no TLS in nginx.conf; Redis no password | Container escape gives root; hardcoded creds in version control |
| 11 | Error Handling / Info Leakage | LOW | MEDIUM | **MEDIUM** | DEBUG=False by default; error_message stored in DB but not fully sanitised | Raw exception messages stored in DB could leak file paths or internal details |
| 12 | Data Protection / Privacy | MEDIUM | HIGH | **HIGH** | No HTTPS redirect; no HSTS; PBKDF2 in use (correct) | No HTTPS enforcement means credentials sent in plaintext |
| 13 | CSRF Protection | HIGH | HIGH | **HIGH** | games/views.py has @csrf_exempt on create_room and post_signal | CSRF bypass on state-changing endpoints |
| 14 | SSRF Protection | LOW | HIGH | **HIGH** | No outbound HTTP from user-supplied URLs currently, but no guard exists | Future features or compromised dependencies could trigger SSRF |
| 15 | XSS Protection | MEDIUM | HIGH | **HIGH** | Django auto-escaping active; no bleach; no CSP; markdown rendered without sanitisation | Stored XSS via thesis titles or generated content rendered as HTML |
| 16 | SQL Injection / ORM Safety | LOW | CRITICAL | **HIGH** | ORM used throughout; no raw SQL found in scan | Low likelihood due to ORM usage, but dynamic ordering/filtering needs validation |
| 17 | Celery / Task Queue | MEDIUM | HIGH | **HIGH** | JSON serializer configured; no time limits set; no per-user concurrency limits | Runaway tasks can exhaust worker pool; no task time limits |
| 18 | AI/LLM Abuse | HIGH | HIGH | **HIGH** | No prompt injection filter; no token budget per user; no output PII filter | Token exhaustion attack can incur thousands of dollars in API costs |
| 19 | Resource Exhaustion / DoS | MEDIUM | HIGH | **HIGH** | 20MB file size check in generation views; no page count limit; no CPU timeout | Large PDFs can exhaust memory in Celery workers |
| 20 | Admin Panel Hardening | MEDIUM | CRITICAL | **CRITICAL** | Default /admin/ URL; no IP restriction; no MFA; no audit log | Admin panel discovery + credential stuffing = full platform compromise |
| 21 | Audit Logging | MEDIUM | HIGH | **HIGH** | Basic application logging exists; no structured security event log | Without audit logs, incident investigation is impossible |
| 22 | Backup / Disaster Recovery | LOW | HIGH | **MEDIUM** | No automated backup configuration found | Data loss risk; not a pre-launch blocker but must be addressed |
| 23 | Supply Chain Security | LOW | HIGH | **MEDIUM** | Exact version pinning present; no hash verification; no CI scanning | Dependency confusion attacks are low probability but high impact |
| 24 | Production Environment Isolation | MEDIUM | HIGH | **HIGH** | No startup validation of required env vars; no multi-stage Docker build | DEBUG=True in production would expose full stack traces |

---

## Mitigation Priority Tiers

### Tier 1 — Production Stoppers (Must fix before launch)

These vulnerabilities are either trivially exploitable or have catastrophic impact. The platform **must not go live** with any of these unresolved.

1. **WebSocket authentication** (Req 6.1): Add auth check before `self.accept()` in `GameRoomConsumer`. Close with code 4001 if unauthenticated.
2. **Nginx media serving** (Req 5.1): Remove `location /media/` block from nginx.conf. Serve all files through authenticated Django views using `X-Accel-Redirect`.
3. **Default SECRET_KEY guard** (Req 2.1): Add `StartupSecurityCheck` that raises `SystemCheckError` if `SECRET_KEY` matches the default and `DEBUG=False`.
4. **Session fixation** (Req 1.3): Call `request.session.cycle_key()` after successful login in `accounts/views.py`.
5. **Open redirect on login** (Req 1.4): Validate `next` parameter against same-origin paths only.
6. **Admin IP restriction** (Req 7.6, 20.2): Deploy `AdminIPRestrictionMiddleware` returning 404 for non-allowlisted IPs.
7. **Admin URL obfuscation** (Req 20.1): Move admin URL to env-var-configured non-guessable path.
8. **CSRF on games signaling** (Req 13.1): Remove `@csrf_exempt` from `create_room` and `post_signal`; implement HMAC-signed tokens as compensating control.
9. **Login rate limiting** (Req 1.1, 8.1): Deploy `RateLimiter` on login endpoint (10 attempts / 15 min per IP and per username).
10. **Redis password** (Req 10.6, 17.5): Configure Redis `requirepass` in docker-compose and update `REDIS_URL`.
11. **Non-root Docker user** (Req 10.1): Add `appuser` and `USER` directive to Dockerfile.
12. **Hardcoded DB credentials** (Req 2.5, 10.2): Remove hardcoded `POSTGRES_PASSWORD=postgres` from docker-compose; use Docker secrets or env file.

### Tier 2 — High Risk (Fix within 2 weeks of launch)

13. **HTTP security headers** (Req 3): Deploy `SecurityHeadersMiddleware` with CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
14. **Prompt injection filter** (Req 4.4, 18.1): Deploy `PromptInjectionFilter` on all text inputs sent to Anthropic API.
15. **Token budget enforcement** (Req 18.2, 18.3): Enforce per-request token budget (8,000 tokens) and per-user daily limit.
16. **Registration rate limiting** (Req 8.2): 5 requests/hour per IP.
17. **Generation job rate limiting** (Req 8.3): 10 jobs/hour per authenticated user.
18. **Thesis upload rate limiting** (Req 8.4): 5 uploads/hour per authenticated user.
19. **edit_outline payload size limit** (Req 4.5): Enforce 50KB limit before `json.loads()`.
20. **WebSocket message validation** (Req 6.2, 6.3, 6.5): Validate message schema, enforce 64KB size limit, validate room code pattern.
21. **Celery task time limits** (Req 17.3): Set `task_time_limit=300`, `task_soft_time_limit=270`.
22. **Celery per-user concurrency** (Req 17.4): Limit 3 concurrent generation tasks per user.
23. **Audit logger** (Req 21): Deploy `AuditLogger` for all security-relevant events.
24. **Log injection fix** (Req 11.5): Sanitise `HTTP_REFERER` in `CrawlErrorMiddleware`.
25. **SSRF guard** (Req 14): Deploy `SSRFGuard` for any outbound HTTP calls.
26. **XSS sanitisation** (Req 15.2, 15.3): Deploy `XSSSanitiser` using bleach on user-supplied HTML and markdown output.
27. **Nginx security headers** (Req 3.7, 10.4, 10.5): Add `server_tokens off`, `X-Content-Type-Options`, `X-Frame-Options` to nginx.conf.
28. **HTTPS enforcement** (Req 12.1, 10.3): Add TLS to nginx.conf; set `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=31536000`.

### Tier 3 — Medium Risk (Fix within 30 days)

29. **Dependency audit in CI** (Req 9.1, 9.4, 23.2): Integrate `pip-audit` and secret scanning into CI pipeline.
30. **Hash pinning in requirements.txt** (Req 23.1): Run `pip-compile --generate-hashes`.
31. **Multi-stage Docker build** (Req 24.4): Exclude dev dependencies from production image.
32. **Admin MFA readiness** (Req 20.3): Integrate `django-otp` for admin authentication.
33. **Admin audit log** (Req 20.4): Implement append-only admin action log.
34. **Admin session timeout** (Req 20.5): 30-minute inactivity timeout for admin sessions.
35. **Output PII filtering** (Req 18.4): Filter email addresses, phone numbers, credit card numbers from LLM responses.
36. **Backup automation** (Req 22.1, 22.2): Implement encrypted daily `pg_dump` with 30-day retention.
37. **Data retention policy** (Req 12.5): Document and implement retention policy.
38. **GDPR privacy notice** (Req 12.6): Add privacy notice accessible from all pages.
39. **Startup env var validation** (Req 24.3): Extend `StartupSecurityCheck` to validate all required env vars.
40. **Dynamic ordering allowlist** (Req 16.2, 16.3): Validate sort fields against explicit allowlists.

---

## Architecture

The security architecture follows a **layered defence** model. Security controls are implemented as reusable, horizontally scalable components — not scattered patches.

```
Request Flow:
  Internet → Nginx (TLS, rate limit, headers) 
           → Django Middleware Stack 
           → View (auth, CSRF, ownership) 
           → Service Layer (validation, sanitisation) 
           → ORM (parameterised queries)
           → PostgreSQL

Security Middleware Stack (ordered):
  1. SecurityMiddleware (Django built-in — HTTPS redirect, HSTS)
  2. WhiteNoiseMiddleware
  3. SecurityHeadersMiddleware (NEW — CSP, Referrer-Policy, Permissions-Policy)
  4. SessionMiddleware
  5. AdminIPRestrictionMiddleware (NEW — IP allowlist for /admin/)
  6. CommonMiddleware
  7. CsrfViewMiddleware
  8. CSRFAuditMiddleware (NEW — logs CSRF failures before raising)
  9. AuthenticationMiddleware
  10. MessageMiddleware
  11. XFrameOptionsMiddleware
  12. CrawlErrorMiddleware (PATCHED — sanitise HTTP_REFERER)
```

### Scalability Principles

All security controls are designed for horizontal scale:

- **Rate limiting**: Redis-backed sliding window counters — shared across all Django instances
- **Audit logging**: Append to a dedicated log sink (file or external service) — not the application DB
- **Session management**: Redis-backed sessions — shared across all instances
- **SSRF guard**: Pure Python IP validation — O(1), no external calls
- **Prompt injection filter**: In-memory regex pattern registry — O(n) where n is pattern count, not input size

