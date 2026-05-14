"""
API Exceptions for Developer Tools

Custom exception classes for different types of errors that can occur
during tool processing.
"""

from .base import ToolAPIError


class ValidationError(ToolAPIError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        details = {}
        if field:
            details['field'] = field
        if value:
            details['value'] = value[:100]  # Limit value length in response
        
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class ProcessingError(ToolAPIError):
    """Raised when processing fails due to invalid data format"""
    
    def __init__(self, message: str, processing_type: str = None, details: dict = None):
        if not details:
            details = {}
        if processing_type:
            details['processing_type'] = processing_type
        
        super().__init__(message, "PROCESSING_ERROR", 422, details)


class RateLimitError(ToolAPIError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str = None, retry_after: int = None):
        if not message:
            message = "Rate limit exceeded. Please try again later."
        
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
        
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429, details)


class FileSizeError(ToolAPIError):
    """Raised when input exceeds size limits"""
    
    def __init__(self, message: str = None, max_size: int = None, actual_size: int = None):
        if not message:
            message = "Input size exceeds maximum allowed limit."
        
        details = {}
        if max_size:
            details['max_size'] = max_size
        if actual_size:
            details['actual_size'] = actual_size
        
        super().__init__(message, "FILE_SIZE_ERROR", 413, details)


class UnsupportedFormatError(ToolAPIError):
    """Raised when input format is not supported"""
    
    def __init__(self, message: str, format_type: str = None, supported_formats: list = None):
        details = {}
        if format_type:
            details['unsupported_format'] = format_type
        if supported_formats:
            details['supported_formats'] = supported_formats
        
        super().__init__(message, "UNSUPPORTED_FORMAT", 415, details)


class TimeoutError(ToolAPIError):
    """Raised when processing times out"""
    
    def __init__(self, message: str = None, timeout_seconds: int = None):
        if not message:
            message = "Processing timed out. Please try with smaller input."
        
        details = {}
        if timeout_seconds:
            details['timeout_seconds'] = timeout_seconds
        
        super().__init__(message, "TIMEOUT_ERROR", 408, details)


class SecurityError(ToolAPIError):
    """Raised when potentially malicious content is detected"""
    
    def __init__(self, message: str, security_issue: str = None):
        details = {}
        if security_issue:
            details['security_issue'] = security_issue
        
        super().__init__(message, "SECURITY_ERROR", 403, details)


class ConfigurationError(ToolAPIError):
    """Raised when there's a configuration error"""
    
    def __init__(self, message: str, config_key: str = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(message, "CONFIGURATION_ERROR", 500, details)
