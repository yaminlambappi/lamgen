"""
Regex Tester API - Backend Implementation

Provides server-side regular expression testing with:
- Advanced regex engine
- Performance analysis
- Pattern optimization suggestions
- Match highlighting and analysis
"""

import re
import time
from typing import Dict, Any, List, Tuple, Optional
from .base import BaseToolAPI
from .exceptions import ValidationError, ProcessingError


class RegexTesterAPI(BaseToolAPI):
    """Backend API for regular expression testing"""
    
    def __init__(self):
        super().__init__("regex-tester")
        self.max_input_size = 10 * 1024 * 1024  # 10MB for text input
        self.max_execution_time = 10  # 10 seconds max execution time
    
    def __call__(self, request):
        """Make the API callable as a Django view"""
        return self.handle_request(request)
    
    def process_request(self, request, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process regex testing request"""
        input_data = data['data']
        options = data.get('options', {})
        
        # Extract options
        pattern = options.get('pattern', '')
        flags = options.get('flags', [])
        test_string = input_data
        highlight_matches = options.get('highlight_matches', True)
        performance_analysis = options.get('performance_analysis', True)
        
        try:
            # Validate inputs
            if not pattern:
                raise ValidationError("Pattern cannot be empty")
            
            if not test_string:
                return {
                    'valid': True,
                    'pattern': pattern,
                    'flags': flags,
                    'matches': [],
                    'stats': {
                        'total_matches': 0,
                        'execution_time': 0,
                        'pattern_complexity': self._analyze_pattern_complexity(pattern)
                    }
                }
            
            # Compile regex with flags
            compiled_regex = self._compile_regex(pattern, flags)
            
            # Test the regex
            start_time = time.time()
            matches = self._test_regex(compiled_regex, test_string, highlight_matches)
            execution_time = time.time() - start_time
            
            # Analyze results
            stats = self._analyze_results(matches, execution_time, performance_analysis)
            
            # Get pattern suggestions
            suggestions = self._get_pattern_suggestions(pattern, matches, stats)
            
            return {
                'valid': True,
                'pattern': pattern,
                'flags': flags,
                'matches': matches,
                'stats': stats,
                'suggestions': suggestions
            }
            
        except re.error as e:
            raise ProcessingError(
                f"Invalid regular expression: {str(e)}",
                processing_type="regex_compilation",
                details={
                    'error_position': getattr(e, 'pos', None),
                    'error_pattern': pattern
                }
            )
        except Exception as e:
            if isinstance(e, (ValidationError, ProcessingError)):
                raise e
            else:
                raise ProcessingError(f"Regex testing failed: {str(e)}")
    
    def _compile_regex(self, pattern: str, flags: List[str]) -> re.Pattern:
        """Compile regex with specified flags"""
        flag_map = {
            'i': re.IGNORECASE,
            'm': re.MULTILINE,
            's': re.DOTALL,
            'x': re.VERBOSE,
            'a': re.ASCII,
            'l': re.LOCALE,
            'u': re.UNICODE
        }
        
        regex_flags = 0
        for flag in flags:
            if flag.lower() in flag_map:
                regex_flags |= flag_map[flag.lower()]
        
        try:
            return re.compile(pattern, regex_flags)
        except re.error as e:
            raise e
    
    def _test_regex(self, compiled_regex: re.Pattern, test_string: str, highlight: bool) -> List[Dict[str, Any]]:
        """Test regex against test string"""
        matches = []
        
        # Find all matches
        for match in compiled_regex.finditer(test_string):
            match_data = {
                'match': match.group(),
                'start': match.start(),
                'end': match.end(),
                'groups': list(match.groups()),
                'groupdict': match.groupdict(),
                'span': match.span()
            }
            
            if highlight:
                match_data['highlighted'] = self._create_highlighted_text(
                    test_string, match.start(), match.end()
                )
            
            matches.append(match_data)
            
            # Prevent infinite loops with very large inputs
            if len(matches) >= 10000:
                break
        
        return matches
    
    def _create_highlighted_text(self, text: str, start: int, end: int) -> str:
        """Create highlighted version of matched text"""
        before = text[:start]
        match = text[start:end]
        after = text[end:]
        
        # Escape HTML entities
        before = self._escape_html(before)
        match = self._escape_html(match)
        after = self._escape_html(after)
        
        return f"{before}<mark>{match}</mark>{after}"
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML entities"""
        return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))
    
    def _analyze_results(self, matches: List[Dict], execution_time: float, performance_analysis: bool) -> Dict[str, Any]:
        """Analyze regex test results"""
        stats = {
            'total_matches': len(matches),
            'execution_time': round(execution_time, 4),
            'pattern_complexity': self._analyze_pattern_complexity(matches[0]['match'] if matches else '')
        }
        
        if performance_analysis and matches:
            stats.update({
                'average_match_length': sum(len(m['match']) for m in matches) / len(matches),
                'longest_match': max(len(m['match']) for m in matches),
                'shortest_match': min(len(m['match']) for m in matches),
                'matches_per_second': len(matches) / execution_time if execution_time > 0 else 0,
                'has_groups': any(m['groups'] for m in matches),
                'has_named_groups': any(m['groupdict'] for m in matches),
                'unique_matches': len(set(m['match'] for m in matches))
            })
        
        return stats
    
    def _analyze_pattern_complexity(self, pattern: str) -> str:
        """Analyze regex pattern complexity"""
        complexity_score = 0
        
        # Check for complex constructs
        complex_constructs = [
            (r'\(\?=', 3),  # Lookahead
            (r'\(\?!', 3),  # Negative lookahead
            (r'\(\?<=', 3),  # Lookbehind
            (r'\(\?<!', 3),  # Negative lookbehind
            (r'\(\?P<', 2),  # Named groups
            (r'\(\?#', 1),   # Comments
            (r'\(\?\:', 1),  # Non-capturing groups
            (r'\{', 1),      # Quantifiers
            (r'\+', 1),      # Plus quantifier
            (r'\*', 1),      # Star quantifier
            (r'\?', 1),      # Question mark
        ]
        
        for construct, score in complex_constructs:
            complexity_score += len(re.findall(construct, pattern)) * score
        
        # Determine complexity level
        if complexity_score == 0:
            return "simple"
        elif complexity_score <= 3:
            return "moderate"
        elif complexity_score <= 7:
            return "complex"
        else:
            return "very_complex"
    
    def _get_pattern_suggestions(self, pattern: str, matches: List[Dict], stats: Dict) -> List[str]:
        """Get pattern optimization suggestions"""
        suggestions = []
        
        # Performance suggestions
        if stats.get('execution_time', 0) > 1.0:
            suggestions.append("Pattern is slow. Consider using more specific anchors or character classes.")
        
        if stats.get('total_matches', 0) > 1000:
            suggestions.append("Large number of matches. Consider adding anchors (^) ($) for better precision.")
        
        # Pattern structure suggestions
        if not pattern.startswith('^') and not pattern.endswith('$'):
            suggestions.append("Consider adding anchors (^) ($) for exact matching.")
        
        if '.*' in pattern:
            suggestions.append("Greedy wildcards (.*) can be slow. Consider using lazy quantifiers (.*?) or specific character classes.")
        
        if '\\d' in pattern and pattern.count('\\d') > 3:
            suggestions.append("Multiple \\d patterns. Consider using [0-9] or digit character class for better performance.")
        
        # Flag suggestions
        if 'i' not in pattern.lower() and stats.get('total_matches', 0) == 0:
            suggestions.append("No matches found. Try case-insensitive flag (i) if case doesn't matter.")
        
        # Group suggestions
        if stats.get('has_groups', False) and not stats.get('has_named_groups', False):
            suggestions.append("Consider using named groups (?P<name>...) for better readability.")
        
        # Specific pattern suggestions
        if pattern.startswith('.*') and pattern.endswith('.*'):
            suggestions.append("Pattern starts and ends with .*. This is very broad and slow.")
        
        if '\\\\' in pattern:
            suggestions.append("Double backslashes detected. Ensure proper escaping.")
        
        return suggestions
    
    def _validate_pattern(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """Validate regex pattern"""
        try:
            re.compile(pattern)
            return True, None
        except re.error as e:
            return False, str(e)
    
    def _get_pattern_info(self, pattern: str) -> Dict[str, Any]:
        """Get detailed pattern information"""
        info = {
            'length': len(pattern),
            'has_anchors': {
                'start': pattern.startswith('^'),
                'end': pattern.endswith('$')
            },
            'has_quantifiers': bool(re.search(r'[*+?{}]', pattern)),
            'has_groups': bool(re.search(r'\(', pattern)),
            'has_character_classes': bool(re.search(r'\[', pattern)),
            'has_escape_sequences': bool(re.search(r'\\', pattern)),
            'has_alternation': bool(re.search(r'\|', pattern))
        }
        
        # Count specific elements
        info.update({
            'group_count': len(re.findall(r'\(', pattern)),
            'quantifier_count': len(re.findall(r'[*+?{}]', pattern)),
            'character_class_count': len(re.findall(r'\[', pattern)),
            'escape_sequence_count': len(re.findall(r'\\.', pattern))
        })
        
        return info
