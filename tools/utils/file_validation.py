"""MIME type validation for file uploads using python-magic."""
import magic

ALLOWED_MIMES: dict[str, list[str]] = {
    'pdf':   ['application/pdf'],
    'image': ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'image/tiff'],
    'zip':   ['application/zip', 'application/x-zip-compressed', 'application/x-zip'],
    'csv':   ['text/csv', 'text/plain', 'application/csv'],
    'text':  ['text/plain'],
}


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
