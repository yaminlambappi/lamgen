"""
Validation Framework - Unified Input Validation for LamGen Tools

Provides comprehensive validation system with schema-based validation,
custom validators, and standardized error reporting.
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum


class ValidationType(Enum):
    """Supported validation types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    EMAIL = "email"
    URL = "url"
    JSON = "json"
    FILE = "file"
    COLOR = "color"
    REGEX = "regex"


@dataclass
class ValidationRule:
    """Single validation rule definition"""
    type: ValidationType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable[[Any], List[str]]] = None
    error_message: Optional[str] = None


class ValidationError:
    """Standardized validation error"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'field': self.field,
            'message': self.message,
            'value': self.value
        }


class ValidationFramework:
    """Main validation engine"""
    
    def __init__(self):
        self.validators = {
            ValidationType.STRING: self._validate_string,
            ValidationType.INTEGER: self._validate_integer,
            ValidationType.FLOAT: self._validate_float,
            ValidationType.BOOLEAN: self._validate_boolean,
            ValidationType.ARRAY: self._validate_array,
            ValidationType.OBJECT: self._validate_object,
            ValidationType.EMAIL: self._validate_email,
            ValidationType.URL: self._validate_url,
            ValidationType.JSON: self._validate_json,
            ValidationType.FILE: self._validate_file,
            ValidationType.COLOR: self._validate_color,
            ValidationType.REGEX: self._validate_regex,
        }
    
    def validate(self, data: Dict[str, Any], schema: Dict[str, ValidationRule]) -> List[str]:
        """
        Validate input data against schema.
        Returns list of error messages.
        """
        errors = []
        
        for field_name, rule in schema.items():
            field_value = data.get(field_name)
            
            # Check required fields
            if rule.required and field_value is None:
                errors.append(f"{field_name} is required")
                continue
            
            # Skip validation if field is not provided and not required
            if field_value is None:
                continue
            
            # Run type-specific validation
            validator = self.validators.get(rule.type)
            if validator:
                field_errors = validator(field_value, rule, field_name)
                errors.extend(field_errors)
            
            # Run custom validator if provided
            if rule.custom_validator:
                custom_errors = rule.custom_validator(field_value)
                for error in custom_errors:
                    errors.append(f"{field_name}: {error}")
        
        return errors
    
    def _validate_string(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate string fields"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
            return errors
        
        # Length validation
        if rule.min_length is not None and len(value) < rule.min_length:
            errors.append(f"{field_name} must be at least {rule.min_length} characters long")
        
        if rule.max_length is not None and len(value) > rule.max_length:
            errors.append(f"{field_name} must be no more than {rule.max_length} characters long")
        
        # Pattern validation
        if rule.pattern:
            if not re.match(rule.pattern, value):
                error_msg = rule.error_message or f"{field_name} format is invalid"
                errors.append(error_msg)
        
        # Allowed values validation
        if rule.allowed_values and value not in rule.allowed_values:
            errors.append(f"{field_name} must be one of: {', '.join(map(str, rule.allowed_values))}")
        
        return errors
    
    def _validate_integer(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate integer fields"""
        errors = []
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            errors.append(f"{field_name} must be a valid integer")
            return errors
        
        # Range validation
        if rule.min_value is not None and int_value < rule.min_value:
            errors.append(f"{field_name} must be at least {rule.min_value}")
        
        if rule.max_value is not None and int_value > rule.max_value:
            errors.append(f"{field_name} must be no more than {rule.max_value}")
        
        # Allowed values validation
        if rule.allowed_values and int_value not in rule.allowed_values:
            errors.append(f"{field_name} must be one of: {', '.join(map(str, rule.allowed_values))}")
        
        return errors
    
    def _validate_float(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate float fields"""
        errors = []
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            errors.append(f"{field_name} must be a valid number")
            return errors
        
        # Range validation
        if rule.min_value is not None and float_value < rule.min_value:
            errors.append(f"{field_name} must be at least {rule.min_value}")
        
        if rule.max_value is not None and float_value > rule.max_value:
            errors.append(f"{field_name} must be no more than {rule.max_value}")
        
        return errors
    
    def _validate_boolean(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate boolean fields"""
        if not isinstance(value, bool):
            return [f"{field_name} must be true or false"]
        return []
    
    def _validate_array(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate array fields"""
        errors = []
        
        if not isinstance(value, list):
            errors.append(f"{field_name} must be an array")
            return errors
        
        # Length validation
        if rule.min_length is not None and len(value) < rule.min_length:
            errors.append(f"{field_name} must contain at least {rule.min_length} items")
        
        if rule.max_length is not None and len(value) > rule.max_length:
            errors.append(f"{field_name} must contain no more than {rule.max_length} items")
        
        return errors
    
    def _validate_object(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate object fields"""
        if not isinstance(value, dict):
            return [f"{field_name} must be an object"]
        return []
    
    def _validate_email(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate email fields"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
            return errors
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            errors.append(f"{field_name} must be a valid email address")
        
        return errors
    
    def _validate_url(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate URL fields"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
            return errors
        
        url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        if not re.match(url_pattern, value):
            errors.append(f"{field_name} must be a valid URL")
        
        return errors
    
    def _validate_json(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate JSON fields"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
            return errors
        
        try:
            json.loads(value)
        except json.JSONDecodeError:
            errors.append(f"{field_name} must be valid JSON")
        
        return errors
    
    def _validate_file(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate file fields"""
        errors = []
        
        # Check if it's a file object (Django UploadedFile)
        if not hasattr(value, 'size') or not hasattr(value, 'content_type'):
            errors.append(f"{field_name} must be a file")
            return errors
        
        # File size validation (convert MB to bytes)
        if rule.max_length:
            max_size_bytes = rule.max_length * 1024 * 1024
            if value.size > max_size_bytes:
                errors.append(f"{field_name} must be smaller than {rule.max_length}MB")
        
        # File type validation
        if rule.allowed_values and value.content_type not in rule.allowed_values:
            errors.append(f"{field_name} must be one of: {', '.join(rule.allowed_values)}")
        
        return errors
    
    def _validate_color(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate color fields (hex, rgb, named colors)"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
            return errors
        
        # Hex color pattern
        hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        # RGB color pattern
        rgb_pattern = r'^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$'
        # RGBA color pattern
        rgba_pattern = r'^rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)$'
        
        if not (re.match(hex_pattern, value) or 
                re.match(rgb_pattern, value) or 
                re.match(rgba_pattern, value)):
            errors.append(f"{field_name} must be a valid color (hex, rgb, or rgba)")
        
        return errors
    
    def _validate_regex(self, value: Any, rule: ValidationRule, field_name: str) -> List[str]:
        """Validate regex fields"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
            return errors
        
        try:
            re.compile(value)
        except re.error:
            errors.append(f"{field_name} must be a valid regular expression")
        
        return errors


# Common validation schemas for reuse
COMMON_SCHEMAS = {
    'email_field': ValidationRule(
        type=ValidationType.EMAIL,
        required=True,
        error_message="Please enter a valid email address"
    ),
    
    'url_field': ValidationRule(
        type=ValidationType.URL,
        required=True,
        error_message="Please enter a valid URL"
    ),
    
    'json_field': ValidationRule(
        type=ValidationType.JSON,
        required=True,
        error_message="Please enter valid JSON"
    ),
    
    'text_field': ValidationRule(
        type=ValidationType.STRING,
        required=True,
        min_length=1,
        max_length=1000000,
        error_message="Please enter text content"
    ),
    
    'color_field': ValidationRule(
        type=ValidationType.COLOR,
        required=True,
        error_message="Please enter a valid color"
    ),
    
    'file_upload': ValidationRule(
        type=ValidationType.FILE,
        required=True,
        max_length=10,  # 10MB
        allowed_values=['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'text/plain'],
        error_message="Please upload a valid file (JPG, PNG, GIF, PDF, or TXT, max 10MB)"
    ),
    
    'number_field': ValidationRule(
        type=ValidationType.INTEGER,
        required=True,
        min_value=0,
        max_value=1000000,
        error_message="Please enter a valid number"
    ),
    
    'positive_integer': ValidationRule(
        type=ValidationType.INTEGER,
        required=True,
        min_value=1,
        max_value=1000000,
        error_message="Please enter a positive integer"
    ),
    
    'percentage_field': ValidationRule(
        type=ValidationType.INTEGER,
        required=True,
        min_value=0,
        max_value=100,
        error_message="Please enter a percentage between 0 and 100"
    ),
}
