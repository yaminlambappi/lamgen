#!/bin/bash
# LamGen production entrypoint — fail fast on any error.
set -euo pipefail

# ---------------------------------------------------------------------------
# 1. Require explicit settings module — no silent fallback
# ---------------------------------------------------------------------------
if [ -z "${DJANGO_SETTINGS_MODULE:-}" ]; then
    echo "[LamGen] FATAL: DJANGO_SETTINGS_MODULE is not set." >&2
    echo "  Set it to 'config.settings.production' in your container environment." >&2
    exit 1
fi

echo "[LamGen] Starting with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"

# ---------------------------------------------------------------------------
# 2. Run startup diagnostics (validates env, DB, Redis, secrets)
# ---------------------------------------------------------------------------
echo "[LamGen] Running startup diagnostics..."
python manage.py startup_diagnostics --fail-fast

# ---------------------------------------------------------------------------
# 3. Apply database migrations
# ---------------------------------------------------------------------------
echo "[LamGen] Applying database migrations..."
python manage.py migrate --noinput

# ---------------------------------------------------------------------------
# 4. Collect static files (manifest-based)
# ---------------------------------------------------------------------------
echo "[LamGen] Collecting static files..."
python manage.py collectstatic --noinput --clear

# ---------------------------------------------------------------------------
# 5. Run deployment verification
# ---------------------------------------------------------------------------
echo "[LamGen] Running deployment verification..."
python manage.py deployment_verify

# ---------------------------------------------------------------------------
# 6. Start Gunicorn
# ---------------------------------------------------------------------------
echo "[LamGen] Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
