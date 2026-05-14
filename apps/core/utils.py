import magic
import re

ALLOWED_MIMES: dict[str, list[str]] = {
    'pdf':   ['application/pdf'],
    'image': ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'image/tiff'],
    'zip':   ['application/zip', 'application/x-zip-compressed', 'application/x-zip'],
    'csv':   ['text/csv', 'text/plain', 'application/csv'],
    'text':  ['text/plain'],
}

MIME_TO_TYPE: dict[str, str] = {mime: type for type, mimes in ALLOWED_MIMES.items() for mime in mimes}

def _get_redis_client():
    """Get a Redis client using the broker URL from settings."""
    import redis
    from django.conf import settings
    return redis.from_url(settings.CELERY_BROKER_URL)

def validate_mime(file_obj, expected_type: str) -> tuple[bool, str]:
    """
    Inspect the first 2 KB of file_obj to detect its real MIME type.
    Returns (is_valid, detected_mime).
    Does NOT raise — always returns a tuple.
    """
    try:
        header = file_obj.read(2048)
        file_obj.seek(0)
        detected: str = magic.from_buffer(header, mime=True)
        allowed = ALLOWED_MIMES.get(expected_type, [])
        return detected in allowed, detected
    except Exception:
        file_obj.seek(0)
        return False, 'unknown'

def safe_filename(filename: str) -> str:
    """Generate safe filename for storage"""
    # Remove path traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    # Remove non-alphanumeric characters, except for dots, underscores, and hyphens
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Remove consecutive dots
    filename = re.sub(r'\. +', '.', filename)
    # Ensure filename doesn't start with a dot
    filename = filename.lstrip('.')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    return filename or 'file'

