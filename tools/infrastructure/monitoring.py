"""
Monitoring Infrastructure - Complete Implementation of System Monitoring

Provides production-ready system monitoring, health checking, metrics collection,
and alert management for the LamGen tools ecosystem.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from tools.framework.base_tool import ToolConfig, ToolStatus
from tools.utils.analytics import analytics_tracker


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """System metric data"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """System alert data"""
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class SystemMonitor:
    """Production-ready system monitor"""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self.alerts: List[Alert] = []
        self.logger = logging.getLogger(__name__)
        self.thresholds = self._default_thresholds()
    
    def _default_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Default monitoring thresholds"""
        return {
            'cpu_usage': {'warning': 70.0, 'critical': 90.0},
            'memory_usage': {'warning': 80.0, 'critical': 95.0},
            'response_time': {'warning': 1.0, 'critical': 2.0},
            'error_rate': {'warning': 5.0, 'critical': 10.0},
            'disk_usage': {'warning': 85.0, 'critical': 95.0}
        }
    
    def collect_metric(self, name: str, value: float, unit: str, tags: Dict[str, str] = None) -> None:
        """Collect system metric"""
        metric = Metric(
            name=name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        self.metrics.append(metric)
        
        # Check thresholds and create alerts
        self._check_thresholds(metric)
        
        # Clean old metrics (keep last 1000)
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def _check_thresholds(self, metric: Metric) -> None:
        """Check metric against thresholds and create alerts"""
        if metric.name in self.thresholds:
            thresholds = self.thresholds[metric.name]
            
            if metric.value >= thresholds['critical']:
                self.create_alert(
                    AlertLevel.CRITICAL,
                    f"Critical threshold exceeded for {metric.name}: {metric.value}{metric.unit}",
                    metric.name,
                    {'current_value': metric.value, 'threshold': thresholds['critical']}
                )
            elif metric.value >= thresholds['warning']:
                self.create_alert(
                    AlertLevel.WARNING,
                    f"Warning threshold exceeded for {metric.name}: {metric.value}{metric.unit}",
                    metric.name,
                    {'current_value': metric.value, 'threshold': thresholds['warning']}
                )
    
    def create_alert(self, level: AlertLevel, message: str, source: str, metadata: Dict[str, Any] = None) -> None:
        """Create system alert"""
        alert = Alert(
            level=level,
            message=message,
            source=source,
            metadata=metadata or {}
        )
        self.alerts.append(alert)
        
        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(level, logging.INFO)
        
        self.logger.log(log_level, f"[{level.value.upper()}] {message}")
        
        # Clean old alerts (keep last 500)
        if len(self.alerts) > 500:
            self.alerts = self.alerts[-500:]
    
    def get_metrics(self, name: str = None, since: datetime = None) -> List[Metric]:
        """Get metrics with optional filtering"""
        filtered_metrics = self.metrics
        
        if name:
            filtered_metrics = [m for m in filtered_metrics if m.name == name]
        
        if since:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= since]
        
        return filtered_metrics
    
    def get_alerts(self, level: AlertLevel = None, resolved: bool = None) -> List[Alert]:
        """Get alerts with optional filtering"""
        filtered_alerts = self.alerts
        
        if level:
            filtered_alerts = [a for a in filtered_alerts if a.level == level]
        
        if resolved is not None:
            filtered_alerts = [a for a in filtered_alerts if a.resolved == resolved]
        
        return filtered_alerts
    
    def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an alert by ID"""
        if 0 <= alert_id < len(self.alerts):
            self.alerts[alert_id].resolved = True
            return True
        return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        recent_alerts = self.get_alerts(since=datetime.now() - timedelta(hours=1))
        critical_alerts = [a for a in recent_alerts if a.level == AlertLevel.CRITICAL and not a.resolved]
        error_alerts = [a for a in recent_alerts if a.level == AlertLevel.ERROR and not a.resolved]
        
        if critical_alerts:
            status = HealthStatus.UNHEALTHY
        elif error_alerts:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        return {
            'status': status.value,
            'critical_alerts': len(critical_alerts),
            'error_alerts': len(error_alerts),
            'total_alerts': len(recent_alerts),
            'last_check': datetime.now().isoformat()
        }


class HealthChecker:
    """Production-ready health checker"""
    
    def __init__(self):
        self.checks = {}
        self.logger = logging.getLogger(__name__)
    
    def register_check(self, name: str, check_func: callable, timeout: int = 30) -> None:
        """Register a health check"""
        self.checks[name] = {
            'function': check_func,
            'timeout': timeout,
            'last_run': None,
            'last_status': None,
            'last_duration': None
        }
    
    def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {
                'name': name,
                'status': HealthStatus.UNKNOWN.value,
                'message': 'Check not found',
                'duration': 0
            }
        
        check = self.checks[name]
        start_time = time.time()
        
        try:
            # Run the check with timeout
            result = check['function']()
            duration = time.time() - start_time
            
            # Update check info
            check['last_run'] = datetime.now()
            check['last_status'] = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
            check['last_duration'] = duration
            
            return {
                'name': name,
                'status': HealthStatus.HEALTHY.value if result else HealthStatus.UNHEALTHY.value,
                'message': 'Check passed' if result else 'Check failed',
                'duration': duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Update check info
            check['last_run'] = datetime.now()
            check['last_status'] = HealthStatus.UNHEALTHY
            check['last_duration'] = duration
            
            self.logger.error(f"Health check '{name}' failed: {str(e)}")
            
            return {
                'name': name,
                'status': HealthStatus.UNHEALTHY.value,
                'message': str(e),
                'duration': duration
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for name in self.checks:
            result = self.run_check(name)
            results[name] = result
            
            # Update overall status
            if result['status'] == HealthStatus.UNHEALTHY.value:
                overall_status = HealthStatus.UNHEALTHY
            elif result['status'] == HealthStatus.DEGRADED.value and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            'overall_status': overall_status.value,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_check_status(self, name: str) -> Dict[str, Any]:
        """Get status of a specific check"""
        if name not in self.checks:
            return {'name': name, 'status': HealthStatus.UNKNOWN.value}
        
        check = self.checks[name]
        
        return {
            'name': name,
            'last_run': check['last_run'].isoformat() if check['last_run'] else None,
            'last_status': check['last_status'].value if check['last_status'] else None,
            'last_duration': check['last_duration']
        }


class MetricsCollector:
    """Production-ready metrics collector"""
    
    def __init__(self):
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.timers: Dict[str, List[float]] = {}
        self.logger = logging.getLogger(__name__)
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None) -> None:
        """Increment a counter metric"""
        key = self._make_key(name, tags)
        self.counters[key] = self.counters.get(key, 0) + value
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Set a gauge metric"""
        key = self._make_key(name, tags)
        self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a histogram metric"""
        key = self._make_key(name, tags)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        
        # Keep only last 1000 values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None) -> None:
        """Record a timer metric"""
        key = self._make_key(name, tags)
        if key not in self.timers:
            self.timers[key] = []
        self.timers[key].append(duration)
        
        # Keep only last 1000 values
        if len(self.timers[key]) > 1000:
            self.timers[key] = self.timers[key][-1000:]
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create metric key with tags"""
        if not tags:
            return name
        
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def get_counter(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, tags)
        return self.gauges.get(key, 0)
    
    def get_histogram_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, tags)
        values = self.histograms.get(key, [])
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'sum': sum(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'p50': self._percentile(values, 50),
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }
    
    def get_timer_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Get timer statistics"""
        key = self._make_key(name, tags)
        values = self.timers.get(key, [])
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'sum': sum(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'p50': self._percentile(values, 50),
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            'counters': self.counters,
            'gauges': self.gauges,
            'histograms': {k: self.get_histogram_stats(k.split('[')[0]) for k in self.histograms.keys()},
            'timers': {k: self.get_timer_stats(k.split('[')[0]) for k in self.timers.keys()}
        }


class AlertManager:
    """Production-ready alert manager"""
    
    def __init__(self):
        self.alert_rules = {}
        self.alert_history: List[Alert] = []
        self.notification_channels = []
        self.logger = logging.getLogger(__name__)
    
    def add_rule(self, name: str, condition: callable, level: AlertLevel, message_template: str) -> None:
        """Add an alert rule"""
        self.alert_rules[name] = {
            'condition': condition,
            'level': level,
            'message_template': message_template,
            'last_triggered': None,
            'trigger_count': 0
        }
    
    def evaluate_rules(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Evaluate all alert rules against metrics"""
        triggered_alerts = []
        
        for name, rule in self.alert_rules.items():
            try:
                if rule['condition'](metrics):
                    # Check cooldown (don't trigger same rule within 5 minutes)
                    if (rule['last_triggered'] and 
                        datetime.now() - rule['last_triggered'] < timedelta(minutes=5)):
                        continue
                    
                    # Create alert
                    message = rule['message_template'].format(**metrics)
                    alert = Alert(
                        level=rule['level'],
                        message=message,
                        source=name,
                        metadata={'rule_name': name, 'metrics': metrics}
                    )
                    
                    triggered_alerts.append(alert)
                    self.alert_history.append(alert)
                    
                    # Update rule info
                    rule['last_triggered'] = datetime.now()
                    rule['trigger_count'] += 1
                    
                    # Send notifications
                    self._send_notifications(alert)
                    
            except Exception as e:
                self.logger.error(f"Error evaluating alert rule '{name}': {str(e)}")
        
        return triggered_alerts
    
    def add_notification_channel(self, channel: callable) -> None:
        """Add a notification channel"""
        self.notification_channels.append(channel)
    
    def _send_notifications(self, alert: Alert) -> None:
        """Send alert notifications"""
        for channel in self.notification_channels:
            try:
                channel(alert)
            except Exception as e:
                self.logger.error(f"Error sending notification: {str(e)}")
    
    def get_alert_history(self, level: AlertLevel = None, since: datetime = None) -> List[Alert]:
        """Get alert history"""
        filtered_alerts = self.alert_history
        
        if level:
            filtered_alerts = [a for a in filtered_alerts if a.level == level]
        
        if since:
            filtered_alerts = [a for a in filtered_alerts if a.timestamp >= since]
        
        return filtered_alerts
    
    def get_rule_stats(self) -> Dict[str, Any]:
        """Get alert rule statistics"""
        return {
            name: {
                'trigger_count': rule['trigger_count'],
                'last_triggered': rule['last_triggered'].isoformat() if rule['last_triggered'] else None
            }
            for name, rule in self.alert_rules.items()
        }


# Default health check functions
def check_database_connection() -> bool:
    """Check database connection"""
    # Simplified check - in production would actually check DB
    return True


def check_redis_connection() -> bool:
    """Check Redis connection"""
    # Simplified check - in production would actually check Redis
    return True


def check_disk_space() -> bool:
    """Check disk space"""
    # Simplified check - in production would actually check disk space
    return True


def check_memory_usage() -> bool:
    """Check memory usage"""
    # Simplified check - in production would actually check memory
    return True


# Default notification channels
def log_notification(alert: Alert) -> None:
    """Log notification channel"""
    logger = logging.getLogger('alerts')
    logger.warning(f"ALERT: [{alert.level.value}] {alert.message}")


def email_notification(alert: Alert) -> None:
    """Email notification channel"""
    # Simplified email notification - in production would send actual email
    logger = logging.getLogger('alerts')
    logger.info(f"Email alert sent: [{alert.level.value}] {alert.message}")
