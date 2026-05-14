"""
JSON Tools - Complete Implementation of JSON Processing Tools

Provides production-ready JSON formatting, validation, and conversion tools
with comprehensive error handling, validation, and performance monitoring.
"""

import json
import re
from typing import Dict, Any, List, Tuple, Optional

from apps.tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus, register_tool
from apps.tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS
from apps.tools.utils.processing import FormatProcessor, DataProcessor
from apps.tools.utils.analytics import analytics_tracker


@register_tool(ToolConfig(
    name="JSON Formatter",
    slug="json-formatter",
    category="developer",
    description="Format and validate JSON data with syntax highlighting and error detection",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=60,
    cache_ttl_seconds=300,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online JSON Formatter & Validator - LamGen',
        'description': 'Format, validate, and beautify JSON data with syntax highlighting. Detect errors instantly.',
        'keywords': 'json formatter, json validator, json beautifier, json parser, online json tool'
    }
))
class JSONFormatterTool(BaseTool):
    """Production-ready JSON formatter with validation and syntax highlighting"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'json_input': COMMON_SCHEMAS['json_field'],
            'indent_size': ValidationRule(
                type=ValidationType.INTEGER,
                required=False,
                min_value=1,
                max_value=8,
                default=2
            ),
            'sort_keys': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Format JSON with proper indentation and validation"""
        try:
            json_input = input_data.get('json_input', '')
            indent_size = input_data.get('indent_size', 2)
            sort_keys = input_data.get('sort_keys', True)
            
            if not json_input.strip():
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="JSON input is required"
                )
            
            # Format JSON
            success, formatted_json, errors = FormatProcessor.format_json(json_input, indent_size)
            
            if not success:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=errors[0] if errors else "JSON formatting failed"
                )
            
            # Additional validation
            try:
                parsed_data = json.loads(json_input)
                data_info = self._analyze_json_structure(parsed_data)
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'formatted_json': formatted_json,
                        'original_json': json_input,
                        'is_valid': True,
                        'structure_info': data_info,
                        'indent_size': indent_size,
                        'sort_keys': sort_keys
                    },
                    metadata={
                        'input_length': len(json_input),
                        'output_length': len(formatted_json),
                        'compression_ratio': len(formatted_json) / len(json_input) if json_input else 0
                    }
                )
                
            except json.JSONDecodeError as e:
                # Try to provide helpful error context
                error_info = self._analyze_json_error(str(e), json_input)
                
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Invalid JSON: {str(e)}",
                    data={
                        'formatted_json': '',
                        'original_json': json_input,
                        'is_valid': False,
                        'error_info': error_info,
                        'suggestions': self._get_json_suggestions(error_info)
                    }
                )
                
        except Exception as e:
            return self.handle_error(e, "format_json")
    
    def _analyze_json_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze JSON structure and provide insights"""
        info = {
            'type': type(data).__name__,
            'depth': self._calculate_depth(data),
            'total_keys': 0,
            'total_values': 0,
            'arrays_count': 0,
            'objects_count': 0,
            'size_bytes': len(json.dumps(data).encode('utf-8'))
        }
        
        if isinstance(data, dict):
            info['total_keys'] = len(data)
            info['objects_count'] = 1
            self._count_nested_items(data, info)
        elif isinstance(data, list):
            info['total_values'] = len(data)
            info['arrays_count'] = 1
            self._count_nested_items(data, info)
        else:
            info['total_values'] = 1
        
        return info
    
    def _calculate_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum depth of JSON structure"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._calculate_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _count_nested_items(self, obj: Any, info: Dict[str, int]) -> None:
        """Recursively count items in JSON structure"""
        if isinstance(obj, dict):
            info['objects_count'] += 1
            info['total_keys'] += len(obj)
            for value in obj.values():
                self._count_nested_items(value, info)
        elif isinstance(obj, list):
            info['arrays_count'] += 1
            info['total_values'] += len(obj)
            for item in obj:
                self._count_nested_items(item, info)
        else:
            info['total_values'] += 1
    
    def _analyze_json_error(self, error_msg: str, json_input: str) -> Dict[str, Any]:
        """Analyze JSON error and provide helpful context"""
        error_info = {
            'error_type': 'syntax_error',
            'line_number': None,
            'column_number': None,
            'context': '',
            'common_cause': ''
        }
        
        # Extract line and column from error message
        line_match = re.search(r'line (\d+)', error_msg.lower())
        column_match = re.search(r'column (\d+)', error_msg.lower())
        
        if line_match:
            error_info['line_number'] = int(line_match.group(1))
        if column_match:
            error_info['column_number'] = int(column_match.group(1))
        
        # Get context around error
        if error_info['line_number']:
            lines = json_input.split('\n')
            error_line = error_info['line_number'] - 1
            if 0 <= error_line < len(lines):
                error_info['context'] = lines[error_line]
        
        # Determine common cause
        if 'expecting' in error_msg.lower():
            error_info['common_cause'] = 'missing_comma_or_bracket'
        elif 'expecting property name' in error_msg.lower():
            error_info['common_cause'] = 'missing_quotes'
        elif 'expecting value' in error_msg.lower():
            error_info['common_cause'] = 'incomplete_structure'
        
        return error_info
    
    def _get_json_suggestions(self, error_info: Dict[str, Any]) -> List[str]:
        """Get suggestions based on error analysis"""
        suggestions = []
        
        if error_info.get('common_cause') == 'missing_comma_or_bracket':
            suggestions.extend([
                "Check for missing commas between object properties",
                "Ensure all brackets and braces are properly closed",
                "Verify string quotes are balanced"
            ])
        elif error_info.get('common_cause') == 'missing_quotes':
            suggestions.extend([
                "Make sure all object property names are in double quotes",
                "Check for unescaped quotes within string values"
            ])
        elif error_info.get('common_cause') == 'incomplete_structure':
            suggestions.extend([
                "Complete the JSON structure by adding missing values",
                "Remove trailing commas from last properties"
            ])
        
        return suggestions


@register_tool(ToolConfig(
    name="JSON Validator",
    slug="json-validator",
    category="developer",
    description="Validate JSON syntax and find errors with detailed error reporting",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=60,
    cache_ttl_seconds=300,
    seo_metadata={
        'title': 'Free Online JSON Validator - LamGen',
        'description': 'Validate JSON syntax instantly. Get detailed error reports and suggestions.',
        'keywords': 'json validator, json checker, json syntax, json error detection'
    }
))
class JSONValidatorTool(BaseTool):
    """Production-ready JSON validator with detailed error reporting"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'json_input': COMMON_SCHEMAS['json_field']
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Validate JSON and provide detailed error analysis"""
        try:
            json_input = input_data.get('json_input', '')
            
            if not json_input.strip():
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="JSON input is required"
                )
            
            # Try to parse JSON
            try:
                parsed_data = json.loads(json_input)
                
                # Additional validation checks
                validation_results = self._perform_advanced_validation(parsed_data)
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'is_valid': True,
                        'parsed_data': parsed_data,
                        'validation_results': validation_results,
                        'structure_info': self._get_structure_summary(parsed_data)
                    }
                )
                
            except json.JSONDecodeError as e:
                error_analysis = self._analyze_validation_error(str(e), json_input)
                
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"JSON validation failed: {str(e)}",
                    data={
                        'is_valid': False,
                        'error_analysis': error_analysis,
                        'suggestions': self._get_validation_suggestions(error_analysis)
                    }
                )
                
        except Exception as e:
            return self.handle_error(e, "validate_json")
    
    def _perform_advanced_validation(self, data: Any) -> Dict[str, Any]:
        """Perform advanced validation beyond syntax checking"""
        results = {
            'has_duplicate_keys': False,
            'duplicate_keys': [],
            'has_empty_values': False,
            'empty_keys': [],
            'max_depth': 0,
            'total_size': 0,
            'warnings': []
        }
        
        if isinstance(data, dict):
            results['max_depth'] = self._calculate_depth(data)
            results['total_size'] = len(json.dumps(data))
            
            # Check for duplicate keys (case-sensitive)
            seen_keys = set()
            for key in data.keys():
                if key in seen_keys:
                    results['has_duplicate_keys'] = True
                    results['duplicate_keys'].append(key)
                seen_keys.add(key)
                
                # Check for empty values
                if data[key] in ['', None, []]:
                    results['has_empty_values'] = True
                    results['empty_keys'].append(key)
            
            # Add warnings for common issues
            if results['has_duplicate_keys']:
                results['warnings'].append("Duplicate object keys detected - last occurrence will override earlier ones")
            if results['has_empty_values']:
                results['warnings'].append("Empty values found - consider removing or providing default values")
        
        return results
    
    def _analyze_validation_error(self, error_msg: str, json_input: str) -> Dict[str, Any]:
        """Analyze validation error and provide detailed context"""
        # Reuse the error analysis from JSONFormatterTool
        formatter_tool = JSONFormatterTool(None)
        return formatter_tool._analyze_json_error(error_msg, json_input)
    
    def _get_validation_suggestions(self, error_info: Dict[str, Any]) -> List[str]:
        """Get validation suggestions based on error analysis"""
        formatter_tool = JSONFormatterTool(None)
        return formatter_tool._get_json_suggestions(error_info)
    
    def _get_structure_summary(self, data: Any) -> Dict[str, Any]:
        """Get summary of JSON structure"""
        formatter_tool = JSONFormatterTool(None)
        return formatter_tool._analyze_json_structure(data)


@register_tool(ToolConfig(
    name="JSON to CSV Converter",
    slug="json-csv-converter",
    category="developer",
    description="Convert JSON data to CSV format with customizable options",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    seo_metadata={
        'title': 'Free JSON to CSV Converter - LamGen',
        'description': 'Convert JSON arrays and objects to CSV format. Customizable delimiters and headers.',
        'keywords': 'json to csv, json csv converter, convert json csv, online json converter'
    }
))
class JSONToCSVConverterTool(BaseTool):
    """Production-ready JSON to CSV converter with advanced options"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'json_input': COMMON_SCHEMAS['json_field'],
            'delimiter': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                min_length=1,
                max_length=5,
                default=',',
                allowed_values=[',', ';', '\t', '|']
            ),
            'include_headers': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            ),
            'flatten_nested': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=False
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Convert JSON to CSV with advanced options"""
        try:
            json_input = input_data.get('json_input', '')
            delimiter = input_data.get('delimiter', ',')
            include_headers = input_data.get('include_headers', True)
            flatten_nested = input_data.get('flatten_nested', False)
            
            if not json_input.strip():
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="JSON input is required"
                )
            
            # Parse JSON
            try:
                data = json.loads(json_input)
            except json.JSONDecodeError as e:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Invalid JSON: {str(e)}"
                )
            
            # Convert to CSV
            success, csv_content, errors = DataProcessor.json_to_csv(data)
            
            if not success:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=errors[0] if errors else "CSV conversion failed"
                )
            
            # Apply custom options
            if delimiter != ',':
                csv_content = csv_content.replace(',', delimiter)
            
            # Generate preview
            lines = csv_content.split('\n')
            preview_lines = lines[:10]  # First 10 lines for preview
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'csv_content': csv_content,
                    'preview_lines': preview_lines,
                    'total_lines': len(lines),
                    'delimiter': delimiter,
                    'include_headers': include_headers,
                    'original_json': json_input
                },
                metadata={
                    'input_size': len(json_input),
                    'output_size': len(csv_content),
                    'conversion_ratio': len(csv_content) / len(json_input) if json_input else 0
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "convert_json_to_csv")


@register_tool(ToolConfig(
    name="JSON to TypeScript Converter",
    slug="json-to-typescript",
    category="developer",
    description="Convert JSON objects to TypeScript interfaces and types",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free JSON to TypeScript Converter - LamGen',
        'description': 'Convert JSON objects to TypeScript interfaces. Generate type definitions automatically.',
        'keywords': 'json to typescript, typescript generator, json types, ts interface generator'
    }
))
class JSONToTypeScriptTool(BaseTool):
    """Production-ready JSON to TypeScript converter with AI enhancement"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'json_input': COMMON_SCHEMAS['json_field'],
            'interface_name': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                max_length=50,
                default='GeneratedInterface'
            ),
            'export_type': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='interface',
                allowed_values=['interface', 'type', 'class']
            ),
            'optional_properties': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            ),
            'add_comments': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Convert JSON to TypeScript interfaces"""
        try:
            json_input = input_data.get('json_input', '')
            interface_name = input_data.get('interface_name', 'GeneratedInterface')
            export_type = input_data.get('export_type', 'interface')
            optional_properties = input_data.get('optional_properties', True)
            add_comments = input_data.get('add_comments', True)
            
            if not json_input.strip():
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="JSON input is required"
                )
            
            # Parse JSON
            try:
                data = json.loads(json_input)
            except json.JSONDecodeError as e:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Invalid JSON: {str(e)}"
                )
            
            # Generate TypeScript
            typescript_code = self._generate_typescript(
                data, interface_name, export_type, optional_properties, add_comments
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'typescript_code': typescript_code,
                    'interface_name': interface_name,
                    'export_type': export_type,
                    'original_json': json_input
                },
                metadata={
                    'lines_of_code': len(typescript_code.split('\n')),
                    'complexity_score': self._calculate_complexity(data)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "convert_json_to_typescript")
    
    def _generate_typescript(self, data: Any, interface_name: str, 
                          export_type: str, optional_properties: bool, add_comments: bool) -> str:
        """Generate TypeScript code from JSON data"""
        lines = []
        
        # Add header comment
        if add_comments:
            lines.append(f'// Generated TypeScript interface from JSON')
            lines.append(f'// Interface: {interface_name}')
            lines.append('')
        
        # Generate interface/type/class
        if export_type == 'interface':
            lines.append(f'export interface {interface_name} {{')
        elif export_type == 'type':
            lines.append(f'export type {interface_name} = {{')
        elif export_type == 'class':
            lines.append(f'export class {interface_name} {{')
        
        # Process the data
        if isinstance(data, dict):
            for key, value in data.items():
                ts_type = self._get_typescript_type(value, optional_properties)
                comment = f'  // {self._get_type_comment(value)}' if add_comments else ''
                lines.append(f'  {comment}{key}{ts_type};')
        elif isinstance(data, list) and data:
            # Handle array of objects
            first_item = data[0]
            if isinstance(first_item, dict):
                item_interface = f'{interface_name}Item'
                lines.append(f'export interface {item_interface} {{')
                for key, value in first_item.items():
                    ts_type = self._get_typescript_type(value, optional_properties)
                    comment = f'  // {self._get_type_comment(value)}' if add_comments else ''
                    lines.append(f'  {comment}{key}{ts_type};')
                lines.append('}')
                lines.append('')
                array_type = f'{item_interface}[]'
                if export_type == 'interface':
                    lines.append(f'export interface {interface_name} {{')
                elif export_type == 'type':
                    lines.append(f'export type {interface_name} = {{')
                elif export_type == 'class':
                    lines.append(f'export class {interface_name} {{')
                lines.append(f'  items: {array_type};')
            else:
                # Simple array
                item_type = self._get_typescript_type(first_item, optional_properties)
                array_type = f'{item_type}[]'
                if export_type == 'interface':
                    lines.append(f'export interface {interface_name} {{')
                elif export_type == 'type':
                    lines.append(f'export type {interface_name} = {{')
                elif export_type == 'class':
                    lines.append(f'export class {interface_name} {{')
                lines.append(f'  items: {array_type};')
        
        lines.append('}')
        
        return '\n'.join(lines)
    
    def _get_typescript_type(self, value: Any, optional_properties: bool) -> str:
        """Get TypeScript type for a value"""
        if isinstance(value, str):
            return '?: string' if optional_properties else ': string'
        elif isinstance(value, int):
            return '?: number' if optional_properties else ': number'
        elif isinstance(value, float):
            return '?: number' if optional_properties else ': number'
        elif isinstance(value, bool):
            return '?: boolean' if optional_properties else ': boolean'
        elif isinstance(value, list):
            if value:
                item_type = self._get_typescript_type(value[0], optional_properties)
                return f'?: {item_type.replace("?:", ":").strip()}[]' if optional_properties else f': {item_type.replace("?:", ":").strip()}[]'
            else:
                return '?: any[]' if optional_properties else ': any[]'
        elif isinstance(value, dict):
            return '?: object' if optional_properties else ': object'
        else:
            return '?: any' if optional_properties else ': any'
    
    def _get_type_comment(self, value: Any) -> str:
        """Get descriptive comment for type"""
        if isinstance(value, str):
            return f'String value: {value[:50]}...' if len(value) > 50 else f'String value: {value}'
        elif isinstance(value, (int, float)):
            return f'Numeric value: {value}'
        elif isinstance(value, bool):
            return f'Boolean value: {value}'
        elif isinstance(value, list):
            return f'Array with {len(value)} items'
        elif isinstance(value, dict):
            return f'Object with {len(value)} properties'
        else:
            return 'Unknown type'
    
    def _calculate_complexity(self, data: Any) -> int:
        """Calculate complexity score for the generated TypeScript"""
        complexity = 0
        
        if isinstance(data, dict):
            complexity += len(data) * 2
            for value in data.values():
                complexity += self._calculate_complexity(value)
        elif isinstance(data, list):
            complexity += len(data)
            for item in data:
                complexity += self._calculate_complexity(item)
        
        return complexity
