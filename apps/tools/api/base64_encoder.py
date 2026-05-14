"""
Base64 Encoder/Decoder API - Backend Implementation

Provides server-side Base64 encoding and decoding with:
- File upload support
- Batch processing
- Multiple encoding formats
- Image handling optimization
"""

import base64
import mimetypes
import re
from typing import Dict, Any, Tuple, Optional
from .base import BaseToolAPI
from .exceptions import ValidationError, ProcessingError, UnsupportedFormatError


class Base64EncoderAPI(BaseToolAPI):
    """Backend API for Base64 encoding and decoding"""
    
    def __init__(self):
        super().__init__("base64-encoder")
        self.max_input_size = 100 * 1024 * 1024  # 100MB for file uploads
    
    def __call__(self, request):
        """Make the API callable as a Django view"""
        return self.handle_request(request)
    
    def process_request(self, request, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Base64 encoding/decoding request"""
        input_data = data['data']
        options = data.get('options', {})
        
        # Extract options
        operation = options.get('operation', 'encode')  # 'encode' or 'decode'
        is_file = options.get('is_file', False)
        file_type = options.get('file_type', 'auto')
        output_format = options.get('output_format', 'base64')  # 'base64' or 'data_url'
        
        try:
            if operation == 'encode':
                return self._encode_data(input_data, is_file, file_type, output_format)
            elif operation == 'decode':
                return self._decode_data(input_data, is_file)
            else:
                raise ValidationError("Invalid operation. Must be 'encode' or 'decode'")
                
        except Exception as e:
            if isinstance(e, (ValidationError, ProcessingError)):
                raise e
            else:
                raise ProcessingError(f"Processing failed: {str(e)}")
    
    def _encode_data(self, data: str, is_file: bool, file_type: str, output_format: str) -> Dict[str, Any]:
        """Encode data to Base64"""
        try:
            if is_file:
                # Handle file encoding
                return self._encode_file_data(data, file_type, output_format)
            else:
                # Handle text encoding
                return self._encode_text_data(data, output_format)
                
        except Exception as e:
            raise ProcessingError(f"Encoding failed: {str(e)}")
    
    def _decode_data(self, data: str, is_file: bool) -> Dict[str, Any]:
        """Decode Base64 data"""
        try:
            if is_file:
                # Handle file decoding (data URL)
                return self._decode_file_data(data)
            else:
                # Handle text decoding
                return self._decode_text_data(data)
                
        except Exception as e:
            raise ProcessingError(f"Decoding failed: {str(e)}")
    
    def _encode_text_data(self, text: str, output_format: str) -> Dict[str, Any]:
        """Encode text to Base64"""
        # Clean the text first
        text = text.strip()
        
        # Encode to bytes
        text_bytes = text.encode('utf-8')
        
        # Encode to Base64
        base64_bytes = base64.b64encode(text_bytes)
        base64_str = base64_bytes.decode('ascii')
        
        result = {
            'success': True,
            'operation': 'encode',
            'input_type': 'text',
            'output_type': output_format,
            'result': base64_str,
            'stats': {
                'input_size': len(text_bytes),
                'output_size': len(base64_bytes),
                'compression_ratio': len(base64_bytes) / len(text_bytes) if text_bytes else 0,
                'encoding': 'utf-8'
            }
        }
        
        return result
    
    def _encode_file_data(self, data: str, file_type: str, output_format: str) -> Dict[str, Any]:
        """Encode file data to Base64"""
        # Detect file type if auto
        if file_type == 'auto':
            file_type = self._detect_file_type(data)
        
        # Validate file type
        if not self._is_supported_file_type(file_type):
            raise UnsupportedFormatError(
                f"Unsupported file type: {file_type}",
                format_type=file_type,
                supported_formats=self._get_supported_file_types()
            )
        
        # For file encoding, we expect binary data or base64 input
        try:
            # If input is already base64, decode first then re-encode
            if self._is_base64(data):
                file_bytes = base64.b64decode(data)
            else:
                # Assume it's binary data represented as string
                file_bytes = data.encode('latin-1')  # Use latin-1 for binary data
            
            # Encode to Base64
            base64_bytes = base64.b64encode(file_bytes)
            base64_str = base64_bytes.decode('ascii')
            
            # Create output based on format
            if output_format == 'data_url':
                mime_type = mimetypes.guess_type(f"file.{file_type}")[0] or 'application/octet-stream'
                result = f"data:{mime_type};base64,{base64_str}"
            else:
                result = base64_str
            
            return {
                'success': True,
                'operation': 'encode',
                'input_type': 'file',
                'file_type': file_type,
                'output_type': output_format,
                'result': result,
                'stats': {
                    'input_size': len(file_bytes),
                    'output_size': len(base64_bytes),
                    'compression_ratio': len(base64_bytes) / len(file_bytes) if file_bytes else 0,
                    'mime_type': mimetypes.guess_type(f"file.{file_type}")[0]
                }
            }
            
        except Exception as e:
            raise ProcessingError(f"File encoding failed: {str(e)}")
    
    def _decode_text_data(self, base64_data: str) -> Dict[str, Any]:
        """Decode Base64 text"""
        try:
            # Clean the input
            base64_data = self._clean_base64_input(base64_data)
            
            # Decode from Base64
            base64_bytes = base64.b64decode(base64_data)
            
            # Try to decode as UTF-8 text
            try:
                text = base64_bytes.decode('utf-8')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                text = base64_bytes.decode('latin-1')
                encoding = 'latin-1'
            
            return {
                'success': True,
                'operation': 'decode',
                'input_type': 'base64',
                'output_type': 'text',
                'result': text,
                'stats': {
                    'input_size': len(base64_data),
                    'output_size': len(base64_bytes),
                    'decompression_ratio': len(base64_bytes) / len(base64_data) if base64_data else 0,
                    'encoding': encoding
                }
            }
            
        except Exception as e:
            raise ProcessingError(f"Text decoding failed: {str(e)}")
    
    def _decode_file_data(self, data_url: str) -> Dict[str, Any]:
        """Decode data URL to file information"""
        try:
            # Parse data URL
            match = re.match(r'data:([^;]+);base64,(.+)', data_url)
            if not match:
                raise ValidationError("Invalid data URL format")
            
            mime_type = match.group(1)
            base64_data = match.group(2)
            
            # Decode Base64
            file_bytes = base64.b64decode(base64_data)
            
            # Extract file extension from mime type
            extension = mimetypes.guess_extension(mime_type) or '.bin'
            
            return {
                'success': True,
                'operation': 'decode',
                'input_type': 'data_url',
                'output_type': 'file',
                'result': base64_data,  # Return the base64 for download
                'file_info': {
                    'mime_type': mime_type,
                    'extension': extension,
                    'size': len(file_bytes),
                    'is_image': mime_type.startswith('image/'),
                    'is_text': mime_type.startswith('text/') or mime_type in [
                        'application/json',
                        'application/xml',
                        'application/javascript'
                    ]
                },
                'stats': {
                    'input_size': len(data_url),
                    'output_size': len(file_bytes),
                    'decompression_ratio': len(file_bytes) / len(data_url) if data_url else 0
                }
            }
            
        except Exception as e:
            if isinstance(e, (ValidationError, ProcessingError)):
                raise e
            else:
                raise ProcessingError(f"File decoding failed: {str(e)}")
    
    def _detect_file_type(self, data: str) -> str:
        """Detect file type from data"""
        # Check if it's a data URL
        if data.startswith('data:'):
            match = re.match(r'data:([^;]+)', data)
            if match:
                mime_type = match.group(1)
                # Map common mime types to extensions
                mime_to_ext = {
                    'image/jpeg': 'jpg',
                    'image/png': 'png',
                    'image/gif': 'gif',
                    'image/webp': 'webp',
                    'text/plain': 'txt',
                    'application/json': 'json',
                    'application/xml': 'xml',
                    'text/html': 'html',
                    'text/css': 'css',
                    'application/javascript': 'js'
                }
                return mime_to_ext.get(mime_type, 'bin')
        
        # Check for binary patterns
        if self._is_base64(data):
            # Try to decode and check magic bytes
            try:
                decoded = base64.b64decode(data[:100])  # Just check first part
                return self._detect_from_magic_bytes(decoded)
            except:
                pass
        
        return 'txt'  # Default to text
    
    def _detect_from_magic_bytes(self, data: bytes) -> str:
        """Detect file type from magic bytes"""
        if data.startswith(b'\xFF\xD8\xFF'):
            return 'jpg'
        elif data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
            return 'gif'
        elif data.startswith(b'RIFF') and len(data) > 8:
            return 'webp'
        elif data.startswith(b'{') or data.startswith(b'['):
            return 'json'
        elif data.startswith(b'<'):
            return 'html'
        else:
            return 'bin'
    
    def _is_base64(self, data: str) -> bool:
        """Check if string is valid Base64"""
        try:
            # Remove whitespace and check if it's valid base64
            clean_data = re.sub(r'\s+', '', data)
            base64.b64decode(clean_data)
            return True
        except:
            return False
    
    def _clean_base64_input(self, data: str) -> str:
        """Clean Base64 input for decoding"""
        # Remove whitespace, newlines, etc.
        clean_data = re.sub(r'\s+', '', data)
        
        # Remove data URL prefix if present
        if clean_data.startswith('data:'):
            match = re.match(r'data:[^;]+;base64,(.+)', clean_data)
            if match:
                clean_data = match.group(1)
        
        return clean_data
    
    def _is_supported_file_type(self, file_type: str) -> bool:
        """Check if file type is supported"""
        supported_types = self._get_supported_file_types()
        return file_type.lower() in supported_types
    
    def _get_supported_file_types(self) -> list:
        """Get list of supported file types"""
        return [
            'txt', 'json', 'xml', 'html', 'css', 'js',
            'jpg', 'jpeg', 'png', 'gif', 'webp',
            'pdf', 'csv', 'bin'
        ]
