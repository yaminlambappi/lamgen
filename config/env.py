"""
Centralized environment parser and validator for LamGen.

All settings files import from here. This is the single source of truth
for environment variable parsing, type coercion, and validation.

Usage:
    from config.env import env, require_env, get_environment

Never import django-environ directly in settings files.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import environ

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

_env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

# Load .env only when not already set by the OS/container environment.
# In production the container injects vars directly; .env is for local dev.
_dotenv_path = BASE_DIR / ".env"
if _dotenv_path.exists():
    environ.Env.read_env(_dotenv_path)

# ---------------------------------------------------------------------------
# Environment name resolution
# ---------------------------------------------------------------------------

VALID_ENVIRONMENTS = {"local", "test", "staging", "production"}


def get_environment() -> str:
    """
    Return the canonical environment name.

    Resolution order:
      1. DJANGO_ENV env var (explicit, preferred)
      2. Infer from DJANGO_SETTINGS_MODULE suffix
      3. Default to 'local'

    Raises ValueError for unknown environment names.
    """
    raw = os.environ.get("DJANGO_ENV", "").strip().lower()
    if raw:
        if raw not in VALID_ENVIRONMENTS:
            raise ValueError(
                f"DJANGO_ENV='{raw}' is not valid. "
                f"Must be one of: {', '.join(sorted(VALID_ENVIRONMENTS))}"
            )
        return raw

    # Infer from DJANGO_SETTINGS_MODULE
    dsm = os.environ.get("DJANGO_SETTINGS_MODULE", "")
    for env_name in VALID_ENVIRONMENTS:
        if dsm.endswith(f".{env_name}"):
            return env_name

    return "local"


def is_production() -> bool:
    return get_environment() == "production"


def is_test() -> bool:
    return get_environment() == "test"


def is_local() -> bool:
    return get_environment() == "local"


def is_staging() -> bool:
    return get_environment() == "staging"


# ---------------------------------------------------------------------------
# Typed helpers — thin wrappers around django-environ
# ---------------------------------------------------------------------------

def env_str(key: str, default: Any = environ.Env.NOTSET) -> str:
    if default is environ.Env.NOTSET:
        return _env.str(key)
    return _env.str(key, default=default)


def env_bool(key: str, default: bool = False) -> bool:
    return _env.bool(key, default=default)


def env_int(key: str, default: Any = environ.Env.NOTSET) -> int:
    if default is environ.Env.NOTSET:
        return _env.int(key)
    return _env.int(key, default=default)


def env_list(key: str, default: list | None = None) -> list:
    if default is None:
        return _env.list(key)
    return _env.list(key, default=default)


def env_db(key: str = "DATABASE_URL", default: Any = environ.Env.NOTSET) -> dict:
    if default is environ.Env.NOTSET:
        return _env.db(key)
    return _env.db(key, default=default)


# Expose the raw environ.Env instance for edge cases (e.g. env.db())
env = _env


# ---------------------------------------------------------------------------
# Secret / required-value helpers
# ---------------------------------------------------------------------------

def require_env(key: str, context: str = "") -> str:
    """
    Return env var value or abort with a clear error.

    Use for secrets and values that have no safe default.
    """
    value = os.environ.get(key, "").strip()
    if not value:
        hint = f" ({context})" if context else ""
        _fatal(f"Required environment variable '{key}' is not set{hint}.")
    return value


def require_secret(key: str) -> str:
    """Like require_env but also rejects obvious placeholder values."""
    value = require_env(key, context="secret")
    _INSECURE_PLACEHOLDERS = {
        "your-secret-key-here",
        "django-insecure-change-me-in-production",
        "changeme",
        "secret",
        "password",
        "placeholder",
    }
    if value.lower() in _INSECURE_PLACEHOLDERS or value.startswith("django-insecure-"):
        if is_production() or is_staging():
            _fatal(
                f"'{key}' contains an insecure placeholder value. "
                "Set a real secret before deploying."
            )
    return value


# ---------------------------------------------------------------------------
# Production safety guards
# ---------------------------------------------------------------------------

def assert_production_safety() -> None:
    """
    Run all production safety checks. Call once at settings load time
    when environment == 'production' or 'staging'.

    Aborts the process on any violation.
    """
    errors: list[str] = []

    # Secret key must be real
    sk = os.environ.get("SECRET_KEY", "")
    if not sk or sk.startswith("django-insecure-") or sk in (
        "your-secret-key-here", "changeme"
    ):
        errors.append("SECRET_KEY is missing or insecure.")

    # DEBUG must be off
    if env_bool("DEBUG", default=False):
        errors.append("DEBUG=True is not allowed in production/staging.")

    # DATABASE_URL must be set and not SQLite
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        errors.append("DATABASE_URL is not set.")
    elif db_url.startswith("sqlite"):
        errors.append("SQLite is not allowed in production/staging. Use PostgreSQL.")

    # REDIS_URL must be set
    if not os.environ.get("REDIS_URL", ""):
        errors.append("REDIS_URL is not set.")

    # ALLOWED_HOSTS must not be wildcard
    allowed = os.environ.get("ALLOWED_HOSTS", "")
    if "*" in allowed:
        errors.append("ALLOWED_HOSTS='*' is not allowed in production/staging.")

    if errors:
        _fatal(
            "Production safety checks failed:\n"
            + "\n".join(f"  • {e}" for e in errors)
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fatal(message: str) -> None:
    """Print a clear error and exit non-zero. Never raises — always exits."""
    print(f"\n[LamGen] FATAL CONFIGURATION ERROR\n{message}\n", file=sys.stderr)
    sys.exit(1)
