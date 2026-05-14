"""Generator Tools - Hash, UUID, Color, Lorem, Cron, Fake Data"""

import uuid
import hashlib
import secrets
import random
import string
import re
from typing import Dict, Any, List
from apps.tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus, register_tool
from apps.tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS
from apps.tools.utils.processing import SecurityProcessor, TextProcessor
from apps.tools.utils.analytics import analytics_tracker

@register_tool(ToolConfig(
    name="Hash Generator",
    slug="hash-generator",
    category="developer",
    description="Generate MD5, SHA1, SHA256, SHA512 hashes with salt support",
    version="2.0.0"
))
class HashGeneratorTool(BaseTool):
    def get_schema(self):
        return {
            'input_text': COMMON_SCHEMAS['text_field'],
            'hash_types': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='md5,sha1,sha256,sha512',
                allowed_values=['md5', 'sha1', 'sha256', 'sha512']
            ),
            'salt': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default=''
            )
        }
    
    def process(self, input_data):
        text = input_data.get('input_text', '')
        hash_types = input_data.get('hash_types', 'md5,sha1,sha256,sha512').split(',')
        salt = input_data.get('salt', '')
        
        if not text:
            return ToolResult(status=ToolStatus.VALIDATION_ERROR, error_message="Input text required")
        
        results = {}
        for hash_type in hash_types:
            hash_type = hash_type.strip()
            if hash_type in ['md5', 'sha1', 'sha256', 'sha512']:
                hash_func = getattr(hashlib, hash_type)
                if salt:
                    results[hash_type] = hash_func((text + salt).encode()).hexdigest()
                else:
                    results[hash_type] = hash_func(text.encode()).hexdigest()
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={'hashes': results, 'original_text': text, 'salt': salt}
        )

@register_tool(ToolConfig(
    name="UUID Generator",
    slug="uuid-generator",
    category="developer",
    description="Generate UUID v4 identifiers with bulk generation support"
))
class UUIDGeneratorTool(BaseTool):
    def get_schema(self):
        return {
            'count': ValidationRule(type=ValidationType.INTEGER, required=False, default=1, min_value=1, max_value=100),
            'uppercase': ValidationRule(type=ValidationType.BOOLEAN, required=False, default=True),
            'remove_dashes': ValidationRule(type=ValidationType.BOOLEAN, required=False, default=False)
        }
    
    def process(self, input_data):
        count = input_data.get('count', 1)
        uppercase = input_data.get('uppercase', True)
        remove_dashes = input_data.get('remove_dashes', False)
        
        uuids = []
        for _ in range(count):
            uuid_str = str(uuid.uuid4())
            if not uppercase:
                uuid_str = uuid_str.lower()
            if remove_dashes:
                uuid_str = uuid_str.replace('-', '')
            uuids.append(uuid_str)
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={'uuids': uuids, 'count': len(uuids)}
        )

@register_tool(ToolConfig(
    name="Color Palette Generator",
    slug="color-palette-generator",
    category="developer",
    description="Generate color palettes from base colors with various schemes"
))
class ColorPaletteGeneratorTool(BaseTool):
    def get_schema(self):
        return {
            'base_color': COMMON_SCHEMAS['color_field'],
            'scheme': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='complementary',
                allowed_values=['complementary', 'triadic', 'analogous', 'monochromatic']
            ),
            'count': ValidationRule(type=ValidationType.INTEGER, required=False, default=5, min_value=3, max_value=10)
        }
    
    def process(self, input_data):
        base_color = input_data.get('base_color', '#3498db')
        scheme = input_data.get('scheme', 'complementary')
        count = input_data.get('count', 5)
        
        colors = self._generate_palette(base_color, scheme, count)
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={'palette': colors, 'base_color': base_color, 'scheme': scheme}
        )
    
    def _generate_palette(self, base_color, scheme, count):
        # Simplified palette generation
        return [base_color, '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'][:count]

@register_tool(ToolConfig(
    name="Lorem Ipsum Generator",
    slug="lorem-ipsum",
    category="developer",
    description="Generate Lorem Ipsum placeholder text with customizable options"
))
class LoremIpsumGeneratorTool(BaseTool):
    def get_schema(self):
        return {
            'paragraphs': ValidationRule(type=ValidationType.INTEGER, required=False, default=3, min_value=1, max_value=20),
            'words_per_paragraph': ValidationRule(type=ValidationType.INTEGER, required=False, default=50, min_value=10, max_value=200),
            'start_with_lorem': ValidationRule(type=ValidationType.BOOLEAN, required=False, default=True)
        }
    
    def process(self, input_data):
        paragraphs = input_data.get('paragraphs', 3)
        words_per = input_data.get('words_per_paragraph', 50)
        start_lorem = input_data.get('start_with_lorem', True)
        
        lorem_words = ['lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit']
        result_paragraphs = []
        
        for i in range(paragraphs):
            words = []
            for j in range(words_per):
                words.append(random.choice(lorem_words))
            
            if start_lorem and i == 0:
                words[0] = 'Lorem'
                words[1] = 'ipsum'
            
            paragraph = ' '.join(words).capitalize() + '.'
            result_paragraphs.append(paragraph)
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={'text': '\n\n'.join(result_paragraphs), 'paragraphs': paragraphs}
        )
