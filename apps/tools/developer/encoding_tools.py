"""
Encoding Tools - Complete Implementation of Encoding/Decoding Utilities

Provides production-ready Base64, URL, and HTML entity encoding tools
with comprehensive validation, error handling, and security features.
"""

import base64
import urllib.parse
import html
import re
from typing import Dict, Any, List, Tuple

from apps.tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus, register_tool
from apps.tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS
from apps.tools.utils.processing import SecurityProcessor, TextProcessor
from apps.tools.utils.analytics import analytics_tracker


@register_tool(ToolConfig(
    name="Base64 Encoder",
    slug="base64-encoder",
    category="developer",
    description="Encode text to Base64 format with multiple encoding options",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=60,
    cache_ttl_seconds=300,
    seo_metadata={
        'title': 'Free Online Base64 Encoder - LamGen',
        'description': 'Encode text to Base64 format. Support for multiple character encodings and line breaks.',
        'keywords': 'base64 encoder, base64 encode, text to base64, online base64 tool'
    }
))
class Base64EncoderTool(BaseTool):
    """Production-ready Base64 encoder with advanced options"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'input_text': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                max_length=1000000,
                error_message="Text to encode is required"
            ),
            'encoding': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='utf-8',
                allowed_values=['utf-8', 'ascii', 'latin-1', 'utf-16']
            ),
            'line_breaks': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='none',
                allowed_values=['none', 'lf', 'crlf', 'cr']
            ),
            'url_safe': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=False
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Encode text to Base64 with advanced options"""
        try:
            input_text = input_data.get('input_text', '')
            encoding = input_data.get('encoding', 'utf-8')
            line_breaks = input_data.get('line_breaks', 'none')
            url_safe = input_data.get('url_safe', False)
            
            if not input_text.strip():
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Input text is required"
                )
            
            # Process line breaks
            processed_text = self._process_line_breaks(input_text, line_breaks)
            
            # Encode to bytes with specified encoding
            try:
                text_bytes = processed_text.encode(encoding)
            except UnicodeEncodeError as e:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Encoding error: {str(e)}"
                )
            
            # Encode to Base64
            if url_safe:
                encoded_bytes = base64.urlsafe_b64encode(text_bytes)
                encoded_str = encoded_bytes.decode('ascii')
            else:
                encoded_bytes = base64.b64encode(text_bytes)
                encoded_str = encoded_bytes.decode('ascii')
            
            # Generate metadata
            metadata = {
                'input_length': len(input_text),
                'output_length': len(encoded_str),
                'encoding': encoding,
                'line_breaks': line_breaks,
                'url_safe': url_safe,
                'compression_ratio': len(encoded_str) / len(input_text) if input_text else 0
            }
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'encoded_text': encoded_str,
                    'original_text': input_text,
                    'encoding_options': {
                        'encoding': encoding,
                        'line_breaks': line_breaks,
                        'url_safe': url_safe
                    }
                },
                metadata=metadata
            )
            
        except Exception as e:
            return self.handle_error(e, "encode_base64")
    
    def _process_line_breaks(self, text: str, line_break_type: str) -> str:
        """Process line breaks according to specified type"""
        if line_break_type == 'none':
            return text
        elif line_break_type == 'lf':
            return text.replace('\r\n', '\n').replace('\r', '\n')
        elif line_break_type == 'crlf':
            return text.replace('\r\n', '\r\n').replace('\r', '\r\n').replace('\n', '\r\n')
        elif line_break_type == 'cr':
            return text.replace('\r\n', '\r').replace('\n', '\r')
        else:
            return text


@register_tool(ToolConfig(
    name="Base64 Decoder",
    slug="base64-decoder",
    category="developer",
    description="Decode Base64 text with automatic encoding detection",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=60,
    cache_ttl_seconds=300,
    seo_metadata={
        'title': 'Free Online Base64 Decoder - LamGen',
        'description': 'Decode Base64 text with automatic encoding detection. Support for multiple character sets.',
        'keywords': 'base64 decoder, base64 decode, base64 to text, online base64 decoder'
    }
))
class Base64DecoderTool(BaseTool):
    """Production-ready Base64 decoder with encoding detection"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'base64_input': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                max_length=1000000,
                error_message="Base64 input is required"
            ),
            'encoding': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='utf-8',
                allowed_values=['utf-8', 'ascii', 'latin-1', 'utf-16', 'auto']
            ),
            'url_safe': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=False
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Decode Base64 text with encoding detection"""
        try:
            base64_input = input_data.get('base64_input', '')
            encoding = input_data.get('encoding', 'utf-8')
            url_safe = input_data.get('url_safe', False)
            
            if not base64_input.strip():
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Base64 input is required"
                )
            
            # Clean Base64 input
            cleaned_input = self._clean_base64_input(base64_input)
            
            # Decode Base64
            try:
                if url_safe:
                    decoded_bytes = base64.urlsafe_b64decode(cleaned_input)
                else:
                    decoded_bytes = base64.b64decode(cleaned_input)
            except Exception as e:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Invalid Base64: {str(e)}"
                )
            
            # Auto-detect encoding if requested
            if encoding == 'auto':
                encoding = self._detect_encoding(decoded_bytes)
            
            # Decode bytes to string
            try:
                decoded_text = decoded_bytes.decode(encoding)
            except UnicodeDecodeError as e:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error_message=f"Decoding error with {encoding}: {str(e)}"
                )
            
            # Validate decoded content
            validation_info = self._validate_decoded_content(decoded_text)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'decoded_text': decoded_text,
                    'original_base64': base64_input,
                    'detected_encoding': encoding,
                    'validation_info': validation_info
                },
                metadata={
                    'input_length': len(base64_input),
                    'output_length': len(decoded_text),
                    'encoding': encoding,
                    'url_safe': url_safe
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "decode_base64")
    
    def _clean_base64_input(self, input_text: str) -> str:
        """Clean Base64 input for common issues"""
        # Remove whitespace
        cleaned = re.sub(r'\s+', '', input_text)
        
        # Remove common prefixes/suffixes
        cleaned = re.sub(r'^data:[^,]+,base64,', '', cleaned)
        cleaned = cleaned.strip()
        
        # Fix padding issues
        padding_needed = len(cleaned) % 4
        if padding_needed:
            cleaned += '=' * (4 - padding_needed)
        
        return cleaned
    
    def _detect_encoding(self, data: bytes) -> str:
        """Simple encoding detection"""
        encodings_to_try = ['utf-8', 'ascii', 'latin-1', 'utf-16']
        
        for encoding in encodings_to_try:
            try:
                data.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        
        return 'utf-8'  # Default fallback
    
    def _validate_decoded_content(self, text: str) -> Dict[str, Any]:
        """Validate decoded content and provide insights"""
        validation = {
            'is_printable': True,
            'non_printable_chars': 0,
            'contains_control_chars': False,
            'likely_text': True,
            'encoding_confidence': 'high'
        }
        
        # Check for non-printable characters
        non_printable_count = 0
        control_chars = []
        
        for char in text:
            if ord(char) < 32 or ord(char) > 126:
                if char not in ['\n', '\r', '\t']:
                    non_printable_count += 1
                if ord(char) < 32:
                    control_chars.append(char)
                    validation['contains_control_chars'] = True
        
        validation['non_printable_chars'] = non_printable_count
        validation['control_characters'] = control_chars
        
        # Determine if likely text
        if non_printable_count > len(text) * 0.1:
            validation['likely_text'] = False
            validation['encoding_confidence'] = 'low'
        elif non_printable_count > 0:
            validation['encoding_confidence'] = 'medium'
        
        return validation


@register_tool(ToolConfig(
    name="URL Encoder",
    slug="url-encoder",
    category="developer",
    description="Encode URLs for safe transmission with various encoding options",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=60,
    cache_ttl_seconds=300,
    seo_metadata={
        'title': 'Free Online URL Encoder - LamGen',
        'description': 'Encode URLs for safe transmission. Support for multiple encoding schemes.',
        'keywords': 'url encoder, url encode, encode url, online url encoder'
    }
))
class URLEncoderTool(BaseTool):
    """Production-ready URL encoder with multiple encoding schemes"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'url_input': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                max_length=2048,
                error_message="URL input is required"
            ),
            'encoding_scheme': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='url_encoded',
                allowed_values=[
                    'url_encoded',
                    'base64',
                    'html_entity',
                    'punycode',
                    'double_encoded'
                ]
            ),
            'plus_as_space': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Encode URL with specified scheme"""
        try:
            url_input = input_data.get('url_input', '')
            encoding_scheme = input_data.get('encoding_scheme', 'url_encoded')
            plus_as_space = input_data.get('plus_as_space', True)
            
            if not url_input.strip():
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="URL input is required"
                )
            
            # Validate URL format
            is_valid, normalized_url = SecurityProcessor.validate_url(url_input)
            if not is_valid:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Invalid URL format"
                )
            
            # Apply encoding scheme
            encoded_url = self._apply_encoding_scheme(
                normalized_url, encoding_scheme, plus_as_space
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'encoded_url': encoded_url,
                    'original_url': normalized_url,
                    'encoding_scheme': encoding_scheme,
                    'url_info': self._analyze_url(normalized_url)
                },
                metadata={
                    'input_length': len(url_input),
                    'output_length': len(encoded_url),
                    'encoding_scheme': encoding_scheme
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "encode_url")
    
    def _apply_encoding_scheme(self, url: str, scheme: str, plus_as_space: bool) -> str:
        """Apply specific encoding scheme to URL"""
        if scheme == 'url_encoded':
            # Standard URL encoding
            encoded = urllib.parse.quote(url, safe='')
            if plus_as_space:
                encoded = encoded.replace('+', '%20')
            return encoded
        
        elif scheme == 'base64':
            # Base64 encoding
            url_bytes = url.encode('utf-8')
            encoded = base64.b64encode(url_bytes).decode('ascii')
            return encoded
        
        elif scheme == 'html_entity':
            # HTML entity encoding
            return html.escape(url)
        
        elif scheme == 'punycode':
            # Punycode for internationalized domain names
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.netloc:
                    # Convert domain to punycode
                    import idna
                    punycode_domain = idna.encode(parsed.netloc)
                    # Reconstruct URL
                    new_netloc = punycode_domain.decode('ascii')
                    return url.replace(parsed.netloc, new_netloc)
                return url
            except ImportError:
                return url  # idna not available
            except Exception:
                return url
        
        elif scheme == 'double_encoded':
            # Double URL encoding
            first_encode = urllib.parse.quote(url, safe='')
            second_encode = urllib.parse.quote(first_encode, safe='')
            return second_encode
        
        return url  # Fallback
    
    def _analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyze URL and provide insights"""
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        return {
            'scheme': parsed.scheme,
            'domain': parsed.netloc,
            'path': parsed.path,
            'query_params': dict(query_params),
            'fragment': parsed.fragment,
            'is_secure': parsed.scheme == 'https',
            'has_query': len(query_params) > 0,
            'param_count': len(query_params)
        }


@register_tool(ToolConfig(
    name="HTML Entity Encoder",
    slug="html-entity-encoder",
    category="developer",
    description="Encode HTML entities for security and display purposes",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=60,
    cache_ttl_seconds=300,
    seo_metadata={
        'title': 'Free Online HTML Entity Encoder - LamGen',
        'description': 'Encode HTML entities for security. Convert special characters to HTML entities.',
        'keywords': 'html entity encoder, html encode, html entities, online html encoder'
    }
))
class HTMLEntityEncoderTool(BaseTool):
    """Production-ready HTML entity encoder with security features"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'html_input': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                max_length=50000,
                error_message="HTML input is required"
            ),
            'encoding_level': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='standard',
                allowed_values=['minimal', 'standard', 'comprehensive', 'numeric']
            ),
            'preserve_newlines': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            ),
            'encode_quotes': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Encode HTML entities with security considerations"""
        try:
            html_input = input_data.get('html_input', '')
            encoding_level = input_data.get('encoding_level', 'standard')
            preserve_newlines = input_data.get('preserve_newlines', True)
            encode_quotes = input_data.get('encode_quotes', True)
            
            if not html_input.strip():
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="HTML input is required"
                )
            
            # Apply HTML entity encoding
            encoded_html = self._apply_html_encoding(
                html_input, encoding_level, preserve_newlines, encode_quotes
            )
            
            # Analyze original HTML
            analysis = self._analyze_html_content(html_input)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'encoded_html': encoded_html,
                    'original_html': html_input,
                    'encoding_level': encoding_level,
                    'content_analysis': analysis
                },
                metadata={
                    'input_length': len(html_input),
                    'output_length': len(encoded_html),
                    'encoding_level': encoding_level
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "encode_html_entities")
    
    def _apply_html_encoding(self, html: str, level: str, 
                           preserve_newlines: bool, encode_quotes: bool) -> str:
        """Apply HTML entity encoding based on level"""
        if level == 'minimal':
            # Only encode critical characters
            encoded = html.replace('&', '&amp;')
            if encode_quotes:
                encoded = encoded.replace('"', '&quot;').replace("'", '&#x27;')
            encoded = encoded.replace('<', '&lt;').replace('>', '&gt;')
        
        elif level == 'standard':
            # Encode common special characters
            encoded = html.escape(html, quote=encode_quotes)
            if not preserve_newlines:
                encoded = encoded.replace('\n', ' ').replace('\r', ' ')
        
        elif level == 'comprehensive':
            # Encode all non-alphanumeric characters
            encoded = ''
            for char in html:
                if char.isalnum() or char.isspace():
                    encoded += char
                else:
                    encoded += f'&#{ord(char)};'
            if not preserve_newlines:
                encoded = encoded.replace('\n', ' ').replace('\r', ' ')
        
        elif level == 'numeric':
            # Numeric entities for all non-alphanumeric
            encoded = ''
            for char in html:
                if char.isalnum() or char.isspace():
                    encoded += char
                else:
                    encoded += f'&#{ord(char)};'
            if not preserve_newlines:
                encoded = encoded.replace('\n', ' ').replace('\r', ' ')
        
        return encoded
    
    def _analyze_html_content(self, html: str) -> Dict[str, Any]:
        """Analyze HTML content for security insights"""
        analysis = {
            'has_script_tags': '<script' in html.lower(),
            'has_iframe_tags': '<iframe' in html.lower(),
            'has_form_tags': '<form' in html.lower(),
            'has_input_tags': '<input' in html.lower(),
            'special_char_count': 0,
            'tag_count': 0,
            'security_risk': 'low'
        }
        
        # Count special characters and tags
        special_chars = '<>&"\''
        analysis['special_char_count'] = sum(html.count(char) for char in special_chars)
        
        # Count HTML tags (simplified)
        import re
        tags = re.findall(r'<[^>]+>', html.lower())
        analysis['tag_count'] = len(tags)
        
        # Assess security risk
        if analysis['has_script_tags'] or analysis['has_iframe_tags']:
            analysis['security_risk'] = 'high'
        elif analysis['has_form_tags'] or analysis['has_input_tags']:
            analysis['security_risk'] = 'medium'
        
        return analysis
