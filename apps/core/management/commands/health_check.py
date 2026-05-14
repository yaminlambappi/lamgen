"""
management command: health_check

Lightweight liveness/readiness probe suitable for use in:
  - Docker HEALTHCHECK
  - Kubernetes liveness/readiness probes
  - Load balancer health endpoints
  - Monitoring scripts

Exit codes:
  0 — all checks passed (healthy)
  1 — one or more checks failed (unhealthy)

Usage:
    python manage.py health_check
    python manage.py health_check --check db
    python manage.py health_check --check redis
    python manage.py health_check --check all   (default)
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand


CHECKS = ("db", "redis", "all")


class Command(BaseCommand):
    help = "Liveness/readiness health check. Exits 0 if healthy, 1 if not."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            choices=CHECKS,
            default="all",
            help="Which subsystem to check (default: all).",
        )

    def handle(self, *args, **options):
        check = options["check"]
        results: dict[str, tuple[bool, str]] = {}

        if check in ("db", "all"):
            results["db"] = self._check_db()
        if check in ("redis", "all"):
            results["redis"] = self._check_redis()

        healthy = all(ok for ok, _ in results.values())

        for name, (ok, detail) in results.items():
            icon = "OK" if ok else "FAIL"
            self.stdout.write(f"{name}: {icon} — {detail}")

        if not healthy:
            sys.exit(1)

    def _check_db(self) -> tuple[bool, str]:
        try:
            from django.db import connection
            connection.ensure_connection()
            return True, f"connected ({connection.vendor})"
        except Exception as exc:
            return False, str(exc)

    def _check_redis(self) -> tuple[bool, str]:
        try:
            from django.conf import settings
            import redis
            url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(url, socket_connect_timeout=3)
            client.ping()
            return True, f"connected ({url})"
        except Exception as exc:
            return False, str(exc)
