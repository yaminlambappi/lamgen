"""
JSON Formatter API - Backend Implementation

Provides server-side JSON formatting, validation, and processing with:
- Large file handling
- Advanced formatting options
- Error detection and reporting
- Performance optimization
"""

import json
import re
from typing import Dict, Any, List, Tuple
from .base import BaseToolAPI
from .exceptions import ValidationError, ProcessingError


class JSONFormatterAPI(BaseToolAPI):
    """Backend API for JSON formatting and validation"""
    
    def __init__(self):
        super().__init__("json-formatter")
        self.max_input_size = 50 * 1024 * 1024  # 50MB for JSON files
    
    def process_request(self, request, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process JSON formatting request"""
        json_data = data['data']
        options = data.get('options', {})
        
        # Extract options with defaults
        indent_size = options.get('indent_size', 2)
        sort_keys = options.get('sort_keys', False)
        compact = options.get('compact', False)
        validate_only = options.get('validate_only', False)
        
        try:
            # Parse JSON
            parsed_json = self._parse_json(json_data)
            
            # If validation only, return validation result
            if validate_only:
                return {
                    'valid': True,
                    'formatted': False,
                    'stats': self._get_json_stats(parsed_json)
                }
            
            # Format JSON
            formatted_json = self._format_json(parsed_json, indent_size, sort_keys, compact)
            
            # Get statistics
            stats = self._get_json_stats(parsed_json)
            stats['output_size'] = len(formatted_json.encode('utf-8'))
            stats['output_lines'] = len(formatted_json.split('\n'))
            
            return {
                'valid': True,
                'formatted': True,
                'result': formatted_json,
                'stats': stats
            }
            
        except json.JSONDecodeError as e:
            # Provide detailed error information
            error_info = self._analyze_json_error(json_data, e)
            raise ProcessingError(
                f"Invalid JSON: {e.msg}",
                processing_type="json_validation",
                details=error_info
            )
    
    def _parse_json(self, json_data: str) -> Any:
        """Parse JSON with error handling"""
        try:
            return json.loads(json_data)
        except json.JSONDecodeError as e:
            raise e
    
    def _format_json(self, parsed_json: Any, indent_size: int, sort_keys: bool, compact: bool) -> str:
        """Format JSON according to options"""
        if compact:
            return json.dumps(parsed_json, separators=(',', ':'), ensure_ascii=False)
        else:
            return json.dumps(
                parsed_json,
                indent=indent_size,
                sort_keys=sort_keys,
                ensure_ascii=False
            )
    
    def _get_json_stats(self, parsed_json: Any) -> Dict[str, Any]:
        """Get JSON statistics"""
        stats = {
            'total_keys': self._count_keys(parsed_json),
            'max_depth': self._get_depth(parsed_json),
            'input_size': len(json.dumps(parsed_json).encode('utf-8')),
            'data_types': self._get_data_types(parsed_json),
            'arrays_count': self._count_arrays(parsed_json),
            'objects_count': self._count_objects(parsed_json)
        }
        return stats
    
    def _count_keys(self, obj: Any, depth: int = 0) -> int:
        """Recursively count all keys in JSON"""
        if depth > 1000:  # Prevent infinite recursion
            return 0
        
        if isinstance(obj, dict):
            count = len(obj)
            for value in obj.values():
                count += self._count_keys(value, depth + 1)
            return count
        elif isinstance(obj, list):
            count = 0
            for item in obj:
                count += self._count_keys(item, depth + 1)
            return count
        else:
            return 0
    
    def _get_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Get maximum depth of JSON structure"""
        if current_depth > 1000:  # Prevent infinite recursion
            return current_depth
        
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._get_depth(value, current_depth + 1) for value in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._get_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _get_data_types(self, obj: Any) -> Dict[str, int]:
        """Count different data types in JSON"""
        types = {
            'string': 0,
            'number': 0,
            'boolean': 0,
            'null': 0,
            'object': 0,
            'array': 0
        }
        
        def count_types(item):
            if isinstance(item, dict):
                types['object'] += 1
                for value in item.values():
                    count_types(value)
            elif isinstance(item, list):
                types['array'] += 1
                for element in item:
                    count_types(element)
            elif isinstance(item, str):
                types['string'] += 1
            elif isinstance(item, (int, float)):
                types['number'] += 1
            elif isinstance(item, bool):
                types['boolean'] += 1
            elif item is None:
                types['null'] += 1
        
        count_types(obj)
        return types
    
    def _count_arrays(self, obj: Any) -> int:
        """Count number of arrays in JSON"""
        if isinstance(obj, dict):
            count = 0
            for value in obj.values():
                count += self._count_arrays(value)
            return count
        elif isinstance(obj, list):
            count = 1
            for item in obj:
                count += self._count_arrays(item)
            return count
        else:
            return 0
    
    def _count_objects(self, obj: Any) -> int:
        """Count number of objects in JSON"""
        if isinstance(obj, dict):
            count = 1
            for value in obj.values():
                count += self._count_objects(value)
            return count
        elif isinstance(obj, list):
            count = 0
            for item in obj:
                count += self._count_objects(item)
            return count
        else:
            return 0
    
    def _analyze_json_error(self, json_data: str, error: json.JSONDecodeError) -> Dict[str, Any]:
        """Analyze JSON error and provide helpful information"""
        line_num = error.lineno
        col_num = error.colno
        
        # Get context around error
        lines = json_data.split('\n')
        error_line = lines[line_num - 1] if line_num <= len(lines) else ""
        
        # Find common issues
        suggestions = []
        
        # Check for common syntax errors
        if "Expecting ',' delimiter" in error.msg:
            suggestions.append("Check for missing commas between elements")
        elif "Expecting ':' delimiter" in error.msg:
            suggestions.append("Check for missing colon after key")
        elif "Unterminated string" in error.msg:
            suggestions.append("Check for unclosed quotes")
        elif "Expecting property name" in error.msg:
            suggestions.append("Check for extra commas or missing brackets")
        
        # Check for trailing comma
        if line_num <= len(lines):
            line = lines[line_num - 1].strip()
            if line.endswith(','):
                suggestions.append("Remove trailing comma")
        
        # Check for quotes vs apostrophes
        if "'" in error_line:
            suggestions.append("Use double quotes for strings, not single quotes")
        
        return {
            'line': line_num,
            'column': col_num,
            'error_line': error_line.strip(),
            'error_message': error.msg,
            'suggestions': suggestions,
            'context': self._get_error_context(lines, line_num - 1)
        }
    
    def _get_error_context(self, lines: List[str], error_line_idx: int) -> Dict[str, Any]:
        """Get context around error line"""
        context_lines = 3  # Show 3 lines before and after
        
        start_idx = max(0, error_line_idx - context_lines)
        end_idx = min(len(lines), error_line_idx + context_lines + 1)
        
        context = []
        for i in range(start_idx, end_idx):
            line_info = {
                'line_number': i + 1,
                'content': lines[i],
                'is_error_line': i == error_line_idx
            }
            context.append(line_info)
        
        return {
            'lines': context,
            'error_line_index': error_line_idx - start_idx
        }
