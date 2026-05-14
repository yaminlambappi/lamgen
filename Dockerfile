FROM python:3.11-slim

# Install system dependencies for WeasyPrint, libmagic, and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    libmagic1 \
    libmagic-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin -c "Docker image user" appuser
RUN mkdir -p /media/uploads /media/outputs && chown -R appuser:appuser /app /media

USER appuser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Must be overridden at runtime — this is a safe default for the build stage only.
# The actual value is injected via docker-compose env_file or container environment.
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ENV DJANGO_ENV=production

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
