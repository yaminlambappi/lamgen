"""
Run automated browser health checks for all tools (Playwright).

Default browser is system Google Chrome (no ``playwright install chromium`` required).

Examples:
  python manage.py audit_tools --base-url=http://127.0.0.1:8000
  python manage.py audit_tools --browser=chromium   # bundled Chromium; run: python -m playwright install chromium
  python manage.py audit_tools --browser=firefox    # bundled Firefox; run: python -m playwright install firefox
  python manage.py audit_tools --category=developer-tools --workers=8
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from tools.models import Tool
from tools.services.tool_audit_service import (
    AUDIT_BROWSER_CHOICES,
    AUDIT_BROWSER_CHROME,
    AUDIT_BROWSER_CHROMIUM,
    AUDIT_BROWSER_FIREFOX,
    STATUS_BROKEN,
    STATUS_WARNING,
    materialize_tools_for_audit,
    prepare_tool_audit_sync,
    resolve_system_chrome_executable,
    run_tool_audit,
    write_fix_suggestions,
    write_reports,
)


class Command(BaseCommand):
    help = (
        "Playwright-based health audit for Tool pages (writes reports/tool_health/). "
        "Default: system Google Chrome. Use --browser=chromium|firefox for Playwright-managed browsers."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default="",
            help="Origin serving the site (default: SITE_URL from settings, else http://127.0.0.1:8000).",
        )
        parser.add_argument("--category", default="", help="Limit to ToolCategory.slug.")
        parser.add_argument("--tool", default="", help="Limit to Tool.slug (unique).")
        parser.add_argument(
            "--browser",
            choices=list(AUDIT_BROWSER_CHOICES),
            default=AUDIT_BROWSER_CHROME,
            help=(
                "Browser engine: chrome = system Google Chrome (default; no playwright install browsers); "
                "chromium = Playwright Chromium (requires: python -m playwright install chromium); "
                "firefox = Playwright Firefox (requires: python -m playwright install firefox)."
            ),
        )
        parser.add_argument(
            "--headless",
            action="store_true",
            default=True,
            help="Run browser headless (default: true).",
        )
        parser.add_argument(
            "--no-headless",
            action="store_true",
            help="Show browser window for debugging.",
        )
        parser.add_argument(
            "--parallel",
            action="store_true",
            help="Run concurrent audits (default on; use --workers to tune).",
        )
        parser.add_argument(
            "--no-parallel",
            action="store_true",
            help="Sequential audits (workers=1).",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=4,
            help="Max concurrent browser contexts (default 4).",
        )
        parser.add_argument(
            "--timeout-ms",
            type=int,
            default=35_000,
            help="Navigation timeout per attempt (default 35000).",
        )
        parser.add_argument(
            "--retries",
            type=int,
            default=2,
            help="Navigation retries per tool (default 2).",
        )
        parser.add_argument(
            "--screenshot-warnings",
            action="store_true",
            help="Also capture PNG screenshots for warning-level tools.",
        )
        parser.add_argument(
            "--fix-simple-issues",
            action="store_true",
            help="Write fix_suggestions.json (hints only; no auto code changes).",
        )
        parser.add_argument(
            "--fail-on-broken",
            action="store_true",
            help="Exit with code 1 if any tool is broken (for CI).",
        )

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

        base_url = (options["base_url"] or "").strip() or getattr(
            settings, "SITE_URL", "http://127.0.0.1:8000"
        )
        if not base_url.startswith("http"):
            base_url = f"http://{base_url}"

        qs = Tool.objects.filter(is_active=True, category__is_active=True).select_related("category")
        cat_slug = (options["category"] or "").strip()
        tool_slug = (options["tool"] or "").strip()
        if cat_slug:
            qs = qs.filter(category__slug=cat_slug)
        if tool_slug:
            qs = qs.filter(slug=tool_slug)

        tools_list = materialize_tools_for_audit(qs)
        if not tools_list:
            raise CommandError("No tools matched filters (check --category / --tool and DB seed).")

        headless = not options["no_headless"]
        max_parallel = 1 if options["no_parallel"] else max(1, int(options["workers"]))

        capture = frozenset({STATUS_BROKEN})
        if options["screenshot_warnings"]:
            capture = frozenset({STATUS_BROKEN, STATUS_WARNING})

        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        artifact_dir = Path(settings.BASE_DIR) / "reports" / "tool_health" / run_id

        def progress(cur: int, total: int, slug: str) -> None:
            self.stdout.write(f"[{cur}/{total}] {slug}")

        self.stdout.write(self.style.NOTICE(f"Auditing {len(tools_list)} tool(s) against {base_url} …"))

        base_origin, urls_by_pk, template_meta = prepare_tool_audit_sync(base_url, tools_list)

        engine = options["browser"]
        chrome_path: str | None = None
        if engine == AUDIT_BROWSER_CHROME:
            chrome_path = resolve_system_chrome_executable()
            if not chrome_path:
                raise CommandError(
                    "Google Chrome was not found on this system.\n"
                    "Checked: PATH (google-chrome, google-chrome-stable), "
                    "/usr/bin/google-chrome, /usr/bin/google-chrome-stable.\n\n"
                    "Install (Debian/Ubuntu example):\n"
                    "  sudo apt-get update && sudo apt-get install -y google-chrome-stable\n\n"
                    "Or use Playwright's bundled Chromium (one-time download):\n"
                    "  python manage.py audit_tools --browser=chromium\n"
                    "  python -m playwright install chromium\n"
                )

        try:
            payload = asyncio.run(
                run_tool_audit(
                    tools_list=tools_list,
                    base_origin=base_origin,
                    urls_by_tool_pk=urls_by_pk,
                    template_meta_by_tool_pk=template_meta,
                    headless=headless,
                    engine=engine,
                    chrome_executable=chrome_path,
                    max_parallel=max_parallel,
                    timeout_ms=int(options["timeout_ms"]),
                    retries=int(options["retries"]),
                    capture_screenshots_for=capture,
                    progress_callback=progress,
                    artifact_dir=artifact_dir,
                )
            )
        except ImportError as exc:
            raise CommandError(
                "Playwright is not installed. Install the `playwright` package:\n"
                "  pip install playwright\n"
                "For --browser=chromium or firefox, also run the matching `playwright install` command."
            ) from exc
        except Exception as exc:
            err = str(exc)
            if "Executable doesn't exist" in err or "playwright install" in err.lower():
                if engine == AUDIT_BROWSER_CHROME:
                    raise CommandError(
                        "Playwright failed to launch system Google Chrome.\n"
                        f"Detail: {err[:600]}\n\n"
                        "Reinstall Chrome or try --browser=chromium with:\n"
                        "  python -m playwright install chromium"
                    ) from exc
                install_hint = (
                    "python -m playwright install chromium"
                    if engine == AUDIT_BROWSER_CHROMIUM
                    else "python -m playwright install firefox"
                )
                raise CommandError(
                    "Playwright browser binaries are missing or do not match your installed playwright package.\n"
                    f"Run (same Python/venv as manage.py):\n  {install_hint}\n\n"
                    "Or use system Chrome (default) with a working Google Chrome install:\n"
                    "  python manage.py audit_tools --browser=chrome"
                ) from exc
            raise

        paths = write_reports(payload, run_id=run_id)
        self.stdout.write(self.style.SUCCESS(f"Report JSON: {paths['run_json']}"))
        self.stdout.write(self.style.SUCCESS(f"Dashboard HTML: {paths['run_html']}"))

        if options["fix_simple_issues"]:
            fix_path = write_fix_suggestions(payload, run_id)
            self.stdout.write(self.style.SUCCESS(f"Fix suggestions: {fix_path}"))

        s = payload["summary"]
        self.stdout.write("")
        for cat in payload["categories"]:
            self.stdout.write(self.style.NOTICE(f"Category: {cat['name']}"))
            self.stdout.write(f"  Total: {cat['total']}")
            self.stdout.write(f"  Working (healthy): {cat['healthy']}")
            self.stdout.write(f"  Warnings: {cat['warning']}")
            self.stdout.write(f"  Broken: {cat['broken']}")
            broken_slugs = [t["tool_slug"] for t in cat["tools"] if t["status"] == STATUS_BROKEN]
            if broken_slugs:
                self.stdout.write(self.style.ERROR("  Broken:\n"))
                for b in broken_slugs:
                    self.stdout.write(self.style.ERROR(f"    * {b}"))
            self.stdout.write("")

        self.stdout.write(
            f"Global summary: total={s['total']} healthy={s['healthy']} "
            f"warning={s['warning']} broken={s['broken']}"
        )
        if s["broken"]:
            self.stdout.write(self.style.WARNING("See report for suggested_fixes per tool."))
        if options["fail_on_broken"] and s["broken"]:
            raise CommandError(f"Audit found {s['broken']} broken tool(s).")
