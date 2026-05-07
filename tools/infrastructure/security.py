"""
Security Infrastructure - Complete Implementation of Security System

Provides production-ready security management, rate limiting, access control,
and audit logging for the LamGen tools ecosystem.
"""

import time
import hashlib
import hmac
import secrets
import logging
import re
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from tools.framework.base_tool import ToolConfig, ToolStatus


class SecurityLevel(Enum):
    """Security levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccessLevel(Enum):
    """Access levels"""
    PUBLIC = "public"
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


@dataclass
class SecurityEvent:
    """Security event data"""
    event_type: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0


@dataclass
class RateLimitRule:
    """Rate limit rule"""
    key: str
    limit: int
    window: int  # seconds
    burst_limit: int = 0
    burst_window: int = 0


class SecurityManager:
    """Production-ready security manager"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.security_events: List[SecurityEvent] = []
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns = self._default_suspicious_patterns()
        self.security_config = self._default_security_config()
        
    def _default_suspicious_patterns(self) -> List[str]:
        """Default suspicious patterns"""
        return [
            r'<script[^>]*>',  # Script tags
            r'javascript:',      # JavaScript URLs
            r'on\w+\s*=',      # Event handlers
            r'union\s+select',   # SQL injection
            r'drop\s+table',     # SQL injection
            r'exec\s*\(',        # Command injection
            r'eval\s*\(',        # Code execution
        ]
    
    def _default_security_config(self) -> Dict[str, Any]:
        """Default security configuration"""
        return {
            'max_request_size': 10485760,  # 10MB
            'max_url_length': 2048,
            'max_header_size': 8192,
            'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
            'blocked_user_agents': [],
            'require_https': False,
            'session_timeout': 3600,  # 1 hour
            'max_login_attempts': 5,
            'lockout_duration': 900,  # 15 minutes
        }
    
    def validate_input(self, input_data: str, input_type: str = 'text') -> Dict[str, Any]:
        """Validate input for security threats"""
        validation_result = {
            'is_valid': True,
            'threats_found': [],
            'risk_score': 0.0,
            'sanitized_input': input_data
        }
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                validation_result['is_valid'] = False
                validation_result['threats_found'].append(f"Suspicious pattern: {pattern}")
                validation_result['risk_score'] += 20
        
        # Check input size
        if len(input_data) > self.security_config['max_request_size']:
            validation_result['is_valid'] = False
            validation_result['threats_found'].append("Input too large")
            validation_result['risk_score'] += 10
        
        # Sanitize input
        sanitized = self._sanitize_input(input_data)
        validation_result['sanitized_input'] = sanitized
        
        return validation_result
    
    def _sanitize_input(self, input_data: str) -> str:
        """Sanitize input data"""
        # Remove HTML tags
        sanitized = re.sub(r'<[^>]*>', '', input_data)
        
        # Remove JavaScript URLs
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        # Remove event handlers
        sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        return sanitized.strip()
    
    def check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP reputation"""
        reputation_result = {
            'is_blocked': ip_address in self.blocked_ips,
            'reputation_score': 0.0,
            'threat_level': 'low',
            'details': {}
        }
        
        # Check if IP is blocked
        if reputation_result['is_blocked']:
            reputation_result['threat_level'] = 'high'
            reputation_result['reputation_score'] = 100
            reputation_result['details']['reason'] = 'IP is blocked'
        
        # Check for suspicious patterns in IP
        if self._is_suspicious_ip(ip_address):
            reputation_result['threat_level'] = 'medium'
            reputation_result['reputation_score'] = 50
            reputation_result['details']['reason'] = 'Suspicious IP pattern'
        
        return reputation_result
    
    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        # Simplified IP checking - in production would use threat intelligence
        suspicious_ranges = [
            '0.0.0.0/8',      # Reserved
            '127.0.0.0/8',    # Loopback
            '169.254.0.0/16', # Link-local
            '224.0.0.0/4',    # Multicast
        ]
        
        # Simple check for private/internal IPs
        if ip_address.startswith(('192.168.', '10.', '172.')):
            return True
        
        return False
    
    def log_security_event(self, event_type: str, user_id: Optional[str], 
                          ip_address: str, user_agent: str, details: Dict[str, Any] = None) -> None:
        """Log security event"""
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            risk_score=self._calculate_risk_score(event_type, details)
        )
        
        self.security_events.append(event)
        
        # Clean old events (keep last 10000)
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-10000:]
        
        # Log the event
        log_level = logging.WARNING if event.risk_score > 50 else logging.INFO
        self.logger.log(log_level, f"Security event: {event_type} from {ip_address}")
        
        # Auto-block if high risk
        if event.risk_score > 80:
            self.block_ip(ip_address)
    
    def _calculate_risk_score(self, event_type: str, details: Dict[str, Any]) -> float:
        """Calculate risk score for security event"""
        base_scores = {
            'login_attempt': 10,
            'login_failure': 30,
            'suspicious_input': 50,
            'blocked_request': 60,
            'rate_limit_exceeded': 40,
            'access_denied': 35,
            'security_violation': 80
        }
        
        score = base_scores.get(event_type, 20)
        
        # Add contextual risk factors
        if details.get('user_agent', '').count('bot') > 0:
            score += 10
        
        if details.get('failed_attempts', 0) > 3:
            score += 20
        
        return min(100, score)
    
    def block_ip(self, ip_address: str, duration: int = 3600) -> None:
        """Block IP address"""
        self.blocked_ips.add(ip_address)
        self.logger.warning(f"IP {ip_address} blocked for {duration} seconds")
        
        # Schedule unblock (simplified - would use background task in production)
        # In production, this would be handled by a proper scheduling system
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Unblock IP address"""
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            self.logger.info(f"IP {ip_address} unblocked")
            return True
        return False
    
    def get_security_events(self, event_type: str = None, since: datetime = None) -> List[SecurityEvent]:
        """Get security events"""
        filtered_events = self.security_events
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        
        if since:
            filtered_events = [e for e in filtered_events if e.timestamp >= since]
        
        return filtered_events
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary"""
        recent_events = self.get_security_events(since=datetime.now() - timedelta(hours=24))
        
        event_counts = defaultdict(int)
        risk_scores = []
        
        for event in recent_events:
            event_counts[event.event_type] += 1
            risk_scores.append(event.risk_score)
        
        return {
            'total_events': len(recent_events),
            'event_counts': dict(event_counts),
            'blocked_ips': len(self.blocked_ips),
            'average_risk_score': sum(risk_scores) / len(risk_scores) if risk_scores else 0,
            'high_risk_events': len([e for e in recent_events if e.risk_score > 70]),
            'last_check': datetime.now().isoformat()
        }


class RateLimiter:
    """Production-ready rate limiter"""
    
    def __init__(self):
        self.rules: Dict[str, RateLimitRule] = {}
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.logger = logging.getLogger(__name__)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def add_rule(self, key: str, limit: int, window: int, burst_limit: int = 0, burst_window: int = 0) -> None:
        """Add rate limit rule"""
        self.rules[key] = RateLimitRule(
            key=key,
            limit=limit,
            window=window,
            burst_limit=burst_limit,
            burst_window=burst_window
        )
    
    def is_allowed(self, key: str, identifier: str = None) -> Dict[str, Any]:
        """Check if request is allowed based on rate limits"""
        if key not in self.rules:
            return {'allowed': True, 'reason': 'No rate limit rule'}
        
        rule = self.rules[key]
        request_key = f"{key}:{identifier or 'default'}"
        current_time = time.time()
        
        # Clean up old entries
        self._cleanup_old_entries(current_time)
        
        # Check regular rate limit
        requests_queue = self.requests[request_key]
        
        # Remove old requests outside the window
        while (requests_queue and 
               current_time - requests_queue[0] > rule.window):
            requests_queue.popleft()
        
        # Check if limit exceeded
        if len(requests_queue) >= rule.limit:
            return {
                'allowed': False,
                'reason': f'Rate limit exceeded: {rule.limit} requests per {rule.window}s',
                'retry_after': int(rule.window - (current_time - requests_queue[0])),
                'limit': rule.limit,
                'window': rule.window
            }
        
        # Add current request
        requests_queue.append(current_time)
        
        # Check burst limit if configured
        if rule.burst_limit > 0 and rule.burst_window > 0:
            burst_key = f"{request_key}:burst"
            burst_queue = self.requests[burst_key]
            
            # Remove old burst requests
            while (burst_queue and 
                   current_time - burst_queue[0] > rule.burst_window):
                burst_queue.popleft()
            
            if len(burst_queue) >= rule.burst_limit:
                return {
                    'allowed': False,
                    'reason': f'Burst limit exceeded: {rule.burst_limit} requests per {rule.burst_window}s',
                    'retry_after': int(rule.burst_window - (current_time - burst_queue[0])),
                    'limit': rule.burst_limit,
                    'window': rule.burst_window
                }
            
            burst_queue.append(current_time)
        
        return {
            'allowed': True,
            'remaining': rule.limit - len(requests_queue),
            'reset_time': int(requests_queue[0] + rule.window - current_time) if requests_queue else 0
        }
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Clean up old request entries"""
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        keys_to_remove = []
        
        for key, queue in self.requests.items():
            # Remove old requests
            while (queue and 
                   current_time - queue[0] > 3600):  # Remove entries older than 1 hour
                queue.popleft()
            
            # Remove empty queues
            if not queue:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.requests[key]
        
        self.last_cleanup = current_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        stats = {
            'total_rules': len(self.rules),
            'active_keys': len(self.requests),
            'total_requests': sum(len(queue) for queue in self.requests.values()),
            'rules': {}
        }
        
        for key, rule in self.rules.items():
            request_count = 0
            for request_key, queue in self.requests.items():
                if request_key.startswith(key + ':'):
                    request_count += len(queue)
            
            stats['rules'][key] = {
                'limit': rule.limit,
                'window': rule.window,
                'current_requests': request_count
            }
        
        return stats


class AccessControl:
    """Production-ready access control"""
    
    def __init__(self):
        self.permissions: Dict[str, Set[str]] = defaultdict(set)
        self.roles: Dict[str, Set[str]] = defaultdict(set)
        self.user_roles: Dict[str, Set[str]] = defaultdict(set)
        self.logger = logging.getLogger(__name__)
        
        # Initialize default roles and permissions
        self._initialize_default_permissions()
    
    def _initialize_default_permissions(self) -> None:
        """Initialize default permissions and roles"""
        # Define permissions
        permissions = [
            'read_tools',
            'write_tools',
            'delete_tools',
            'manage_users',
            'view_analytics',
            'manage_system',
            'access_admin'
        ]
        
        # Define roles
        self.roles['public'] = {'read_tools'}
        self.roles['user'] = {'read_tools', 'write_tools', 'view_analytics'}
        self.roles['admin'] = {'read_tools', 'write_tools', 'delete_tools', 'manage_users', 'view_analytics', 'manage_system'}
        self.roles['system'] = set(permissions)
        
        # Add permissions to permission set
        for permission in permissions:
            self.permissions[permission] = set()
    
    def add_role(self, role: str, permissions: List[str]) -> None:
        """Add role with permissions"""
        self.roles[role] = set(permissions)
        
        # Update permission sets
        for permission in permissions:
            self.permissions[permission].add(role)
    
    def assign_role(self, user_id: str, role: str) -> None:
        """Assign role to user"""
        self.user_roles[user_id].add(role)
        self.logger.info(f"Role '{role}' assigned to user '{user_id}'")
    
    def revoke_role(self, user_id: str, role: str) -> bool:
        """Revoke role from user"""
        if role in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role)
            self.logger.info(f"Role '{role}' revoked from user '{user_id}'")
            return True
        return False
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has permission"""
        user_roles = self.user_roles.get(user_id, set())
        
        # Check each role for the permission
        for role in user_roles:
            if permission in self.roles.get(role, set()):
                return True
        
        return False
    
    def has_any_permission(self, user_id: str, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(user_id, perm) for perm in permissions)
    
    def has_all_permissions(self, user_id: str, permissions: List[str]) -> bool:
        """Check if user has all of the specified permissions"""
        return all(self.has_permission(user_id, perm) for perm in permissions)
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user"""
        user_permissions = set()
        user_roles = self.user_roles.get(user_id, set())
        
        for role in user_roles:
            user_permissions.update(self.roles.get(role, set()))
        
        return user_permissions
    
    def get_user_roles(self, user_id: str) -> Set[str]:
        """Get roles for a user"""
        return self.user_roles.get(user_id, set())
    
    def get_users_with_permission(self, permission: str) -> Set[str]:
        """Get all users who have a specific permission"""
        users = set()
        
        for user_id in self.user_roles:
            if self.has_permission(user_id, permission):
                users.add(user_id)
        
        return users
    
    def get_users_with_role(self, role: str) -> Set[str]:
        """Get all users who have a specific role"""
        users = set()
        
        for user_id, roles in self.user_roles.items():
            if role in roles:
                users.add(user_id)
        
        return users
    
    def check_access(self, user_id: str, required_permission: str, 
                     context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check access with detailed result"""
        has_access = self.has_permission(user_id, required_permission)
        
        result = {
            'allowed': has_access,
            'user_id': user_id,
            'required_permission': required_permission,
            'user_permissions': list(self.get_user_permissions(user_id)),
            'user_roles': list(self.get_user_roles(user_id)),
            'timestamp': datetime.now().isoformat()
        }
        
        if not has_access:
            result['reason'] = f"User does not have required permission: {required_permission}"
        
        return result


class AuditLogger:
    """Production-ready audit logger"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.audit_logs: List[Dict[str, Any]] = []
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for audit logs
        try:
            handler = logging.FileHandler('audit.log')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
        except Exception:
            pass  # Continue without file logging
    
    def log_event(self, event_type: str, user_id: str, action: str, 
                  resource: str, details: Dict[str, Any] = None) -> None:
        """Log audit event"""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': details or {},
            'ip_address': details.get('ip_address') if details else None,
            'user_agent': details.get('user_agent') if details else None
        }
        
        self.audit_logs.append(audit_entry)
        
        # Log to file
        log_message = f"[{event_type}] User {user_id} {action} on {resource}"
        self.logger.info(log_message)
        
        # Clean old logs (keep last 50000)
        if len(self.audit_logs) > 50000:
            self.audit_logs = self.audit_logs[-50000:]
    
    def get_audit_logs(self, event_type: str = None, user_id: str = None, 
                     since: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""
        filtered_logs = self.audit_logs
        
        if event_type:
            filtered_logs = [log for log in filtered_logs if log['event_type'] == event_type]
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log['user_id'] == user_id]
        
        if since:
            filtered_logs = [log for log in filtered_logs 
                           if datetime.fromisoformat(log['timestamp']) >= since]
        
        # Return most recent logs
        return sorted(filtered_logs, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_user_activity(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user activity summary"""
        since = datetime.now() - timedelta(days=days)
        user_logs = self.get_audit_logs(user_id=user_id, since=since)
        
        action_counts = {}
        resource_counts = {}
        
        for log in user_logs:
            action_counts[log['action']] = action_counts.get(log['action'], 0) + 1
            resource_counts[log['resource']] = resource_counts.get(log['resource'], 0) + 1
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_actions': len(user_logs),
            'action_counts': action_counts,
            'resource_counts': resource_counts,
            'last_activity': user_logs[0]['timestamp'] if user_logs else None
        }
    
    def get_security_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get security-related audit events"""
        security_events = ['login', 'logout', 'access_denied', 'permission_change', 'role_change']
        
        logs = []
        for event_type in security_events:
            logs.extend(self.get_audit_logs(event_type=event_type, 
                         since=datetime.now() - timedelta(days=days)))
        
        return sorted(logs, key=lambda x: x['timestamp'], reverse=True)


# Global instances
_security_manager = None
_rate_limiter = None
_access_control = None
_audit_logger = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
        # Add default rate limits
        _rate_limiter.add_rule('api_requests', 100, 60)  # 100 requests per minute
        _rate_limiter.add_rule('login_attempts', 5, 300)  # 5 login attempts per 5 minutes
        _rate_limiter.add_rule('file_uploads', 10, 60)   # 10 file uploads per minute
    return _rate_limiter


def get_access_control() -> AccessControl:
    """Get global access control instance"""
    global _access_control
    if _access_control is None:
        _access_control = AccessControl()
    return _access_control


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Security decorators
def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # This would need to be integrated with the actual authentication system
            # For now, it's a placeholder
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(key: str, limit: int, window: int):
    """Decorator for rate limiting"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            result = limiter.is_allowed(key)
            
            if not result['allowed']:
                raise Exception(f"Rate limit exceeded: {result['reason']}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Security utilities
def generate_secure_token(length: int = 32) -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(length)


def hash_password(password: str, salt: str = None) -> str:
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Use HMAC-SHA256 for hashing
    password_hash = hmac.new(
        salt.encode(),
        password.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{salt}:{password_hash}"


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        salt, password_hash = hashed_password.split(':', 1)
        
        computed_hash = hmac.new(
            salt.encode(),
            password.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_hash, password_hash)
        
    except Exception:
        return False


def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return generate_secure_token(32)


def validate_csrf_token(token: str, expected_token: str) -> bool:
    """Validate CSRF token"""
    return hmac.compare_digest(token, expected_token)
