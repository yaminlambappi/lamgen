"""
Quality Assurance - Complete Implementation of Quality Assurance Framework

Provides production-ready quality assurance capabilities including code review,
security testing, compliance checking, and quality metrics for the LamGen tools ecosystem.
"""

import re
import ast
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus


class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


class SecurityLevel(Enum):
    """Security assessment levels"""
    SECURE = "secure"
    MODERATELY_SECURE = "moderately_secure"
    VULNERABLE = "vulnerable"
    HIGH_RISK = "high_risk"


class ComplianceLevel(Enum):
    """Compliance assessment levels"""
    FULLY_COMPLIANT = "fully_compliant"
    MOSTLY_COMPLIANT = "mostly_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"


@dataclass
class QualityMetric:
    """Quality metric data point"""
    name: str
    value: float
    threshold: float
    level: QualityLevel
    description: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SecurityVulnerability:
    """Security vulnerability finding"""
    severity: str
    type: str
    description: str
    file_path: str
    line_number: int
    recommendation: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceIssue:
    """Compliance issue finding"""
    standard: str
    requirement: str
    status: ComplianceLevel
    description: str
    remediation: str
    timestamp: datetime = field(default_factory=datetime.now)


class CodeReviewer:
    """Production-ready code reviewer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.review_config = self._default_review_config()
        self.quality_metrics: List[QualityMetric] = []
        self.code_patterns = self._default_code_patterns()
    
    def _default_review_config(self) -> Dict[str, Any]:
        """Default code review configuration"""
        return {
            'max_line_length': 100,
            'max_function_length': 50,
            'max_class_length': 300,
            'max_cyclomatic_complexity': 10,
            'min_test_coverage': 80,
            'max_nesting_depth': 4,
            'require_docstrings': True,
            'check_naming_conventions': True
        }
    
    def _default_code_patterns(self) -> Dict[str, List[str]]:
        """Default code patterns to check"""
        return {
            'anti_patterns': [
                'print(',  # Debug prints
                'eval(',   # Eval usage
                'exec(',   # Exec usage
                'import *', # Wildcard imports
                'except:',  # Bare except
                'pass$',   # Pass statements
            ],
            'security_patterns': [
                'password',
                'secret',
                'token',
                'key',
                'credential',
                'auth'
            ],
            'performance_patterns': [
                '.append(',
                '.extend(',
                'for.*in.*range(',
                'while.*True',
                'list(',
                'dict('
            ]
        }
    
    def review_code(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Review code quality"""
        review_result = {
            'file_path': file_path,
            'overall_quality': QualityLevel.GOOD,
            'quality_score': 0,
            'metrics': {},
            'issues': [],
            'recommendations': [],
            'security_issues': [],
            'performance_issues': []
        }
        
        try:
            # Parse AST
            try:
                tree = ast.parse(file_content)
            except SyntaxError as e:
                review_result['issues'].append({
                    'type': 'syntax_error',
                    'message': f"Syntax error: {str(e)}",
                    'severity': 'critical'
                })
                return review_result
            
            # Analyze code metrics
            metrics = self._analyze_code_metrics(tree, file_content)
            review_result['metrics'] = metrics
            
            # Check code patterns
            pattern_issues = self._check_code_patterns(file_content)
            review_result['issues'].extend(pattern_issues)
            
            # Check naming conventions
            if self.review_config['check_naming_conventions']:
                naming_issues = self._check_naming_conventions(tree)
                review_result['issues'].extend(naming_issues)
            
            # Check security issues
            security_issues = self._check_security_issues(file_content)
            review_result['security_issues'] = security_issues
            
            # Check performance issues
            performance_issues = self._check_performance_issues(tree, file_content)
            review_result['performance_issues'] = performance_issues
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(metrics, review_result['issues'])
            review_result['quality_score'] = quality_score
            
            # Determine quality level
            review_result['overall_quality'] = self._determine_quality_level(quality_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(review_result)
            review_result['recommendations'] = recommendations
            
            # Store metrics
            for metric_name, metric_value in metrics.items():
                metric = QualityMetric(
                    name=metric_name,
                    value=metric_value,
                    threshold=self.review_config.get(f'max_{metric_name}', 0),
                    level=QualityLevel.GOOD,
                    description=f"Code metric: {metric_name}"
                )
                self.quality_metrics.append(metric)
            
        except Exception as e:
            self.logger.error(f"Error reviewing code {file_path}: {str(e)}")
            review_result['error'] = str(e)
        
        return review_result
    
    def _analyze_code_metrics(self, tree: ast.AST, file_content: str) -> Dict[str, float]:
        """Analyze code metrics"""
        metrics = {}
        
        # Line count
        lines = file_content.split('\n')
        metrics['line_length'] = len(lines)
        
        # Function metrics
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        metrics['function_count'] = len(functions)
        
        if functions:
            function_lengths = []
            complexities = []
            
            for func in functions:
                # Function length (lines)
                func_lines = func.end_lineno - func.lineno + 1 if hasattr(func, 'end_lineno') else 10
                function_lengths.append(func_lines)
                
                # Cyclomatic complexity (simplified)
                complexity = self._calculate_cyclomatic_complexity(func)
                complexities.append(complexity)
            
            metrics['avg_function_length'] = sum(function_lengths) / len(function_lengths)
            metrics['max_function_length'] = max(function_lengths)
            metrics['avg_complexity'] = sum(complexities) / len(complexities)
            metrics['max_complexity'] = max(complexities)
        
        # Class metrics
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        metrics['class_count'] = len(classes)
        
        # Import metrics
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        metrics['import_count'] = len(imports)
        
        # Comment density (simplified)
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        metrics['comment_density'] = (comment_lines / len(lines)) * 100 if lines else 0
        
        return metrics
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_code_patterns(self, file_content: str) -> List[Dict[str, Any]]:
        """Check for code patterns"""
        issues = []
        
        # Check anti-patterns
        for pattern in self.code_patterns['anti_patterns']:
            if re.search(pattern, file_content):
                issues.append({
                    'type': 'anti_pattern',
                    'message': f"Potentially problematic pattern detected: {pattern}",
                    'severity': 'medium',
                    'pattern': pattern
                })
        
        return issues
    
    def _check_naming_conventions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check naming conventions"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    issues.append({
                        'type': 'naming_convention',
                        'message': f"Function name '{node.name}' should follow snake_case convention",
                        'severity': 'low',
                        'line': node.lineno
                    })
            
            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    issues.append({
                        'type': 'naming_convention',
                        'message': f"Class name '{node.name}' should follow PascalCase convention",
                        'severity': 'low',
                        'line': node.lineno
                    })
        
        return issues
    
    def _check_security_issues(self, file_content: str) -> List[SecurityVulnerability]:
        """Check for security issues"""
        vulnerabilities = []
        
        # Check for hardcoded secrets
        for pattern in self.code_patterns['security_patterns']:
            matches = re.finditer(pattern + r'.*[:=]\s*[\'\"]([^\'\"]+)[\'\"]', file_content, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append(SecurityVulnerability(
                    severity='medium',
                    type='hardcoded_secret',
                    description=f"Potential hardcoded {pattern}: {match.group()[:50]}...",
                    file_path='',
                    line_number=file_content[:match.start()].count('\n') + 1,
                    recommendation="Use environment variables or secure configuration"
                ))
        
        # Check for dangerous functions
        dangerous_functions = ['eval', 'exec', 'compile']
        for func in dangerous_functions:
            if re.search(r'\b' + func + r'\s*\(', file_content):
                vulnerabilities.append(SecurityVulnerability(
                    severity='high',
                    type='dangerous_function',
                    description=f"Use of dangerous function: {func}",
                    file_path='',
                    line_number=0,
                    recommendation=f"Avoid using {func}, use safer alternatives"
                ))
        
        return vulnerabilities
    
    def _check_performance_issues(self, tree: ast.AST, file_content: str) -> List[Dict[str, Any]]:
        """Check for performance issues"""
        issues = []
        
        # Check for potential performance bottlenecks
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check for range(len(x)) pattern
                if (isinstance(node.iter, ast.Call) and
                    isinstance(node.iter.func, ast.Name) and
                    node.iter.func.id == 'range' and
                    len(node.iter.args) == 1 and
                    isinstance(node.iter.args[0], ast.Call) and
                    isinstance(node.iter.args[0].func, ast.Name) and
                    node.iter.args[0].func.id == 'len'):
                    issues.append({
                        'type': 'performance',
                        'message': "Consider using enumerate() instead of range(len())",
                        'severity': 'low',
                        'line': node.lineno
                    })
        
        return issues
    
    def _calculate_quality_score(self, metrics: Dict[str, Any], issues: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score"""
        score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            severity = issue.get('severity', 'medium')
            if severity == 'critical':
                score -= 20
            elif severity == 'high':
                score -= 10
            elif severity == 'medium':
                score -= 5
            elif severity == 'low':
                score -= 2
        
        # Deduct points for metric violations
        if metrics.get('max_function_length', 0) > self.review_config['max_function_length']:
            score -= 10
        
        if metrics.get('max_complexity', 0) > self.review_config['max_cyclomatic_complexity']:
            score -= 15
        
        if metrics.get('line_length', 0) > self.review_config['max_line_length'] * 10:  # Very long file
            score -= 5
        
        return max(0, score)
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level from score"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 70:
            return QualityLevel.ACCEPTABLE
        elif score >= 60:
            return QualityLevel.NEEDS_IMPROVEMENT
        else:
            return QualityLevel.POOR
    
    def _generate_recommendations(self, review_result: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Based on quality score
        score = review_result['quality_score']
        if score < 70:
            recommendations.append("Overall code quality needs improvement")
        
        # Based on metrics
        metrics = review_result['metrics']
        if metrics.get('max_function_length', 0) > 50:
            recommendations.append("Consider breaking down large functions")
        
        if metrics.get('max_complexity', 0) > 10:
            recommendations.append("Reduce cyclomatic complexity by simplifying logic")
        
        if metrics.get('comment_density', 0) < 10:
            recommendations.append("Add more comments and documentation")
        
        # Based on issues
        for issue in review_result['issues']:
            if issue['type'] == 'anti_pattern':
                recommendations.append(f"Address anti-pattern: {issue.get('pattern', 'unknown')}")
        
        # Based on security issues
        if review_result['security_issues']:
            recommendations.append("Address security vulnerabilities")
        
        # Based on performance issues
        if review_result['performance_issues']:
            recommendations.append("Optimize performance bottlenecks")
        
        return recommendations


class SecurityTester:
    """Production-ready security tester"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.security_config = self._default_security_config()
        self.vulnerabilities: List[SecurityVulnerability] = []
        self.security_checks = self._default_security_checks()
    
    def _default_security_config(self) -> Dict[str, Any]:
        """Default security configuration"""
        return {
            'check_sql_injection': True,
            'check_xss': True,
            'check_csrf': True,
            'check_authentication': True,
            'check_authorization': True,
            'check_data_validation': True,
            'check_error_handling': True,
            'check_logging': True
        }
    
    def _default_security_checks(self) -> Dict[str, List[str]]:
        """Default security check patterns"""
        return {
            'sql_injection': [
                r'execute\s*\(',
                r'cursor\.execute',
                r'SELECT.*FROM.*WHERE',
                r'INSERT.*INTO',
                r'UPDATE.*SET',
                r'DELETE.*FROM'
            ],
            'xss': [
                r'innerHTML',
                r'outerHTML',
                r'document\.write',
                r'eval\s*\(',
                r'setTimeout\s*\('
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'file://',
                r'open\s*\(',
                r'read\s*\('
            ],
            'command_injection': [
                r'os\.system',
                r'subprocess\.call',
                r'exec\s*\(',
                r'eval\s*\(',
                r'popen\s*\('
            ]
        ]
    
    def test_security(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Test code for security vulnerabilities"""
        security_result = {
            'file_path': file_path,
            'security_level': SecurityLevel.SECURE,
            'vulnerabilities': [],
            'risk_score': 0,
            'recommendations': [],
            'compliance_status': {}
        }
        
        try:
            vulnerabilities = []
            
            # Check for various security issues
            if self.security_config['check_sql_injection']:
                sql_vulns = self._check_sql_injection(file_content)
                vulnerabilities.extend(sql_vulns)
            
            if self.security_config['check_xss']:
                xss_vulns = self._check_xss(file_content)
                vulnerabilities.extend(xss_vulns)
            
            if self.security_config['check_authentication']:
                auth_vulns = self._check_authentication(file_content)
                vulnerabilities.extend(auth_vulns)
            
            if self.security_config['check_data_validation']:
                validation_vulns = self._check_data_validation(file_content)
                vulnerabilities.extend(validation_vulns)
            
            # Check for command injection
            cmd_vulns = self._check_command_injection(file_content)
            vulnerabilities.extend(cmd_vulns)
            
            # Check for path traversal
            path_vulns = self._check_path_traversal(file_content)
            vulnerabilities.extend(path_vulns)
            
            security_result['vulnerabilities'] = vulnerabilities
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(vulnerabilities)
            security_result['risk_score'] = risk_score
            
            # Determine security level
            security_result['security_level'] = self._determine_security_level(risk_score)
            
            # Generate recommendations
            recommendations = self._generate_security_recommendations(vulnerabilities)
            security_result['recommendations'] = recommendations
            
            # Store vulnerabilities
            self.vulnerabilities.extend(vulnerabilities)
            
        except Exception as e:
            self.logger.error(f"Error testing security for {file_path}: {str(e)}")
            security_result['error'] = str(e)
        
        return security_result
    
    def _check_sql_injection(self, file_content: str) -> List[SecurityVulnerability]:
        """Check for SQL injection vulnerabilities"""
        vulnerabilities = []
        
        for pattern in self.security_checks['sql_injection']:
            matches = re.finditer(pattern, file_content, re.IGNORECASE)
            for match in matches:
                # Check if it's using parameterized queries (simplified check)
                line_start = file_content.rfind('\n', 0, match.start())
                line_end = file_content.find('\n', match.start())
                line = file_content[line_start+1:line_end]
                
                if not any(safe_pattern in line.lower() for safe_pattern in ['parameter', 'bind', '?', '%s']):
                    vulnerabilities.append(SecurityVulnerability(
                        severity='high',
                        type='sql_injection',
                        description=f"Potential SQL injection: {match.group()[:50]}...",
                        file_path='',
                        line_number=file_content[:match.start()].count('\n') + 1,
                        recommendation="Use parameterized queries or prepared statements"
                    ))
        
        return vulnerabilities
    
    def _check_xss(self, file_content: str) -> List[SecurityVulnerability]:
        """Check for XSS vulnerabilities"""
        vulnerabilities = []
        
        for pattern in self.security_checks['xss']:
            matches = re.finditer(pattern, file_content, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append(SecurityVulnerability(
                    severity='medium',
                    type='xss',
                    description=f"Potential XSS vulnerability: {match.group()[:50]}...",
                    file_path='',
                    line_number=file_content[:match.start()].count('\n') + 1,
                    recommendation="Sanitize user input and use safe HTML rendering"
                ))
        
        return vulnerabilities
    
    def _check_authentication(self, file_content: str) -> List[SecurityVulnerability]:
        """Check for authentication issues"""
        vulnerabilities = []
        
        # Check for hardcoded credentials
        credential_patterns = [
            r'password\s*=\s*[\'\"]([^\'\"]+)[\'\"]',
            r'secret\s*=\s*[\'\"]([^\'\"]+)[\'\"]',
            r'key\s*=\s*[\'\"]([^\'\"]+)[\'\"]',
            r'token\s*=\s*[\'\"]([^\'\"]+)[\'\"]'
        ]
        
        for pattern in credential_patterns:
            matches = re.finditer(pattern, file_content, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append(SecurityVulnerability(
                    severity='high',
                    type='hardcoded_credentials',
                    description=f"Hardcoded credential found: {match.group(1)[:10]}...",
                    file_path='',
                    line_number=file_content[:match.start()].count('\n') + 1,
                    recommendation="Use environment variables or secure configuration"
                ))
        
        return vulnerabilities
    
    def _check_data_validation(self, file_content: str) -> List[SecurityVulnerability]:
        """Check for data validation issues"""
        vulnerabilities = []
        
        # Check for direct use of user input without validation
        input_patterns = [
            r'request\.form\[',
            r'request\.args\[',
            r'request\.get\(',
            r'input\s*\(',
            r'raw_input\s*\('
        ]
        
        for pattern in input_patterns:
            matches = re.finditer(pattern, file_content, re.IGNORECASE)
            for match in matches:
                line_start = file_content.rfind('\n', 0, match.start())
                line_end = file_content.find('\n', match.start())
                line = file_content[line_start+1:line_end]
                
                # Check if validation is present (simplified)
                if not any(validation in line.lower() for validation in ['validate', 'sanitize', 'clean', 'escape']):
                    vulnerabilities.append(SecurityVulnerability(
                        severity='medium',
                        type='insufficient_validation',
                        description=f"User input without validation: {match.group()[:50]}...",
                        file_path='',
                        line_number=file_content[:match.start()].count('\n') + 1,
                        recommendation="Validate and sanitize all user input"
                    ))
        
        return vulnerabilities
    
    def _check_command_injection(self, file_content: str) -> List[SecurityVulnerability]:
        """Check for command injection vulnerabilities"""
        vulnerabilities = []
        
        for pattern in self.security_checks['command_injection']:
            matches = re.finditer(pattern, file_content, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append(SecurityVulnerability(
                    severity='high',
                    type='command_injection',
                    description=f"Potential command injection: {match.group()[:50]}...",
                    file_path='',
                    line_number=file_content[:match.start()].count('\n') + 1,
                    recommendation="Avoid executing system commands with user input"
                ))
        
        return vulnerabilities
    
    def _check_path_traversal(self, file_content: str) -> List[SecurityVulnerability]:
        """Check for path traversal vulnerabilities"""
        vulnerabilities = []
        
        for pattern in self.security_checks['path_traversal']:
            matches = re.finditer(pattern, file_content, re.IGNORECASE)
            for match in matches:
                vulnerabilities.append(SecurityVulnerability(
                    severity='medium',
                    type='path_traversal',
                    description=f"Potential path traversal: {match.group()[:50]}...",
                    file_path='',
                    line_number=file_content[:match.start()].count('\n') + 1,
                    recommendation="Validate file paths and use safe file operations"
                ))
        
        return vulnerabilities
    
    def _calculate_risk_score(self, vulnerabilities: List[SecurityVulnerability]) -> float:
        """Calculate security risk score"""
        score = 0
        
        for vuln in vulnerabilities:
            if vuln.severity == 'critical':
                score += 25
            elif vuln.severity == 'high':
                score += 15
            elif vuln.severity == 'medium':
                score += 10
            elif vuln.severity == 'low':
                score += 5
        
        return min(100, score)
    
    def _determine_security_level(self, risk_score: float) -> SecurityLevel:
        """Determine security level from risk score"""
        if risk_score >= 50:
            return SecurityLevel.HIGH_RISK
        elif risk_score >= 25:
            return SecurityLevel.VULNERABLE
        elif risk_score >= 10:
            return SecurityLevel.MODERATELY_SECURE
        else:
            return SecurityLevel.SECURE
    
    def _generate_security_recommendations(self, vulnerabilities: List[SecurityVulnerability]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if not vulnerabilities:
            recommendations.append("No security vulnerabilities detected - continue following security best practices")
            return recommendations
        
        # Group by type
        vuln_types = {}
        for vuln in vulnerabilities:
            if vuln.type not in vuln_types:
                vuln_types[vuln.type] = []
            vuln_types[vuln.type].append(vuln)
        
        # Generate recommendations for each type
        for vuln_type, vulns in vuln_types.items():
            if vuln_type == 'sql_injection':
                recommendations.append("Implement parameterized queries and input validation")
            elif vuln_type == 'xss':
                recommendations.append("Sanitize user input and use safe HTML rendering")
            elif vuln_type == 'hardcoded_credentials':
                recommendations.append("Move credentials to environment variables or secure configuration")
            elif vuln_type == 'command_injection':
                recommendations.append("Avoid executing system commands with user input")
            elif vuln_type == 'path_traversal':
                recommendations.append("Validate file paths and use safe file operations")
            elif vuln_type == 'insufficient_validation':
                recommendations.append("Implement comprehensive input validation and sanitization")
        
        # General recommendations
        if len(vulnerabilities) > 5:
            recommendations.append("Consider conducting a comprehensive security audit")
        
        return recommendations


class ComplianceChecker:
    """Production-ready compliance checker"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.compliance_config = self._default_compliance_config()
        self.compliance_standards = self._default_compliance_standards()
        self.compliance_issues: List[ComplianceIssue] = []
    
    def _default_compliance_config(self) -> Dict[str, Any]:
        """Default compliance configuration"""
        return {
            'check_gdpr': True,
            'check_ccpa': True,
            'check_pci_dss': False,
            'check_hipaa': False,
            'check_accessibility': True,
            'check_data_protection': True,
            'check_privacy_policy': True
        }
    
    def _default_compliance_standards(self) -> Dict[str, Dict[str, Any]]:
        """Default compliance standards"""
        return {
            'gdpr': {
                'name': 'General Data Protection Regulation',
                'requirements': [
                    'data_minimization',
                    'consent_management',
                    'data_subject_rights',
                    'data_breach_notification',
                    'privacy_by_design'
                ]
            },
            'accessibility': {
                'name': 'Web Content Accessibility Guidelines',
                'requirements': [
                    'alt_text_for_images',
                    'keyboard_navigation',
                    'color_contrast',
                    'heading_structure',
                    'form_labels'
                ]
            },
            'data_protection': {
                'name': 'Data Protection Best Practices',
                'requirements': [
                    'encryption_at_rest',
                    'encryption_in_transit',
                    'access_controls',
                    'audit_logging',
                    'data_retention'
                ]
            }
        }
    
    def check_compliance(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Check compliance with various standards"""
        compliance_result = {
            'file_path': file_path,
            'overall_compliance': ComplianceLevel.FULLY_COMPLIANT,
            'standards_checked': [],
            'compliance_score': 0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            issues = []
            standards_checked = []
            
            # Check GDPR compliance
            if self.compliance_config['check_gdpr']:
                gdpr_issues = self._check_gdpr_compliance(file_content)
                issues.extend(gdpr_issues)
                standards_checked.append('gdpr')
            
            # Check accessibility compliance
            if self.compliance_config['check_accessibility']:
                accessibility_issues = self._check_accessibility_compliance(file_content)
                issues.extend(accessibility_issues)
                standards_checked.append('accessibility')
            
            # Check data protection compliance
            if self.compliance_config['check_data_protection']:
                data_protection_issues = self._check_data_protection_compliance(file_content)
                issues.extend(data_protection_issues)
                standards_checked.append('data_protection')
            
            compliance_result['standards_checked'] = standards_checked
            compliance_result['issues'] = issues
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(issues, standards_checked)
            compliance_result['compliance_score'] = compliance_score
            
            # Determine overall compliance level
            compliance_result['overall_compliance'] = self._determine_compliance_level(compliance_score)
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(issues)
            compliance_result['recommendations'] = recommendations
            
            # Store issues
            self.compliance_issues.extend(issues)
            
        except Exception as e:
            self.logger.error(f"Error checking compliance for {file_path}: {str(e)}")
            compliance_result['error'] = str(e)
        
        return compliance_result
    
    def _check_gdpr_compliance(self, file_content: str) -> List[ComplianceIssue]:
        """Check GDPR compliance"""
        issues = []
        
        # Check for data minimization
        if re.search(r'collect.*all.*data', file_content, re.IGNORECASE):
            issues.append(ComplianceIssue(
                standard='gdpr',
                requirement='data_minimization',
                status=ComplianceLevel.PARTIALLY_COMPLIANT,
                description="Potential violation of data minimization principle",
                remediation="Implement data minimization practices"
            ))
        
        # Check for consent management
        if 'consent' not in file_content.lower():
            issues.append(ComplianceIssue(
                standard='gdpr',
                requirement='consent_management',
                status=ComplianceLevel.PARTIALLY_COMPLIANT,
                description="No consent management mechanism found",
                remediation="Implement user consent management"
            ))
        
        return issues
    
    def _check_accessibility_compliance(self, file_content: str) -> List[ComplianceIssue]:
        """Check accessibility compliance"""
        issues = []
        
        # Check for alt text
        img_tags = re.findall(r'<img[^>]*>', file_content, re.IGNORECASE)
        for img in img_tags:
            if 'alt=' not in img.lower():
                issues.append(ComplianceIssue(
                    standard='accessibility',
                    requirement='alt_text_for_images',
                    status=ComplianceLevel.PARTIALLY_COMPLIANT,
                    description="Image missing alt text",
                    remediation="Add descriptive alt text to all images"
                ))
        
        # Check for heading structure
        if not re.search(r'<h[1-6]>', file_content, re.IGNORECASE):
            issues.append(ComplianceIssue(
                standard='accessibility',
                requirement='heading_structure',
                status=ComplianceLevel.PARTIALLY_COMPLIANT,
                description="No heading structure found",
                remediation="Implement proper heading hierarchy"
            ))
        
        return issues
    
    def _check_data_protection_compliance(self, file_content: str) -> List[ComplianceIssue]:
        """Check data protection compliance"""
        issues = []
        
        # Check for encryption
        if 'encrypt' not in file_content.lower():
            issues.append(ComplianceIssue(
                standard='data_protection',
                requirement='encryption_at_rest',
                status=ComplianceLevel.PARTIALLY_COMPLIANT,
                description="No encryption mechanism found",
                remediation="Implement data encryption"
            ))
        
        # Check for access controls
        if 'auth' not in file_content.lower() and 'permission' not in file_content.lower():
            issues.append(ComplianceIssue(
                standard='data_protection',
                requirement='access_controls',
                status=ComplianceLevel.PARTIALLY_COMPLIANT,
                description="No access control mechanism found",
                remediation="Implement proper access controls"
            ))
        
        return issues
    
    def _calculate_compliance_score(self, issues: List[ComplianceIssue], standards_checked: List[str]) -> float:
        """Calculate compliance score"""
        if not standards_checked:
            return 100.0
        
        # Each standard starts with 100 points
        total_points = len(standards_checked) * 100
        deductions = 0
        
        for issue in issues:
            if issue.status == ComplianceLevel.NON_COMPLIANT:
                deductions += 50
            elif issue.status == ComplianceLevel.PARTIALLY_COMPLIANT:
                deductions += 25
            elif issue.status == ComplianceLevel.MOSTLY_COMPLIANT:
                deductions += 10
        
        score = max(0, (total_points - deductions) / len(standards_checked))
        return score
    
    def _determine_compliance_level(self, score: float) -> ComplianceLevel:
        """Determine compliance level from score"""
        if score >= 95:
            return ComplianceLevel.FULLY_COMPLIANT
        elif score >= 80:
            return ComplianceLevel.MOSTLY_COMPLIANT
        elif score >= 60:
            return ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            return ComplianceLevel.NON_COMPLIANT
    
    def _generate_compliance_recommendations(self, issues: List[ComplianceIssue]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if not issues:
            recommendations.append("Excellent compliance - maintain current practices")
            return recommendations
        
        # Group by standard
        standard_issues = {}
        for issue in issues:
            if issue.standard not in standard_issues:
                standard_issues[issue.standard] = []
            standard_issues[issue.standard].append(issue)
        
        # Generate recommendations for each standard
        for standard, std_issues in standard_issues.items():
            standard_name = self.compliance_standards.get(standard, {}).get('name', standard)
            recommendations.append(f"Address {standard_name} compliance issues")
            
            for issue in std_issues[:3]:  # Top 3 issues per standard
                recommendations.append(f"- {issue.remediation}")
        
        return recommendations


class QualityAssurance:
    """Production-ready quality assurance orchestrator"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.code_reviewer = CodeReviewer()
        self.security_tester = SecurityTester()
        self.compliance_checker = ComplianceChecker()
        self.qa_results: List[Dict[str, Any]] = []
    
    def run_quality_assurance(self, file_path: str, file_content: str) -> Dict[str, Any]:
        """Run comprehensive quality assurance"""
        qa_result = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'overall_quality': 'good',
            'quality_score': 0,
            'code_review': {},
            'security_test': {},
            'compliance_check': {},
            'summary': {
                'total_issues': 0,
                'critical_issues': 0,
                'high_issues': 0,
                'medium_issues': 0,
                'low_issues': 0
            },
            'recommendations': [],
            'action_items': []
        }
        
        try:
            # Run code review
            code_review = self.code_reviewer.review_code(file_path, file_content)
            qa_result['code_review'] = code_review
            
            # Run security test
            security_test = self.security_tester.test_security(file_path, file_content)
            qa_result['security_test'] = security_test
            
            # Run compliance check
            compliance_check = self.compliance_checker.check_compliance(file_path, file_content)
            qa_result['compliance_check'] = compliance_check
            
            # Calculate overall quality score
            overall_score = self._calculate_overall_quality_score(
                code_review, security_test, compliance_check
            )
            qa_result['quality_score'] = overall_score
            
            # Determine overall quality
            qa_result['overall_quality'] = self._determine_overall_quality(overall_score)
            
            # Generate summary
            qa_result['summary'] = self._generate_qa_summary(code_review, security_test, compliance_check)
            
            # Generate recommendations
            recommendations = self._generate_qa_recommendations(qa_result)
            qa_result['recommendations'] = recommendations
            
            # Generate action items
            action_items = self._generate_action_items(qa_result)
            qa_result['action_items'] = action_items
            
            # Store result
            self.qa_results.append(qa_result)
            
        except Exception as e:
            self.logger.error(f"Error in quality assurance for {file_path}: {str(e)}")
            qa_result['error'] = str(e)
        
        return qa_result
    
    def _calculate_overall_quality_score(self, code_review: Dict[str, Any], 
                                       security_test: Dict[str, Any], 
                                       compliance_check: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        # Weight different aspects
        weights = {
            'code_quality': 0.4,
            'security': 0.3,
            'compliance': 0.3
        }
        
        # Get scores from each component
        code_score = code_review.get('quality_score', 0)
        security_score = 100 - security_test.get('risk_score', 0)  # Invert risk score
        compliance_score = compliance_check.get('compliance_score', 0)
        
        # Calculate weighted average
        overall_score = (
            code_score * weights['code_quality'] +
            security_score * weights['security'] +
            compliance_score * weights['compliance']
        )
        
        return overall_score
    
    def _determine_overall_quality(self, score: float) -> str:
        """Determine overall quality level"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'acceptable'
        elif score >= 60:
            return 'needs_improvement'
        else:
            return 'poor'
    
    def _generate_qa_summary(self, code_review: Dict[str, Any], 
                           security_test: Dict[str, Any], 
                           compliance_check: Dict[str, Any]) -> Dict[str, Any]:
        """Generate QA summary"""
        summary = {
            'total_issues': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0
        }
        
        # Count code review issues
        for issue in code_review.get('issues', []):
            severity = issue.get('severity', 'medium')
            summary['total_issues'] += 1
            if severity == 'critical':
                summary['critical_issues'] += 1
            elif severity == 'high':
                summary['high_issues'] += 1
            elif severity == 'medium':
                summary['medium_issues'] += 1
            else:
                summary['low_issues'] += 1
        
        # Count security vulnerabilities
        for vuln in security_test.get('vulnerabilities', []):
            severity = vuln.severity
            summary['total_issues'] += 1
            if severity == 'critical':
                summary['critical_issues'] += 1
            elif severity == 'high':
                summary['high_issues'] += 1
            elif severity == 'medium':
                summary['medium_issues'] += 1
            else:
                summary['low_issues'] += 1
        
        # Count compliance issues
        for issue in compliance_check.get('issues', []):
            status = issue.status
            summary['total_issues'] += 1
            if status == ComplianceLevel.NON_COMPLIANT:
                summary['critical_issues'] += 1
            elif status == ComplianceLevel.PARTIALLY_COMPLIANT:
                summary['high_issues'] += 1
            elif status == ComplianceLevel.MOSTLY_COMPLIANT:
                summary['medium_issues'] += 1
            else:
                summary['low_issues'] += 1
        
        return summary
    
    def _generate_qa_recommendations(self, qa_result: Dict[str, Any]) -> List[str]:
        """Generate QA recommendations"""
        recommendations = []
        
        # Code quality recommendations
        code_recommendations = qa_result['code_review'].get('recommendations', [])
        recommendations.extend(code_recommendations)
        
        # Security recommendations
        security_recommendations = qa_result['security_test'].get('recommendations', [])
        recommendations.extend(security_recommendations)
        
        # Compliance recommendations
        compliance_recommendations = qa_result['compliance_check'].get('recommendations', [])
        recommendations.extend(compliance_recommendations)
        
        # Overall recommendations
        summary = qa_result['summary']
        if summary['critical_issues'] > 0:
            recommendations.insert(0, "URGENT: Address critical security and quality issues immediately")
        
        if summary['high_issues'] > 5:
            recommendations.insert(0, "High priority: Address multiple high-severity issues")
        
        return recommendations
    
    def _generate_action_items(self, qa_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable items"""
        action_items = []
        
        summary = qa_result['summary']
        
        # Critical issues
        if summary['critical_issues'] > 0:
            action_items.append({
                'priority': 'critical',
                'action': 'Fix critical vulnerabilities and issues',
                'estimated_effort': 'high',
                'deadline': 'immediate'
            })
        
        # High issues
        if summary['high_issues'] > 0:
            action_items.append({
                'priority': 'high',
                'action': f'Address {summary["high_issues"]} high-severity issues',
                'estimated_effort': 'medium',
                'deadline': '1 week'
            })
        
        # Medium issues
        if summary['medium_issues'] > 3:
            action_items.append({
                'priority': 'medium',
                'action': f'Resolve {summary["medium_issues"]} medium-severity issues',
                'estimated_effort': 'medium',
                'deadline': '2 weeks'
            })
        
        # Quality improvement
        if qa_result['quality_score'] < 80:
            action_items.append({
                'priority': 'medium',
                'action': 'Improve overall code quality',
                'estimated_effort': 'medium',
                'deadline': '3 weeks'
            })
        
        return action_items
    
    def get_qa_dashboard(self) -> Dict[str, Any]:
        """Get QA dashboard summary"""
        dashboard = {
            'total_files_reviewed': len(self.qa_results),
            'average_quality_score': 0,
            'quality_distribution': {},
            'top_issues': [],
            'trends': {}
        }
        
        if not self.qa_results:
            return dashboard
        
        # Calculate average quality score
        total_score = sum(result['quality_score'] for result in self.qa_results)
        dashboard['average_quality_score'] = total_score / len(self.qa_results)
        
        # Quality distribution
        quality_levels = [result['overall_quality'] for result in self.qa_results]
        from collections import Counter
        quality_counts = Counter(quality_levels)
        dashboard['quality_distribution'] = dict(quality_counts)
        
        # Top issues
        all_issues = []
        for result in self.qa_results:
            all_issues.extend(result['code_review'].get('issues', []))
            all_issues.extend(result['security_test'].get('vulnerabilities', []))
            all_issues.extend(result['compliance_check'].get('issues', []))
        
        # Group by type
        issue_types = {}
        for issue in all_issues:
            issue_type = getattr(issue, 'type', 'unknown')
            if issue_type not in issue_types:
                issue_types[issue_type] = 0
            issue_types[issue_type] += 1
        
        dashboard['top_issues'] = sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return dashboard


# Global instances
_code_reviewer = None
_security_tester = None
_compliance_checker = None
_quality_assurance = None


def get_code_reviewer() -> CodeReviewer:
    """Get global code reviewer instance"""
    global _code_reviewer
    if _code_reviewer is None:
        _code_reviewer = CodeReviewer()
    return _code_reviewer


def get_security_tester() -> SecurityTester:
    """Get global security tester instance"""
    global _security_tester
    if _security_tester is None:
        _security_tester = SecurityTester()
    return _security_tester


def get_compliance_checker() -> ComplianceChecker:
    """Get global compliance checker instance"""
    global _compliance_checker
    if _compliance_checker is None:
        _compliance_checker = ComplianceChecker()
    return _compliance_checker


def get_quality_assurance() -> QualityAssurance:
    """Get global quality assurance instance"""
    global _quality_assurance
    if _quality_assurance is None:
        _quality_assurance = QualityAssurance()
    return _quality_assurance
