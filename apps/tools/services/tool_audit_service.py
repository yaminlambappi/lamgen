"""
Tool Health Audit — Playwright-based checks for all LamGen tools.

Designed for 300+ tools: batched async navigation, semaphore-limited parallelism,
retries, structured JSON + HTML reports, and actionable fix hints.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.parse import urlparse

from django.conf import settings
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist

logger = logging.getLogger("tools.audit")

# Playwright audit browser engines (see --browser on audit_tools command)
AUDIT_BROWSER_CHROME = "chrome"
AUDIT_BROWSER_CHROMIUM = "chromium"
AUDIT_BROWSER_FIREFOX = "firefox"
AUDIT_BROWSER_CHOICES: tuple[str, ...] = (
    AUDIT_BROWSER_CHROME,
    AUDIT_BROWSER_CHROMIUM,
    AUDIT_BROWSER_FIREFOX,
)

# Flags suited for Ubuntu, headless VPS, Docker, and CI (Chromium-compatible engines only)
CHROMIUM_COMMON_LAUNCH_ARGS: list[str] = [
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu",
]


def resolve_system_chrome_executable() -> str | None:
    """
    Locate a system Google Chrome / Chrome Stable binary.

    Order: PATH (google-chrome, google-chrome-stable), then /usr/bin paths
    required on stock Ubuntu/Debian installs.
    """
    for name in ("google-chrome", "google-chrome-stable"):
        resolved = shutil.which(name)
        if resolved and os.path.isfile(resolved) and os.access(resolved, os.X_OK):
            return resolved
    for path in ("/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


async def _launch_playwright_browser(
    p: Any,
    *,
    engine: str,
    headless: bool,
    chrome_executable: str | None,
) -> Any:
    """
    Launch Playwright browser for audits.

    * chrome — system Chrome via chromium.launch(executable_path=…)
    * chromium — Playwright-managed Chromium (requires `playwright install chromium`)
    * firefox — Playwright-managed Firefox (requires `playwright install firefox`)
    """
    if engine == AUDIT_BROWSER_CHROME:
        if not chrome_executable:
            raise ValueError("chrome_executable is required when engine is chrome")
        browser = await p.chromium.launch(
            executable_path=chrome_executable,
            headless=headless,
            args=list(CHROMIUM_COMMON_LAUNCH_ARGS),
        )
        logger.info("Using browser: Google Chrome (%s)", chrome_executable)
        return browser
    if engine == AUDIT_BROWSER_CHROMIUM:
        browser = await p.chromium.launch(
            headless=headless,
            args=list(CHROMIUM_COMMON_LAUNCH_ARGS),
        )
        logger.info("Using browser: Playwright Chromium (bundled; playwright-managed)")
        return browser
    if engine == AUDIT_BROWSER_FIREFOX:
        browser = await p.firefox.launch(headless=headless)
        logger.info("Using browser: Playwright Firefox (bundled; playwright-managed)")
        return browser
    raise ValueError(f"Unsupported browser engine: {engine!r}")

STATUS_HEALTHY = "healthy"
STATUS_WARNING = "warning"
STATUS_BROKEN = "broken"


@dataclass
class ToolAuditRow:
    category_slug: str
    category_name: str
    tool_slug: str
    tool_name: str
    url: str
    status: str
    http_status: int | None
    load_time_ms: float | None
    load_time_mobile_ms: float | None = None
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    network_failures: list[str] = field(default_factory=list)
    runtime_hints: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    suggested_fixes: list[str] = field(default_factory=list)
    template_file_missing: bool = False
    template_fallback_used: bool = False
    mobile_horizontal_overflow: bool = False
    sparse_main_content: bool = False
    navigation_error: str | None = None
    screenshot_path: str | None = None
    api_probe_note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _reports_root() -> Path:
    return Path(settings.BASE_DIR) / "reports" / "tool_health"


def template_on_disk_exists(template_name: str) -> bool:
    """Return True if templates/<template_name> exists under BASE_DIR."""
    rel = template_name.lstrip("/").replace("..", "")
    path = Path(settings.BASE_DIR) / "templates" / rel
    return path.is_file()


def django_template_resolves(template_name: str) -> bool:
    """Synchronous Django template loader check — call only from sync code."""
    try:
        get_template(template_name)
        return True
    except TemplateDoesNotExist:
        return False


def materialize_tools_for_audit(qs) -> list[Any]:
    """
    Evaluate the Tool queryset in a synchronous context (never inside async).

    Caller must use select_related('category') on the queryset to avoid N+1
    when later reading category fields from in-memory instances.
    """
    return list(qs.order_by("category__order", "order", "id"))


def prepare_tool_audit_sync(base_url: str, tools: Sequence[Any]) -> tuple[str, dict[int, str], dict[int, dict[str, bool]]]:
    """
    All Django-adjacent work that must not run inside an async coroutine:
    URL reversing and template resolution for each tool.

    Returns (base_origin, urls_by_tool_pk, template_meta_by_tool_pk).
    """
    base_url = (base_url or "").rstrip("/")
    base_origin = _origin(base_url if base_url.startswith("http") else f"http://{base_url}")
    urls_by_pk: dict[int, str] = {}
    template_by_pk: dict[int, dict[str, bool]] = {}
    for t in tools:
        rel = t.get_absolute_url()
        urls_by_pk[t.pk] = f"{base_origin}{rel}" if rel.startswith("/") else rel
        template_by_pk[t.pk] = {
            "on_disk": template_on_disk_exists(t.template_name),
            "resolves": django_template_resolves(t.template_name),
        }
    return base_origin, urls_by_pk, template_by_pk


def classify_status(
    http_status: int | None,
    navigation_error: str | None,
    page_errors: Sequence[str],
    console_errors: Sequence[str],
    network_failures: Sequence[str],
    template_problem: bool,
) -> str:
    if navigation_error or http_status in (None, 0) or (http_status and http_status >= 500):
        return STATUS_BROKEN
    if http_status and http_status >= 400:
        return STATUS_BROKEN
    if page_errors:
        return STATUS_BROKEN
    if template_problem:
        return STATUS_WARNING
    if network_failures or len(console_errors) > 3:
        return STATUS_WARNING
    if console_errors:
        return STATUS_WARNING
    return STATUS_HEALTHY


def build_suggested_fixes(row: ToolAuditRow) -> list[str]:
    hints: list[str] = []
    if row.http_status == 404:
        hints.append("Verify Tool.is_active, ToolCategory.slug, and URL routing; run seed_tools if DB is stale.")
    if row.http_status and row.http_status >= 500:
        hints.append("Inspect Django server logs for this path — likely view or template render exception.")
    if row.navigation_error:
        hints.append(f"Navigation failed ({row.navigation_error[:120]}…): check server is up, TLS, and --base-url.")
    if row.template_file_missing:
        hints.append(
            "Add the template file under templates/ matching Tool.template_name, or update the tool row in admin/seed."
        )
        hints.append("If intentional, generic_tool.html is used — improve the dedicated template for UX.")
    if row.page_errors:
        hints.append("JS exception on load: open DevTools Sources, fix the script referenced in the stack trace.")
    if any("alpine" in e.lower() for e in row.console_errors + row.page_errors):
        hints.append("Alpine.js: check x-data scope, undefined identifiers, and script load order (defer).")
    if any("htmx" in e.lower() for e in row.console_errors + row.page_errors):
        hints.append("HTMX: verify hx-* targets exist, CSRF token on POST, and response is valid HTML fragment.")
    if any("tailwind" in e.lower() for e in row.console_errors):
        hints.append("Tailwind/build: confirm CDN or built CSS is reachable; purge may have stripped classes.")
    if row.network_failures:
        if any("/tools/api/" in f for f in row.network_failures):
            hints.append("Tool API returned error: confirm endpoint URL, request schema, and server-side handler.")
        if any("401" in f or "403" in f for f in row.network_failures):
            hints.append("Auth required on API: tool may need session or API key — audit server auth for this route.")
    if row.load_time_ms and row.load_time_ms > 8000:
        hints.append("Slow load: profile static assets, database queries in view, and third-party scripts.")
    if row.mobile_horizontal_overflow:
        hints.append("Mobile overflow: audit wide tables, min-width, and long unbroken strings in CSS.")
    if row.sparse_main_content:
        hints.append("Sparse main region: verify template extends tool_base and primary UI is inside <main>.")
    return list(dict.fromkeys(hints))  # dedupe, preserve order


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


async def _audit_single_page(
    *,
    page,
    url: str,
    base_origin: str,
    timeout_ms: int,
) -> dict[str, Any]:
    console_errors: list[str] = []
    page_errors: list[str] = []
    network_failures: list[str] = []
    runtime_hints: list[str] = []

    def on_console(msg) -> None:
        try:
            if msg.type == "error":
                text = msg.text
                console_errors.append(text)
                low = text.lower()
                if "alpine" in low:
                    runtime_hints.append("Alpine-related console error")
                if "htmx" in low:
                    runtime_hints.append("HTMX-related console error")
                if "tailwind" in low:
                    runtime_hints.append("Tailwind-related console error")
        except Exception:
            pass

    def on_page_error(exc) -> None:
        page_errors.append(str(exc))

    def on_response(resp) -> None:
        try:
            u = resp.url
            if not u.startswith(base_origin):
                return
            if resp.request.resource_type in ("image", "media", "font"):
                return
            st = resp.status
            if st >= 400:
                network_failures.append(f"{st} {resp.request.method} {u}")
        except Exception:
            pass

    def on_request_failed(request) -> None:
        try:
            u = request.url
            if not u.startswith(base_origin):
                return
            fail = request.failure
            if isinstance(fail, str):
                msg = fail
            elif fail is not None:
                msg = getattr(fail, "error_text", None) or str(fail)
            else:
                msg = "request_failed"
            network_failures.append(f"FAILED {request.method} {u} ({msg})")
        except Exception:
            pass

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)

    nav_error = None
    http_status = None
    t0 = time.perf_counter()
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        http_status = resp.status if resp else None
    except Exception as exc:  # noqa: BLE001 — surface to report
        nav_error = f"{type(exc).__name__}: {exc}"
        logger.warning("audit navigation failed url=%s err=%s", url, nav_error)
    load_ms = (time.perf_counter() - t0) * 1000

    # Allow in-flight XHR/fetch to settle (HTMX, APIs)
    try:
        await page.wait_for_load_state("networkidle", timeout=min(10_000, timeout_ms))
    except Exception:
        pass

    template_fallback_used = False
    sparse_main = False
    overflow = False
    if not nav_error:
        try:
            body_html = await page.content()
            if "generic_tool.html" in body_html or "generic-tool" in body_html.lower():
                # Heuristic: generic fallback often has distinct copy; keep light check
                template_fallback_used = "generic_tool" in body_html or "Coming soon" in body_html
            main_text_len = await page.evaluate(
                """() => {
                    const m = document.querySelector('main, [role="main"], .tool-body, .tool-page, article');
                    const el = m || document.body;
                    return (el && el.innerText) ? el.innerText.replace(/\\s+/g, ' ').trim().length : 0;
                }"""
            )
            sparse_main = main_text_len < 40
            overflow = await page.evaluate(
                """() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 16"""
            )
        except Exception as exc:
            logger.debug("audit post-eval failed url=%s: %s", url, exc)

    return {
        "http_status": http_status,
        "load_time_ms": load_ms,
        "console_errors": console_errors[:50],
        "page_errors": page_errors[:20],
        "network_failures": network_failures[:40],
        "runtime_hints": list(dict.fromkeys(runtime_hints)),
        "navigation_error": nav_error,
        "template_fallback_used": template_fallback_used,
        "sparse_main_content": sparse_main,
        "mobile_horizontal_overflow": overflow,
    }


async def _audit_with_retry(
    *,
    browser,
    url: str,
    base_origin: str,
    timeout_ms: int,
    viewport: dict[str, int],
    retries: int,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Returns (desktop_result, mobile_metrics_or_none)."""
    last_desktop: dict[str, Any] | None = None
    for attempt in range(retries):
        context = await browser.new_context(
            viewport=viewport,
            ignore_https_errors=True,
            java_script_enabled=True,
        )
        page = await context.new_page()
        try:
            last_desktop = await _audit_single_page(
                page=page,
                url=url,
                base_origin=base_origin,
                timeout_ms=timeout_ms,
            )
        finally:
            await context.close()
        if not last_desktop.get("navigation_error"):
            break
        if attempt < retries - 1:
            await asyncio.sleep(0.6 * (attempt + 1))

    assert last_desktop is not None
    mobile_extra: dict[str, Any] | None = None
    if not last_desktop.get("navigation_error"):
        mctx = await browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True,
            ignore_https_errors=True,
        )
        mpage = await mctx.new_page()
        try:
            t0 = time.perf_counter()
            try:
                await mpage.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            except Exception:
                pass
            mobile_ms = (time.perf_counter() - t0) * 1000
            try:
                overflow = await mpage.evaluate(
                    """() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 16"""
                )
            except Exception:
                overflow = False
            mobile_extra = {"load_time_mobile_ms": mobile_ms, "mobile_horizontal_overflow": overflow}
        finally:
            await mctx.close()

    return last_desktop, mobile_extra


async def run_tool_audit(
    *,
    tools_list: Sequence[Any],
    base_origin: str,
    urls_by_tool_pk: dict[int, str],
    template_meta_by_tool_pk: dict[int, dict[str, bool]],
    headless: bool = True,
    engine: str = AUDIT_BROWSER_CHROME,
    chrome_executable: str | None = None,
    max_parallel: int = 4,
    timeout_ms: int = 35_000,
    retries: int = 2,
    capture_screenshots_for: frozenset[str] = frozenset({STATUS_BROKEN}),
    progress_callback: Callable[[int, int, str], None] | None = None,
    artifact_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Audit tools using Playwright (async only). All ORM/queryset/template-loader
    work must be done before calling this — pass pre-materialized tools_list and
    maps from prepare_tool_audit_sync().

    ``engine`` is one of AUDIT_BROWSER_CHROME, AUDIT_BROWSER_CHROMIUM, AUDIT_BROWSER_FIREFOX.
    For Chrome, pass ``chrome_executable`` from resolve_system_chrome_executable() (sync).
    """
    from playwright.async_api import async_playwright

    if engine not in AUDIT_BROWSER_CHOICES:
        raise ValueError(f"Invalid engine {engine!r}; expected one of {AUDIT_BROWSER_CHOICES}")
    if engine == AUDIT_BROWSER_CHROME and not chrome_executable:
        raise ValueError("chrome_executable is required when engine is chrome")

    tools_seq = list(tools_list)
    total = len(tools_seq)
    shot_root = artifact_dir or (_reports_root() / "latest_run")
    logger.info(
        "tool_audit start tools=%d base=%s parallel=%d engine=%s",
        total,
        base_origin,
        max_parallel,
        engine,
    )

    rows: list[ToolAuditRow] = []
    sem = asyncio.Semaphore(max(1, max_parallel))

    async with async_playwright() as p:
        browser = await _launch_playwright_browser(
            p,
            engine=engine,
            headless=headless,
            chrome_executable=chrome_executable,
        )
        try:

            async def one(tool: Any, idx: int) -> ToolAuditRow:
                async with sem:
                    if progress_callback:
                        progress_callback(idx + 1, total, tool.slug)
                    url = urls_by_tool_pk[tool.pk]
                    tmeta = template_meta_by_tool_pk[tool.pk]
                    desktop, mobile = await _audit_with_retry(
                        browser=browser,
                        url=url,
                        base_origin=base_origin,
                        timeout_ms=timeout_ms,
                        viewport={"width": 1280, "height": 720},
                        retries=retries,
                    )
                    on_disk = tmeta["on_disk"]
                    resolves = tmeta["resolves"]
                    desktop = dict(desktop)
                    desktop["template_file_missing"] = not on_disk
                    desktop["template_does_not_resolve"] = not resolves
                    template_problem = (not on_disk) or (not resolves)
                    status = classify_status(
                        desktop["http_status"],
                        desktop["navigation_error"],
                        desktop["page_errors"],
                        desktop["console_errors"],
                        desktop["network_failures"],
                        template_problem,
                    )
                    if mobile and mobile.get("mobile_horizontal_overflow"):
                        status = STATUS_WARNING if status == STATUS_HEALTHY else status

                    tmpl_missing = bool(
                        desktop.get("template_file_missing") or desktop.get("template_does_not_resolve")
                    )
                    if desktop.get("sparse_main_content") and status == STATUS_HEALTHY:
                        status = STATUS_WARNING

                    row = ToolAuditRow(
                        category_slug=tool.category.slug,
                        category_name=tool.category.name,
                        tool_slug=tool.slug,
                        tool_name=tool.name,
                        url=url,
                        status=status,
                        http_status=desktop.get("http_status"),
                        load_time_ms=round(desktop.get("load_time_ms") or 0, 2),
                        load_time_mobile_ms=round(mobile["load_time_mobile_ms"], 2) if mobile else None,
                        console_errors=desktop.get("console_errors") or [],
                        page_errors=desktop.get("page_errors") or [],
                        network_failures=desktop.get("network_failures") or [],
                        runtime_hints=desktop.get("runtime_hints") or [],
                        issues=[],
                        template_file_missing=tmpl_missing,
                        template_fallback_used=desktop.get("template_fallback_used", False),
                        mobile_horizontal_overflow=bool(mobile and mobile.get("mobile_horizontal_overflow")),
                        sparse_main_content=desktop.get("sparse_main_content", False),
                        navigation_error=desktop.get("navigation_error"),
                    )

                    # API probe note: same-origin /tools/api/ failures already in network_failures
                    api_fails = [n for n in row.network_failures if "/tools/api/" in n]
                    if api_fails:
                        row.api_probe_note = f"Tool API errors: {len(api_fails)} request(s) failed."

                    issues: list[str] = []
                    if row.navigation_error:
                        issues.append(f"navigation: {row.navigation_error}")
                    if row.http_status and row.http_status >= 400:
                        issues.append(f"HTTP {row.http_status}")
                    if row.page_errors:
                        issues.extend([f"pageerror: {e}" for e in row.page_errors[:5]])
                    if row.console_errors:
                        issues.extend([f"console: {e}" for e in row.console_errors[:5]])
                    if desktop.get("template_file_missing"):
                        issues.append(f"template file missing on disk: {tool.template_name}")
                    if desktop.get("template_does_not_resolve"):
                        issues.append(f"template not found by Django loader: {tool.template_name}")
                    if row.sparse_main_content:
                        issues.append("main content appears very sparse")
                    if row.mobile_horizontal_overflow:
                        issues.append("mobile horizontal overflow detected")
                    row.issues = issues
                    row.suggested_fixes = build_suggested_fixes(row)

                    # Screenshot for broken (and optionally warnings)
                    if row.status in capture_screenshots_for:
                        run_dir = shot_root
                        run_dir.mkdir(parents=True, exist_ok=True)
                        shot_dir = run_dir / "screenshots"
                        shot_dir.mkdir(parents=True, exist_ok=True)
                        fname = f"{row.category_slug}__{row.tool_slug}.png".replace("/", "_")
                        spath = shot_dir / fname
                        ctx = await browser.new_context(viewport={"width": 1280, "height": 720})
                        pg = await ctx.new_page()
                        try:
                            try:
                                await pg.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                                await pg.screenshot(path=str(spath), full_page=False)
                                row.screenshot_path = str(spath.relative_to(settings.BASE_DIR))
                            except Exception as exc:
                                logger.warning("screenshot failed %s: %s", url, exc)
                        finally:
                            await ctx.close()

                    return row

            tasks = [one(t, i) for i, t in enumerate(tools_seq)]
            rows = await asyncio.gather(*tasks)
        finally:
            await browser.close()

    by_cat: dict[str, dict[str, Any]] = {}
    for r in rows:
        c = r.category_slug
        if c not in by_cat:
            by_cat[c] = {
                "slug": r.category_slug,
                "name": r.category_name,
                "total": 0,
                "healthy": 0,
                "warning": 0,
                "broken": 0,
                "tools": [],
            }
        bucket = by_cat[c]
        bucket["total"] += 1
        if r.status == STATUS_HEALTHY:
            bucket["healthy"] += 1
        elif r.status == STATUS_WARNING:
            bucket["warning"] += 1
        else:
            bucket["broken"] += 1
        bucket["tools"].append(r.to_dict())

    broken_list = [r.to_dict() for r in rows if r.status == STATUS_BROKEN]
    warnings_list = [r.to_dict() for r in rows if r.status == STATUS_WARNING]

    summary = {
        "total": len(rows),
        "healthy": sum(1 for r in rows if r.status == STATUS_HEALTHY),
        "warning": sum(1 for r in rows if r.status == STATUS_WARNING),
        "broken": sum(1 for r in rows if r.status == STATUS_BROKEN),
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_origin,
        "summary": summary,
        "categories": list(by_cat.values()),
        "broken_tools": broken_list,
        "warnings": warnings_list,
        "all_tools": [r.to_dict() for r in rows],
    }
    logger.info(
        "tool_audit done total=%d healthy=%d warning=%d broken=%d",
        summary["total"],
        summary["healthy"],
        summary["warning"],
        summary["broken"],
    )
    return payload


def write_reports(payload: dict[str, Any], *, run_id: str | None = None) -> dict[str, str]:
    """Write JSON, HTML dashboard, and latest pointers. Returns paths written."""
    root = _reports_root()
    root.mkdir(parents=True, exist_ok=True)
    rid = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = root / rid
    run_dir.mkdir(parents=True, exist_ok=True)

    payload = {**payload, "run_id": rid}
    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    html = render_dashboard_html(payload)
    html_path = run_dir / "dashboard.html"
    html_path.write_text(html, encoding="utf-8")

    latest_json = root / "latest.json"
    latest_html = root / "latest_dashboard.html"
    latest_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_html.write_text(html, encoding="utf-8")

    meta = {
        "latest_run_dir": str(run_dir.relative_to(settings.BASE_DIR)),
        "run_id": rid,
        "generated_at": payload.get("generated_at"),
    }
    (root / "latest_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "run_id": rid,
        "run_json": str(json_path),
        "run_html": str(html_path),
        "latest_json": str(latest_json),
        "latest_html": str(latest_html),
    }


def render_dashboard_html(payload: dict[str, Any]) -> str:
    """Render standalone HTML dashboard (no Django request required for file open)."""
    try:
        tpl = get_template("tools/audit/dashboard.html")
        return tpl.render({"report": payload})
    except Exception:
        return _fallback_dashboard_html(payload)


def _fallback_dashboard_html(payload: dict[str, Any]) -> str:
    s = payload.get("summary", {})
    cats = payload.get("categories", [])
    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Tool Health</title>",
        "<style>body{font-family:system-ui;margin:24px;} .ok{color:green} .warn{color:#b58900} .bad{color:#c00}",
        "table{border-collapse:collapse;width:100%} td,th{border:1px solid #ccc;padding:6px;text-align:left}</style>",
        "</head><body>",
        f"<h1>Tool Health — {payload.get('generated_at', '')}</h1>",
        f"<p>Base: {payload.get('base_url', '')}</p>",
        f"<p>Total {s.get('total')} — <span class='ok'>{s.get('healthy')} healthy</span> — "
        f"<span class='warn'>{s.get('warning')} warnings</span> — <span class='bad'>{s.get('broken')} broken</span></p>",
        "<h2>By category</h2><table><tr><th>Category</th><th>Total</th><th>Healthy</th><th>Warning</th><th>Broken</th></tr>",
    ]
    for c in cats:
        parts.append(
            f"<tr><td>{c.get('name')}</td><td>{c.get('total')}</td>"
            f"<td>{c.get('healthy', 0)}</td><td>{c.get('warning', 0)}</td><td>{c.get('broken', 0)}</td></tr>"
        )
    parts.append("</table><h2>Broken tools</h2><ul>")
    for b in payload.get("broken_tools", []):
        parts.append(f"<li><strong>{b.get('tool_slug')}</strong> ({b.get('category_name')}) — {b.get('issues', [])[:2]}</li>")
    parts.append("</ul></body></html>")
    return "\n".join(parts)


def generate_fix_simple_issues_report(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Produce structured fix hints for --fix-simple-issues (no automatic code edits).
    """
    suggestions: list[dict[str, Any]] = []
    for row in payload.get("all_tools", []):
        slug = row.get("tool_slug")
        if row.get("template_file_missing"):
            suggestions.append(
                {
                    "tool": slug,
                    "kind": "missing_template",
                    "action": "Create template file under templates/ or update Tool.template_name in database.",
                }
            )
        if row.get("http_status") == 404:
            suggestions.append({"tool": slug, "kind": "missing_route", "action": "Confirm category/tool slugs and is_active flags match URL."})
        for nf in row.get("network_failures") or []:
            if "401" in nf or "403" in nf:
                suggestions.append({"tool": slug, "kind": "api_auth", "action": "Review API authentication for this tool's fetch calls."})
                break
        if row.get("load_time_ms", 0) > 10_000:
            suggestions.append({"tool": slug, "kind": "slow", "action": "Profile server TTFB and heavy static assets for this page."})
    return {"generated_at": payload.get("generated_at"), "suggestions": suggestions}


def write_fix_suggestions(payload: dict[str, Any], run_id: str) -> str:
    root = _reports_root()
    data = generate_fix_simple_issues_report(payload)
    path = root / run_id / "fix_suggestions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)
