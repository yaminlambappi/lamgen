import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read environment variables
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read .env file if it exists
environ.Env.read_env(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    "lamgen.lamlab.me",
    "www.lamgen.lamlab.me",
    "127.0.0.1",
    "localhost",
]

CSRF_TRUSTED_ORIGINS = [
    "https://lamgen.lamlab.me",
    "https://www.lamgen.lamlab.me",
]
# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    # Existing apps
    'accounts',
    'thesis',
    'generation',
    # New ecosystem apps
    'tools',
    'seo',
    'games',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tools.context_processors.tools_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3'),
}

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Auth redirects
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = env.str('MEDIA_ROOT', default=str(BASE_DIR / 'media'))

# Edge Caching & Whitenoise Optimization (Immutable static files)
WHITENOISE_MAX_AGE = 31536000
WHITENOISE_KEEP_ONLY_HASHED_FILES = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Messages storage
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Celery configuration
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Cache (Redis with fallback to LocMem for local dev without Redis)
try:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {'socket_connect_timeout': 2, 'socket_timeout': 2},
        }
    }
except Exception:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# SEO settings
SITE_NAME = 'LamGen Tools'
SITE_URL = env('SITE_URL', default='https://lamgen.tools')

# Tools ecosystem settings
TOOLS_PER_PAGE = 24
SEO_PAGES_PER_PAGE = 20

# Anthropic API key
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')

# ---------------------------------------------------------------------------
# Generation settings
# ---------------------------------------------------------------------------

# Model variant — override via CLAUDE_MODEL env var
CLAUDE_MODEL = env('CLAUDE_MODEL', default='claude-sonnet-4-5')

# Hard ceiling on output tokens per single API call
CLAUDE_MAX_TOKENS = env.int('CLAUDE_MAX_TOKENS', default=4000)

# Hard ceiling on total tokens (input + output) consumed by one GenerationJob.
# Prevents runaway costs. At ~$0.003/1k input + $0.015/1k output (Sonnet),
# 40 000 tokens ≈ $0.25 worst-case per job.
CLAUDE_MAX_TOKENS_PER_JOB = env.int('CLAUDE_MAX_TOKENS_PER_JOB', default=40000)

# When True, ClaudeService returns deterministic mock responses instead of
# calling the real API. Set to True in .env during development.
CLAUDE_MOCK_MODE = env.bool('CLAUDE_MOCK_MODE', default=False)

# Generation mode controls prompt verbosity and token allocation strategy.
# Options: 'economy' | 'standard' | 'quality'
#   economy  — minimal prompts, tightest token caps, cheapest per assignment
#   standard — balanced (default for production)
#   quality  — fuller context injection, higher token caps
GENERATION_MODE = env('GENERATION_MODE', default='standard')

# Assignment type hint — used to select deterministic fallback outlines.
# Options: 'essay' | 'report' | 'case_study' | 'literature_review' | 'other'
ASSIGNMENT_TYPE_DEFAULT = env('ASSIGNMENT_TYPE_DEFAULT', default='essay')

# Citation style default when not detected from the document.
CITATION_STYLE_DEFAULT = env('CITATION_STYLE_DEFAULT', default='APA')

# Writing tone default.
# Options: 'critical_analytical' | 'descriptive_explanatory' | 'reflective' | 'professional_report'
WRITING_TONE_DEFAULT = env('WRITING_TONE_DEFAULT', default='critical_analytical')

# Section mode: 'auto' detects section count from the brief; 'fixed' uses
# SECTION_COUNT_DEFAULT regardless of what the brief says.
SECTION_MODE = env('SECTION_MODE', default='auto')
SECTION_COUNT_DEFAULT = env.int('SECTION_COUNT_DEFAULT', default=5)

# Maximum budget in USD cents for a single generation job (soft warning only).
# Used for cost estimation display — does not block generation.
MAX_GENERATION_BUDGET_CENTS = env.int('MAX_GENERATION_BUDGET_CENTS', default=25)

# ---------------------------------------------------------------------------
# Tool Categories — imported from config/tool_categories.py
# Used by seed_tools management command and the frontend Design System.
# ---------------------------------------------------------------------------
from config.tool_categories import TOOL_CATEGORIES  # noqa: E402
