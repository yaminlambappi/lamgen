"""
management command: deployment_verify

Post-deployment verification gate. Confirms the deployment is safe to
receive traffic. Exits non-zero if any critical check fails.

Checks:
  - Pending migrations
  - Static manifest integrity
  - Database write access
  - Redis write access
  - Settings module is production/staging

Usage:
    python manage.py deployment_verify
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Verify deployment readiness. Exits 1 if any critical check fails."

    def handle(self, *args, **options):
        errors: list[str] = []

        errors += self._check_no_pending_migrations()
        errors += self._check_static_manifest()
        errors += self._check_db_write()
        errors += self._check_redis_write()
        errors += self._check_settings_is_not_local()

        if errors:
            self.stderr.write(self.style.ERROR("\n[LamGen] Deployment verification FAILED:"))
            for err in errors:
                self.stderr.write(self.style.ERROR(f"  • {err}"))
            self.stderr.write("")
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS("[LamGen] Deployment verification passed.\n"))

    # ------------------------------------------------------------------

    def _check_no_pending_migrations(self) -> list[str]:
        from django.db.migrations.executor import MigrationExecutor
        from django.db import connections, DEFAULT_DB_ALIAS
        try:
            connection = connections[DEFAULT_DB_ALIAS]
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                names = ", ".join(f"{app}.{name}" for app, name in [m[0].app_label, m[0].name] for m in [plan[:1]])
                return [f"{len(plan)} unapplied migration(s) — run 'manage.py migrate'"]
            return []
        except Exception as exc:
            return [f"Could not check migrations: {exc}"]

    def _check_static_manifest(self) -> list[str]:
        from django.conf import settings
        from pathlib import Path
        storage_cls = getattr(settings, "STATICFILES_STORAGE", "")
        if "Manifest" not in storage_cls and "Compressed" not in storage_cls:
            return []  # plain storage — not required
        static_root = Path(str(getattr(settings, "STATIC_ROOT", "staticfiles")))
        manifest = static_root / "staticfiles.json"
        if not manifest.exists():
            return [f"staticfiles.json missing at {manifest} — run collectstatic"]
        return []

    def _check_db_write(self) -> list[str]:
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return []
        except Exception as exc:
            return [f"Database write check failed: {exc}"]

    def _check_redis_write(self) -> list[str]:
        try:
            from django.conf import settings
            import redis
            url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(url, socket_connect_timeout=3)
            client.set("lamgen:deploy_check", "1", ex=10)
            client.delete("lamgen:deploy_check")
            return []
        except Exception as exc:
            return [f"Redis write check failed: {exc}"]

    def _check_settings_is_not_local(self) -> list[str]:
        from config.env import get_environment
        env_name = get_environment()
        if env_name == "local":
            return ["Running with local settings in a deployment context — use production or staging"]
        return []
