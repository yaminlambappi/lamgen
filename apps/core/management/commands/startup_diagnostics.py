"""
management command: startup_diagnostics

Validates the runtime environment before the application accepts traffic.
Checks: settings module, secrets, database connectivity, Redis connectivity,
static files manifest, and media directory.

Usage:
    python manage.py startup_diagnostics
    python manage.py startup_diagnostics --fail-fast   # exit 1 on first error
"""

from __future__ import annotations

import os
import sys
from typing import NamedTuple

from django.core.management.base import BaseCommand


class Check(NamedTuple):
    name: str
    passed: bool
    detail: str


class Command(BaseCommand):
    help = "Run pre-flight startup diagnostics and report environment health."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fail-fast",
            action="store_true",
            default=False,
            help="Exit with code 1 immediately on the first failed check.",
        )

    def handle(self, *args, **options):
        fail_fast = options["fail_fast"]
        checks: list[Check] = []

        checks.append(self._check_settings_module())
        checks.append(self._check_environment_name())
        checks.append(self._check_secret_key())
        checks.append(self._check_debug_flag())
        checks.append(self._check_database())
        checks.append(self._check_redis())
        checks.append(self._check_static_manifest())
        checks.append(self._check_media_dir())
        checks.append(self._check_allowed_hosts())

        passed = [c for c in checks if c.passed]
        failed = [c for c in checks if not c.passed]

        self.stdout.write("\n[LamGen] Startup Diagnostics\n" + "=" * 40)
        for check in checks:
            icon = self.style.SUCCESS("✓") if check.passed else self.style.ERROR("✗")
            self.stdout.write(f"  {icon}  {check.name}: {check.detail}")

        self.stdout.write("=" * 40)
        self.stdout.write(f"  {len(passed)} passed, {len(failed)} failed\n")

        if failed:
            self.stderr.write(
                self.style.ERROR(
                    f"[LamGen] {len(failed)} diagnostic check(s) failed. "
                    "Fix the issues above before proceeding."
                )
            )
            if fail_fast:
                sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS("[LamGen] All checks passed.\n"))

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_settings_module(self) -> Check:
        dsm = os.environ.get("DJANGO_SETTINGS_MODULE", "")
        if not dsm:
            return Check("DJANGO_SETTINGS_MODULE", False, "NOT SET")
        if dsm == "config.settings":
            return Check(
                "DJANGO_SETTINGS_MODULE",
                False,
                f"'{dsm}' is ambiguous — use a concrete environment module",
            )
        return Check("DJANGO_SETTINGS_MODULE", True, dsm)

    def _check_environment_name(self) -> Check:
        from config.env import get_environment, VALID_ENVIRONMENTS
        try:
            env_name = get_environment()
            return Check("DJANGO_ENV", True, env_name)
        except ValueError as exc:
            return Check("DJANGO_ENV", False, str(exc))

    def _check_secret_key(self) -> Check:
        from django.conf import settings
        sk = getattr(settings, "SECRET_KEY", "")
        if not sk:
            return Check("SECRET_KEY", False, "not set")
        if sk.startswith("django-insecure-") or sk in (
            "your-secret-key-here", "changeme"
        ):
            from config.env import is_production, is_staging
            if is_production() or is_staging():
                return Check("SECRET_KEY", False, "insecure placeholder in prod/staging")
            return Check("SECRET_KEY", True, "insecure placeholder (ok for local/test)")
        return Check("SECRET_KEY", True, f"set ({len(sk)} chars)")

    def _check_debug_flag(self) -> Check:
        from django.conf import settings
        from config.env import is_production, is_staging
        debug = getattr(settings, "DEBUG", False)
        if debug and (is_production() or is_staging()):
            return Check("DEBUG", False, "True in production/staging — must be False")
        return Check("DEBUG", True, str(debug))

    def _check_database(self) -> Check:
        try:
            from django.db import connection
            connection.ensure_connection()
            vendor = connection.vendor
            db_name = connection.settings_dict.get("NAME", "?")
            return Check("PostgreSQL", True, f"connected ({vendor}: {db_name})")
        except Exception as exc:
            return Check("PostgreSQL", False, f"connection failed: {exc}")

    def _check_redis(self) -> Check:
        try:
            from django.conf import settings
            import redis
            url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(url, socket_connect_timeout=3)
            client.ping()
            return Check("Redis", True, f"connected ({url})")
        except Exception as exc:
            return Check("Redis", False, f"connection failed: {exc}")

    def _check_static_manifest(self) -> Check:
        from django.conf import settings
        storage_cls = getattr(settings, "STATICFILES_STORAGE", "")
        is_manifest = "Manifest" in storage_cls or "Compressed" in storage_cls
        static_root = getattr(settings, "STATIC_ROOT", None)

        if not is_manifest:
            return Check("Static manifest", True, f"plain storage ({storage_cls})")

        if not static_root:
            return Check("Static manifest", False, "STATIC_ROOT not set")

        manifest_path = static_root / "staticfiles.json" if hasattr(static_root, "__truediv__") else None
        if manifest_path is None:
            from pathlib import Path
            manifest_path = Path(str(static_root)) / "staticfiles.json"

        if manifest_path.exists():
            return Check("Static manifest", True, str(manifest_path))
        return Check(
            "Static manifest",
            False,
            f"staticfiles.json not found at {manifest_path} — run collectstatic",
        )

    def _check_media_dir(self) -> Check:
        from django.conf import settings
        from pathlib import Path
        media_root = Path(getattr(settings, "MEDIA_ROOT", "media"))
        if media_root.exists():
            return Check("MEDIA_ROOT", True, str(media_root))
        try:
            media_root.mkdir(parents=True, exist_ok=True)
            return Check("MEDIA_ROOT", True, f"created {media_root}")
        except Exception as exc:
            return Check("MEDIA_ROOT", False, f"cannot create: {exc}")

    def _check_allowed_hosts(self) -> Check:
        from django.conf import settings
        from config.env import is_production, is_staging
        hosts = getattr(settings, "ALLOWED_HOSTS", [])
        if "*" in hosts and (is_production() or is_staging()):
            return Check("ALLOWED_HOSTS", False, "wildcard '*' not allowed in prod/staging")
        return Check("ALLOWED_HOSTS", True, ", ".join(hosts) or "(empty)")
