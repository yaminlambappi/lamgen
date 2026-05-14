"""
Base settings for LamGen.

Never use this module directly. Always use a concrete environment module:
  config.settings.local
  config.settings.test
  config.settings.staging
  config.settings.production

Environment variables are loaded via config.env — never import django-environ
directly in settings files.
"""

from pathlib import Path

from config.env import (
    BASE_DIR,
    env,
    env_bool,
    env_int,
    env_list,
    env_str,
    get_environment,
)
from config.tool_categories import TOOL_CATEGORIES  # noqa: E402

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

ENVIRONMENT = get_environment()

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SECRET_KEY = env_str("SECRET_KEY", default="django-insecure-change-me-in-production")
DEBUG = env_bool("DEBUG", default=False)

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    default=[
        "lamgen.lamlab.me",
        "www.lamgen.lamlab.me",
        "127.0.0.1",
        "localhost",
        "194.233.67.21",
    ],
)

CSRF_TRUSTED_ORIGINS = [
    "https://lamgen.lamlab.me",
    "https://www.lamgen.lamlab.me",
]

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # Core LamGen Apps
    "apps.core.apps.CoreConfig",
    "apps.users.apps.UsersConfig",
    "apps.seo.apps.SEOConfig",
    "apps.analytics.apps.AnalyticsConfig",
    "apps.search.apps.SearchConfig",
    "apps.recommendations.apps.RecommendationsConfig",

    # Tool & Feature Apps
    "apps.ai_tools.apps.AiToolsConfig",
    "apps.calculators.apps.CalculatorsConfig",
    "apps.health.apps.HealthConfig",
    "apps.hospitals.apps.HospitalsConfig",
    "apps.electronics.apps.ElectronicsConfig",
    "apps.markets.apps.MarketsConfig",
    "apps.news.apps.NewsConfig",
    "apps.sports.apps.SportsConfig",
    "apps.finance.apps.FinanceConfig",
    "apps.directories.apps.DirectoriesConfig",

    # Existing apps to be migrated
    "apps.tools.apps.ToolsConfig",
    "apps.games.apps.GamesConfig",
    "apps.blog.apps.BlogConfig",
    "apps.generation.apps.GenerationConfig",
    "apps.thesis.apps.ThesisConfig",

    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.seo.middleware.CrawlErrorMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.tools.context_processors.tools_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "users.CustomUser"
LOGIN_URL = "/users/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("bn", "Bengali"),
    ("hi", "Hindi"),
    ("es", "Spanish"),
    ("ar", "Arabic"),
]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# Manifest-based hashing by default; overridden in local/test to plain storage.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = env_str("MEDIA_ROOT", default=str(BASE_DIR / "media"))

WHITENOISE_MAX_AGE = 31536000
WHITENOISE_KEEP_ONLY_HASHED_FILES = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------------------------
# Misc Django
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# ---------------------------------------------------------------------------
# Redis & Celery
# ---------------------------------------------------------------------------

REDIS_URL = env_str("REDIS_URL", default="redis://localhost:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"socket_connect_timeout": 2, "socket_timeout": 2},
    }
}

# ---------------------------------------------------------------------------
# Site / SEO
# ---------------------------------------------------------------------------

SITE_NAME = "LamGen Tools"
SITE_URL = env_str("SITE_URL", default="https://lamgen.lamlab.me")
TOOLS_PER_PAGE = 24
SEO_PAGES_PER_PAGE = 20

# ---------------------------------------------------------------------------
# Anthropic / Generation
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = env_str("ANTHROPIC_API_KEY", default="")
CLAUDE_MODEL = env_str("CLAUDE_MODEL", default="claude-sonnet-4-5")
CLAUDE_MAX_TOKENS = env_int("CLAUDE_MAX_TOKENS", default=4000)
CLAUDE_MAX_TOKENS_PER_JOB = env_int("CLAUDE_MAX_TOKENS_PER_JOB", default=40000)
CLAUDE_MOCK_MODE = env_bool("CLAUDE_MOCK_MODE", default=False)
GENERATION_MODE = env_str("GENERATION_MODE", default="standard")
ASSIGNMENT_TYPE_DEFAULT = env_str("ASSIGNMENT_TYPE_DEFAULT", default="essay")
CITATION_STYLE_DEFAULT = env_str("CITATION_STYLE_DEFAULT", default="APA")
WRITING_TONE_DEFAULT = env_str("WRITING_TONE_DEFAULT", default="critical_analytical")
SECTION_MODE = env_str("SECTION_MODE", default="auto")
SECTION_COUNT_DEFAULT = env_int("SECTION_COUNT_DEFAULT", default=5)
MAX_GENERATION_BUDGET_CENTS = env_int("MAX_GENERATION_BUDGET_CENTS", default=25)

# ---------------------------------------------------------------------------
# Tool categories
# ---------------------------------------------------------------------------

TOOL_CATEGORIES = TOOL_CATEGORIES  # noqa: F811

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs/django.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
