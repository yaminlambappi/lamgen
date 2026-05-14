"""
management command: env_summary

Prints a human-readable summary of the active runtime configuration.
Secrets are redacted. Safe to run in any environment.

Usage:
    python manage.py env_summary
"""

from __future__ import annotations

from django.core.management.base import BaseCommand


def _redact(value: str, show_chars: int = 4) -> str:
    """Show only the first N chars of a secret value."""
    if not value:
        return "(not set)"
    if len(value) <= show_chars:
        return "***"
    return value[:show_chars] + "***"


class Command(BaseCommand):
    help = "Print a summary of the active runtime configuration (secrets redacted)."

    def handle(self, *args, **options):
        import os
        from django.conf import settings
        from config.env import get_environment

        env_name = get_environment()
        dsm = os.environ.get("DJANGO_SETTINGS_MODULE", "(not set)")

        lines = [
            "",
            "╔══════════════════════════════════════════════════╗",
            "║           LamGen — Environment Summary           ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  Environment       : {env_name}",
            f"  Settings module   : {dsm}",
            f"  DEBUG             : {getattr(settings, 'DEBUG', '?')}",
            "",
            "  ── Database ──────────────────────────────────────",
        ]

        db_cfg = settings.DATABASES.get("default", {})
        lines += [
            f"  ENGINE            : {db_cfg.get('ENGINE', '?')}",
            f"  NAME              : {db_cfg.get('NAME', '?')}",
            f"  HOST              : {db_cfg.get('HOST', 'localhost')}",
            f"  PORT              : {db_cfg.get('PORT', '5432')}",
            "",
            "  ── Redis / Celery ────────────────────────────────",
            f"  REDIS_URL         : {getattr(settings, 'REDIS_URL', '?')}",
            f"  CELERY_BROKER_URL : {getattr(settings, 'CELERY_BROKER_URL', '?')}",
            "",
            "  ── Static / Media ────────────────────────────────",
            f"  STATIC_ROOT       : {getattr(settings, 'STATIC_ROOT', '?')}",
            f"  STATICFILES_STORAGE: {getattr(settings, 'STATICFILES_STORAGE', '?')}",
            f"  MEDIA_ROOT        : {getattr(settings, 'MEDIA_ROOT', '?')}",
            "",
            "  ── Security ──────────────────────────────────────",
            f"  SECRET_KEY        : {_redact(getattr(settings, 'SECRET_KEY', ''))}",
            f"  ALLOWED_HOSTS     : {', '.join(getattr(settings, 'ALLOWED_HOSTS', []))}",
            f"  SESSION_COOKIE_SECURE: {getattr(settings, 'SESSION_COOKIE_SECURE', False)}",
            f"  CSRF_COOKIE_SECURE: {getattr(settings, 'CSRF_COOKIE_SECURE', False)}",
            "",
            "  ── AI / Generation ───────────────────────────────",
            f"  ANTHROPIC_API_KEY : {_redact(getattr(settings, 'ANTHROPIC_API_KEY', ''))}",
            f"  CLAUDE_MODEL      : {getattr(settings, 'CLAUDE_MODEL', '?')}",
            f"  CLAUDE_MOCK_MODE  : {getattr(settings, 'CLAUDE_MOCK_MODE', '?')}",
            f"  GENERATION_MODE   : {getattr(settings, 'GENERATION_MODE', '?')}",
            "",
        ]

        self.stdout.write("\n".join(lines))
