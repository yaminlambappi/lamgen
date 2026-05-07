"""
Processing Utilities - Shared Processing Logic for LamGen Tools

Provides common processing functions, file handling,
text manipulation, and data transformation utilities.
"""

import json
import re
import base64
import hashlib
import urllib.parse
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
import mimetypes
import magic

from django.core.files.uploadedfile import UploadedFile
from django.conf import settings


class FileProcessor:
    """
    Unified file processing utilities for all tools.
    Handles validation, conversion, and safe processing.
    """
    
    @staticmethod
    def validate_file(file_obj: UploadedFile, allowed_types: List[str] = None, 
                     max_size_mb: int = 10) -> Tuple[bool, List[str]]:
        """
        Validate uploaded file against type and size constraints.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        # Check file size
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_obj.size > max_size_bytes:
            errors.append(f"File size ({file_obj.size / 1024 / 1024:.1f}MB) exceeds maximum ({max_size_mb}MB)")
        
        # Check file type using both extension and MIME type
        if allowed_types:
            # Check MIME type using python-magic
            try:
                file_mime = magic.from_buffer(file_obj.read(2048), mime=True)
                file_obj.seek(0)  # Reset file pointer
                
                if file_mime not in allowed_types:
                    errors.append(f"File type ({file_mime}) not allowed. Allowed types: {', '.join(allowed_types)}")
            except Exception as e:
                errors.append(f"Could not determine file type: {str(e)}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def read_text_file(file_obj: UploadedFile, encoding: str = 'utf-8') -> Tuple[bool, str, List[str]]:
        """
        Safely read text content from uploaded file.
        
        Returns:
            Tuple[bool, str, List[str]]: (success, content, error_messages)
        """
        try:
            content = file_obj.read().decode(encoding)
            return True, content, []
        except UnicodeDecodeError:
            return False, "", ["File encoding not supported. Please ensure file is UTF-8 encoded."]
        except Exception as e:
            return False, "", [f"Error reading file: {str(e)}"]
    
    @staticmethod
    def get_file_info(file_obj: UploadedFile) -> Dict[str, Any]:
        """Get comprehensive file information"""
        return {
            'name': file_obj.name,
            'size': file_obj.size,
            'size_mb': round(file_obj.size / 1024 / 1024, 2),
            'content_type': file_obj.content_type,
            'extension': FileProcessor.get_file_extension(file_obj.name),
            'mime_type': magic.from_buffer(file_obj.read(2048), mime=True) if file_obj.size > 0 else 'unknown'
        }
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension from filename"""
        return filename.split('.')[-1].lower() if '.' in filename else ''
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Generate safe filename for storage"""
        # Remove dangerous characters
        safe_chars = re.sub(r'[^\w\s.-]', '', filename)
        # Replace spaces with underscores
        safe_chars = re.sub(r'\s+', '_', safe_chars)
        # Remove consecutive dots
        safe_chars = re.sub(r'\.+', '.', safe_chars)
        # Ensure filename doesn't start with dot
        safe_chars = safe_chars.lstrip('.')
        
        return safe_chars or 'file'


class TextProcessor:
    """
    Comprehensive text processing utilities for various tool types.
    """
    
    @staticmethod
    def clean_text(text: str, remove_extra_whitespace: bool = True, 
                   remove_special_chars: bool = False) -> str:
        """
        Clean text with various options.
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        if remove_extra_whitespace:
            text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters (keep basic punctuation)
        if remove_special_chars:
            text = re.sub(r'[^\w\s.,!?;:\-\'"()]', '', text)
        
        return text
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text using sophisticated algorithm"""
        if not text:
            return 0
        
        # Split on whitespace but handle contractions and hyphenated words
        words = re.findall(r"\b\w+(?:[-']\w+)*\b", text.lower())
        return len(words)
    
    @staticmethod
    def count_characters(text: str, include_spaces: bool = True) -> int:
        """Count characters with optional space inclusion"""
        if include_spaces:
            return len(text)
        else:
            return len(text.replace(' ', ''))
    
    @staticmethod
    def count_sentences(text: str) -> int:
        """Count sentences using punctuation patterns"""
        if not text:
            return 0
        
        # Split on sentence-ending punctuation followed by whitespace or end
        sentences = re.split(r'[.!?]+(?=\s|$)', text.strip())
        # Filter out empty strings
        return len([s for s in sentences if s.strip()])
    
    @staticmethod
    def count_paragraphs(text: str) -> int:
        """Count paragraphs (double newlines)"""
        if not text:
            return 0
        
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        return len(paragraphs)
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract all URLs from text"""
        url_pattern = r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract all email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers in various formats"""
        phone_patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # 555-555-5555
            r'\b\(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b',  # (555) 555-5555
            r'\b\d{10}\b',  # 5555555555
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        return phones
    
    @staticmethod
    def calculate_readability(text: str) -> Dict[str, float]:
        """
        Calculate readability metrics using Flesch-Kincaid formula.
        """
        if not text:
            return {'flesch_score': 0.0, 'reading_level': 'Unknown'}
        
        word_count = TextProcessor.count_words(text)
        sentence_count = TextProcessor.count_sentences(text)
        
        if word_count == 0 or sentence_count == 0:
            return {'flesch_score': 0.0, 'reading_level': 'Unknown'}
        
        # Count syllables (simplified)
        syllable_count = sum(TextProcessor._count_syllables(word) for word in text.split())
        
        # Flesch Reading Ease score
        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count
        
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Determine reading level
        if flesch_score >= 90:
            reading_level = 'Very Easy'
        elif flesch_score >= 80:
            reading_level = 'Easy'
        elif flesch_score >= 70:
            reading_level = 'Fairly Easy'
        elif flesch_score >= 60:
            reading_level = 'Standard'
        elif flesch_score >= 50:
            reading_level = 'Fairly Difficult'
        elif flesch_score >= 30:
            reading_level = 'Difficult'
        else:
            reading_level = 'Very Difficult'
        
        return {
            'flesch_score': round(flesch_score, 1),
            'reading_level': reading_level,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_syllables_per_word': round(avg_syllables_per_word, 1)
        }
    
    @staticmethod
    def _count_syllables(word: str) -> int:
        """Count syllables in a word (simplified algorithm)"""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        prev_char_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_char_was_vowel:
                syllable_count += 1
            prev_char_was_vowel = is_vowel
        
        # Subtract 1 for silent 'e' at end
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(syllable_count, 1)


class DataProcessor:
    """
    Data transformation and format conversion utilities.
    """
    
    @staticmethod
    def json_to_csv(json_data: Union[str, Dict, List]) -> Tuple[bool, str, List[str]]:
        """
        Convert JSON data to CSV format.
        
        Returns:
            Tuple[bool, str, List[str]]: (success, csv_content, error_messages)
        """
        try:
            # Parse JSON if string
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            errors = []
            
            if isinstance(data, dict):
                # Convert single object to list
                data = [data]
            elif not isinstance(data, list):
                errors.append("JSON must be an object or array of objects")
                return False, "", errors
            
            if not data:
                errors.append("JSON data is empty")
                return False, "", errors
            
            # Extract headers from first object
            headers = list(data[0].keys())
            
            # Build CSV
            csv_lines = [','.join(headers)]
            
            for item in data:
                row = []
                for header in headers:
                    value = item.get(header, '')
                    # Escape commas and quotes
                    if isinstance(value, str):
                        if ',' in value or '"' in value or '\n' in value:
                            # Escape double quotes by doubling them, then wrap in quotes for CSV
                            value = '"' + value.replace('"', '""') + '"'
                    elif isinstance(value, (list, dict)):
                        value = json.dumps(value)
                        value = '"' + value.replace('"', '""') + '"'
                    row.append(str(value))
                csv_lines.append(','.join(row))
            
            csv_content = '\n'.join(csv_lines)
            return True, csv_content, []
            
        except json.JSONDecodeError as e:
            return False, "", [f"Invalid JSON: {str(e)}"]
        except Exception as e:
            return False, "", [f"Conversion error: {str(e)}"]
    
    @staticmethod
    def csv_to_json(csv_data: str) -> Tuple[bool, str, List[str]]:
        """
        Convert CSV data to JSON format.
        
        Returns:
            Tuple[bool, str, List[str]]: (success, json_content, error_messages)
        """
        try:
            lines = csv_data.strip().split('\n')
            if len(lines) < 2:
                return False, "", ["CSV must have at least a header and one data row"]
            
            # Parse header
            header_line = lines[0]
            headers = [h.strip().strip('"') for h in header_line.split(',')]
            
            # Parse data rows
            data = []
            for line in lines[1:]:
                if not line.strip():
                    continue
                
                # Simple CSV parsing (handles quoted fields)
                values = DataProcessor._parse_csv_line(line)
                
                if len(values) != len(headers):
                    return False, "", [f"Row has {len(values)} values but expected {len(headers)}"]
                
                row_data = dict(zip(headers, values))
                data.append(row_data)
            
            json_content = json.dumps(data, indent=2)
            return True, json_content, []
            
        except Exception as e:
            return False, "", [f"Conversion error: {str(e)}"]
    
    @staticmethod
    def _parse_csv_line(line: str) -> List[str]:
        """Parse CSV line handling quoted fields"""
        values = []
        current_value = ""
        in_quotes = False
        
        for char in line:
            if char == '"':
                if in_quotes and current_value.endswith('"'):
                    # End of quoted field
                    current_value = current_value[:-1]  # Remove closing quote
                    in_quotes = False
                elif not in_quotes:
                    # Start of quoted field
                    in_quotes = True
                else:
                    # Quote inside quoted field
                    current_value += char
            elif char == ',' and not in_quotes:
                # Field separator
                values.append(current_value)
                current_value = ""
            else:
                current_value += char
        
        # Add last value
        values.append(current_value)
        return values
    
    @staticmethod
    def format_bytes(bytes_count: int) -> str:
        """Format bytes in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"
    
    @staticmethod
    def generate_hash(data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """Generate hash of data using specified algorithm"""
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        elif algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'sha512':
            hasher = hashlib.sha512()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        hasher.update(data)
        return hasher.hexdigest()


class SecurityProcessor:
    """
    Security and sanitization utilities.
    """
    
    @staticmethod
    def sanitize_html(html: str, allowed_tags: List[str] = None) -> str:
        """
        Basic HTML sanitization (simplified - use proper library in production).
        """
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        # Remove dangerous tags and attributes
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form', 'input', 'button']
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'javascript:']
        
        # Remove dangerous tags
        for tag in dangerous_tags:
            html = re.sub(f'<{tag}.*?>.*?</{tag}>', '', html, flags=re.IGNORECASE | re.DOTALL)
            html = re.sub(f'<{tag}.*?>', '', html, flags=re.IGNORECASE)
        
        # Remove dangerous attributes
        for attr in dangerous_attrs:
            html = re.sub(f'{attr}=["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        
        return html
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for secure storage.
        """
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate cryptographically secure random token.
        """
        import secrets
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """
        Validate URL and return normalized version.
        """
        if not url:
            return False, "URL is required"
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL validation
        url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        
        if re.match(url_pattern, url):
            return True, url
        else:
            return False, "Invalid URL format"


class FormatProcessor:
    """
    Format-specific processing utilities.
    """
    
    @staticmethod
    def format_json(json_str: str, indent: int = 2) -> Tuple[bool, str, List[str]]:
        """Format JSON string with proper indentation"""
        try:
            data = json.loads(json_str)
            formatted = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)
            return True, formatted, []
        except json.JSONDecodeError as e:
            return False, "", [f"Invalid JSON: {str(e)}"]
    
    @staticmethod
    def minify_json(json_str: str) -> Tuple[bool, str, List[str]]:
        """Minify JSON string"""
        try:
            data = json.loads(json_str)
            minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            return True, minified, []
        except json.JSONDecodeError as e:
            return False, "", [f"Invalid JSON: {str(e)}"]
    
    @staticmethod
    def format_css(css_str: str) -> str:
        """Basic CSS formatting"""
        # Add newlines after semicolons and braces
        css = re.sub(r';', ';\n', css_str)
        css = re.sub(r'{', ' {\n  ', css)
        css = re.sub(r'}', '\n}\n', css)
        
        # Remove extra whitespace
        css = re.sub(r'\n\s*\n', '\n', css)
        css = re.sub(r'\s+', ' ', css)
        
        return css.strip()
    
    @staticmethod
    def minify_css(css_str: str) -> str:
        """Basic CSS minification"""
        # Remove comments
        css = re.sub(r'/\*.*?\*/', '', css_str, flags=re.DOTALL)
        
        # Remove whitespace
        css = re.sub(r'\s+', ' ', css)
        css = re.sub(r';\s*', ';', css)
        css = re.sub(r':\s*', ':', css)
        css = re.sub(r'{\s*', '{', css)
        css = re.sub(r';\s*}', '}', css)
        css = re.sub(r'\s*}', '}', css)
        
        return css.strip()
    
    @staticmethod
    def format_js(js_str: str) -> str:
        """Basic JavaScript formatting"""
        # This is simplified - use proper formatter in production
        js = re.sub(r';', ';\n', js_str)
        js = re.sub(r'{', ' {\n  ', js)
        js = re.sub(r'}', '\n}\n', js)
        
        # Remove extra whitespace
        js = re.sub(r'\n\s*\n', '\n', js)
        js = re.sub(r'\s+', ' ', js)
        
        return js.strip()
    
    @staticmethod
    def minify_js(js_str: str) -> str:
        """Basic JavaScript minification"""
        # Remove comments
        js = re.sub(r'//.*?\n', '', js_str)
        js = re.sub(r'/\*.*?\*/', '', js, flags=re.DOTALL)
        
        # Remove whitespace
        js = re.sub(r'\s+', ' ', js)
        js = re.sub(r';\s*', ';', js)
        js = re.sub(r'{\s*', '{', js)
        js = re.sub(r';\s*}', '}', js)
        js = re.sub(r'\s*}', '}', js)
        
        return js.strip()
