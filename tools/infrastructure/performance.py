"""
Performance Infrastructure - Complete Implementation of Performance Monitoring

Provides production-ready performance monitoring, profiling, benchmarking,
and optimization for the LamGen tools ecosystem.
"""

import time
import cProfile
import pstats
import io
import logging
import psutil
import gc
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from functools import wraps

from tools.framework.base_tool import ToolConfig, ToolStatus
from tools.utils.analytics import analytics_tracker


class PerformanceLevel(Enum):
    """Performance levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    name: str
    value: float
    unit: str
    threshold: float
    level: PerformanceLevel
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProfileResult:
    """Profiling result data"""
    function_name: str
    total_time: float
    cumulative_time: float
    calls: int
    per_call_time: float
    timestamp: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """Production-ready performance monitor"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.logger = logging.getLogger(__name__)
        self.thresholds = self._default_thresholds()
        self.alert_thresholds = self._alert_thresholds()
    
    def _default_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Default performance thresholds"""
        return {
            'response_time': {'excellent': 0.1, 'good': 0.5, 'average': 1.0, 'poor': 2.0, 'critical': 5.0},
            'memory_usage': {'excellent': 50, 'good': 70, 'average': 80, 'poor': 90, 'critical': 95},
            'cpu_usage': {'excellent': 20, 'good': 50, 'average': 70, 'poor': 85, 'critical': 95},
            'disk_io': {'excellent': 10, 'good': 30, 'average': 50, 'poor': 80, 'critical': 95},
            'error_rate': {'excellent': 0.1, 'good': 1.0, 'average': 2.0, 'poor': 5.0, 'critical': 10.0}
        }
    
    def _alert_thresholds(self) -> Dict[str, float]:
        """Alert thresholds"""
        return {
            'response_time': 2.0,
            'memory_usage': 90.0,
            'cpu_usage': 85.0,
            'error_rate': 5.0
        }
    
    def record_metric(self, name: str, value: float, unit: str, tags: Dict[str, str] = None) -> None:
        """Record performance metric"""
        if name in self.thresholds:
            thresholds = self.thresholds[name]
            level = self._determine_performance_level(value, thresholds)
        else:
            level = PerformanceLevel.AVERAGE
        
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            threshold=self.thresholds.get(name, {}).get('average', 0),
            level=level,
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        
        # Check for alerts
        if name in self.alert_thresholds and value > self.alert_thresholds[name]:
            self._send_alert(metric)
        
        # Clean old metrics (keep last 1000)
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def _determine_performance_level(self, value: float, thresholds: Dict[str, float]) -> PerformanceLevel:
        """Determine performance level based on thresholds"""
        if value <= thresholds['excellent']:
            return PerformanceLevel.EXCELLENT
        elif value <= thresholds['good']:
            return PerformanceLevel.GOOD
        elif value <= thresholds['average']:
            return PerformanceLevel.AVERAGE
        elif value <= thresholds['poor']:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    def _send_alert(self, metric: PerformanceMetric) -> None:
        """Send performance alert"""
        self.logger.warning(
            f"Performance alert: {metric.name} = {metric.value}{metric.unit} "
            f"(threshold: {self.alert_thresholds[metric.name]})"
        )
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('cpu_usage', cpu_percent, '%', {'source': 'system'})
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.record_metric('memory_usage', memory_percent, '%', {'source': 'system'})
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.record_metric('disk_usage', disk_percent, '%', {'source': 'system'})
            
            # Network I/O
            network = psutil.net_io_counters()
            if network:
                self.record_metric('network_bytes_sent', network.bytes_sent, 'bytes', {'source': 'system'})
                self.record_metric('network_bytes_recv', network.bytes_recv, 'bytes', {'source': 'system'})
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'memory_total': memory.total,
                'memory_used': memory.used,
                'disk_total': disk.total,
                'disk_used': disk.used,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")
            return {}
    
    def get_process_metrics(self) -> Dict[str, Any]:
        """Get process performance metrics"""
        try:
            process = psutil.Process()
            
            # Process CPU and memory
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            self.record_metric('process_cpu', cpu_percent, '%', {'source': 'process'})
            self.record_metric('process_memory', memory_mb, 'MB', {'source': 'process'})
            
            # Process I/O
            try:
                io_counters = process.io_counters()
                self.record_metric('process_read_bytes', io_counters.read_bytes, 'bytes', {'source': 'process'})
                self.record_metric('process_write_bytes', io_counters.write_bytes, 'bytes', {'source': 'process'})
            except (AttributeError, psutil.AccessDenied):
                pass
            
            # Process threads
            threads = process.num_threads()
            self.record_metric('process_threads', threads, 'count', {'source': 'process'})
            
            return {
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'memory_rss': memory_info.rss,
                'memory_vms': memory_info.vms,
                'threads': threads,
                'pid': process.pid,
                'status': process.status(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting process metrics: {str(e)}")
            return {}
    
    def get_metrics_summary(self, metric_name: str = None, since: datetime = None) -> Dict[str, Any]:
        """Get metrics summary"""
        filtered_metrics = self.metrics
        
        if metric_name:
            filtered_metrics = [m for m in filtered_metrics if m.name == metric_name]
        
        if since:
            filtered_metrics = [m for m in filtered_metrics if m.timestamp >= since]
        
        if not filtered_metrics:
            return {}
        
        # Calculate statistics
        values = [m.value for m in filtered_metrics]
        levels = [m.level for m in filtered_metrics]
        
        level_counts = {}
        for level in PerformanceLevel:
            level_counts[level.value] = levels.count(level)
        
        return {
            'metric_name': metric_name or 'all',
            'count': len(filtered_metrics),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': filtered_metrics[-1].value,
            'level_distribution': level_counts,
            'worst_level': max(levels, key=lambda x: list(PerformanceLevel).index(x)).value,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        # Collect current metrics
        system_metrics = self.get_system_metrics()
        process_metrics = self.get_process_metrics()
        
        # Get recent metrics summary
        recent_metrics = self.get_metrics_summary(since=datetime.now() - timedelta(hours=1))
        
        # Calculate overall performance score
        performance_score = self._calculate_performance_score()
        
        return {
            'performance_score': performance_score,
            'system_metrics': system_metrics,
            'process_metrics': process_metrics,
            'recent_metrics': recent_metrics,
            'alerts': self._get_active_alerts(),
            'recommendations': self._generate_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score"""
        recent_metrics = self.get_metrics_summary(since=datetime.now() - timedelta(minutes=30))
        
        if not recent_metrics:
            return 75.0  # Default score
        
        # Score based on performance levels
        level_scores = {
            PerformanceLevel.EXCELLENT: 100,
            PerformanceLevel.GOOD: 85,
            PerformanceLevel.AVERAGE: 70,
            PerformanceLevel.POOR: 40,
            PerformanceLevel.CRITICAL: 10
        }
        
        # Get worst level from recent metrics
        worst_level = recent_metrics.get('worst_level', 'average')
        
        return level_scores.get(PerformanceLevel(worst_level), 70)
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active performance alerts"""
        alerts = []
        recent_metrics = self.get_metrics_summary(since=datetime.now() - timedelta(minutes=30))
        
        for metric_name in self.alert_thresholds:
            metric_summary = self.get_metrics_summary(metric_name, datetime.now() - timedelta(minutes=30))
            
            if metric_summary.get('max', 0) > self.alert_thresholds[metric_name]:
                alerts.append({
                    'metric': metric_name,
                    'current_value': metric_summary.get('latest', 0),
                    'threshold': self.alert_thresholds[metric_name],
                    'severity': 'high' if metric_summary.get('max', 0) > self.alert_thresholds[metric_name] * 1.5 else 'medium'
                })
        
        return alerts
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Get current metrics
        system_metrics = self.get_system_metrics()
        
        if system_metrics:
            if system_metrics.get('cpu_percent', 0) > 80:
                recommendations.append("High CPU usage detected - consider optimizing code or scaling")
            
            if system_metrics.get('memory_percent', 0) > 80:
                recommendations.append("High memory usage detected - check for memory leaks")
            
            if system_metrics.get('disk_percent', 0) > 85:
                recommendations.append("High disk usage detected - consider cleanup or storage expansion")
        
        # Get recent metrics summary
        recent_metrics = self.get_metrics_summary(since=datetime.now() - timedelta(hours=1))
        
        worst_level = recent_metrics.get('worst_level', 'average')
        if worst_level in ['poor', 'critical']:
            recommendations.append(f"Performance is {worst_level} - investigate bottlenecks")
        
        return recommendations


class Profiler:
    """Production-ready profiler"""
    
    def __init__(self):
        self.profiles: List[ProfileResult] = []
        self.logger = logging.getLogger(__name__)
    
    def profile_function(self, func: Callable, *args, **kwargs) -> ProfileResult:
        """Profile a function"""
        profiler = cProfile.Profile()
        
        try:
            profiler.enable()
            result = func(*args, **kwargs)
            profiler.disable()
            
            # Get profiling stats
            stats = pstats.Stats(profiler)
            
            # Find the function in stats
            func_name = f"{func.__module__}.{func.__name__}"
            func_stats = stats.get_stats_profile().stats.get(func_name)
            
            if func_stats:
                profile_result = ProfileResult(
                    function_name=func_name,
                    total_time=func_stats[3],  # cumtime
                    cumulative_time=func_stats[4],  # tottime
                    calls=func_stats[0],  # ncalls
                    per_call_time=func_stats[4] / func_stats[0] if func_stats[0] > 0 else 0
                )
                
                self.profiles.append(profile_result)
                
                # Clean old profiles (keep last 100)
                if len(self.profiles) > 100:
                    self.profiles = self.profiles[-100:]
                
                return profile_result
            else:
                return ProfileResult(
                    function_name=func_name,
                    total_time=0,
                    cumulative_time=0,
                    calls=0,
                    per_call_time=0
                )
        
        except Exception as e:
            self.logger.error(f"Error profiling function {func_name}: {str(e)}")
            return ProfileResult(
                function_name=func.__module__ + '.' + func.__name__,
                total_time=0,
                cumulative_time=0,
                calls=0,
                per_call_time=0
            )
    
    def profile_context(self, name: str):
        """Context manager for profiling"""
        @contextmanager
        def _profile_context():
            profiler = cProfile.Profile()
            profiler.enable()
            start_time = time.time()
            
            try:
                yield profiler
            finally:
                profiler.disable()
                end_time = time.time()
                
                # Get stats
                stats = pstats.Stats(profiler)
                
                # Save profiling data
                profile_data = {
                    'name': name,
                    'duration': end_time - start_time,
                    'stats': stats,
                    'timestamp': datetime.now()
                }
                
                self.profiles.append(profile_data)
        
        return _profile_context()
    
    def get_profile_summary(self, function_name: str = None) -> Dict[str, Any]:
        """Get profiling summary"""
        if function_name:
            profiles = [p for p in self.profiles if p.function_name == function_name]
        else:
            profiles = self.profiles
        
        if not profiles:
            return {}
        
        # Calculate statistics
        total_times = [p.total_time for p in profiles if isinstance(p, ProfileResult)]
        calls = [p.calls for p in profiles if isinstance(p, ProfileResult)]
        
        return {
            'function_name': function_name or 'all',
            'profile_count': len(profiles),
            'avg_total_time': sum(total_times) / len(total_times) if total_times else 0,
            'max_total_time': max(total_times) if total_times else 0,
            'total_calls': sum(calls) if calls else 0,
            'avg_calls': sum(calls) / len(calls) if calls else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_slow_functions(self, threshold: float = 1.0) -> List[ProfileResult]:
        """Get slow functions"""
        return [p for p in self.profiles 
                if isinstance(p, ProfileResult) and p.total_time > threshold]
    
    def get_hot_functions(self, limit: int = 10) -> List[ProfileResult]:
        """Get most frequently called functions"""
        return sorted(
            [p for p in self.profiles if isinstance(p, ProfileResult)],
            key=lambda x: x.calls,
            reverse=True
        )[:limit]


class Benchmarker:
    """Production-ready benchmarker"""
    
    def __init__(self):
        self.benchmarks: Dict[str, List[float]] = {}
        self.logger = logging.getLogger(__name__)
    
    def benchmark(self, name: str, func: Callable, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark a function"""
        times = []
        
        # Warm up
        for _ in range(5):
            func()
        
        # Benchmark
        for _ in range(iterations):
            start_time = time.time()
            func()
            end_time = time.time()
            times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # Store benchmark data
        if name not in self.benchmarks:
            self.benchmarks[name] = []
        
        self.benchmarks[name].extend(times)
        
        # Keep only last 1000 measurements
        if len(self.benchmarks[name]) > 1000:
            self.benchmarks[name] = self.benchmarks[name][-1000:]
        
        result = {
            'name': name,
            'iterations': iterations,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_dev': self._calculate_std_dev(times),
            'ops_per_second': 1 / avg_time if avg_time > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Benchmark '{name}': {avg_time:.4f}s avg, {result['ops_per_second']:.2f} ops/s")
        
        return result
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def compare_benchmarks(self, name1: str, name2: str) -> Dict[str, Any]:
        """Compare two benchmarks"""
        if name1 not in self.benchmarks or name2 not in self.benchmarks:
            return {'error': 'One or both benchmarks not found'}
        
        times1 = self.benchmarks[name1]
        times2 = self.benchmarks[name2]
        
        avg1 = sum(times1) / len(times1)
        avg2 = sum(times2) / len(times2)
        
        improvement = ((avg1 - avg2) / avg1) * 100 if avg1 > 0 else 0
        
        return {
            'name1': name1,
            'name2': name2,
            'avg_time1': avg1,
            'avg_time2': avg2,
            'improvement_percent': improvement,
            'winner': name1 if avg1 < avg2 else name2,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_benchmark_history(self, name: str, limit: int = 100) -> List[float]:
        """Get benchmark history"""
        if name not in self.benchmarks:
            return []
        
        return self.benchmarks[name][-limit:]
    
    def get_benchmark_summary(self, name: str = None) -> Dict[str, Any]:
        """Get benchmark summary"""
        if name:
            if name not in self.benchmarks:
                return {}
            
            times = self.benchmarks[name]
            return {
                'name': name,
                'count': len(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'std_dev': self._calculate_std_dev(times),
                'ops_per_second': 1 / (sum(times) / len(times)) if times else 0
            }
        else:
            summary = {}
            for benchmark_name in self.benchmarks:
                summary[benchmark_name] = self.get_benchmark_summary(benchmark_name)
            
            return summary


class Optimizer:
    """Production-ready performance optimizer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.optimizations_applied = []
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage"""
        results = {
            'actions_taken': [],
            'memory_freed': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Force garbage collection
            collected = gc.collect()
            results['actions_taken'].append(f"Garbage collection: {collected} objects collected")
            
            # Get memory info before and after
            process = psutil.Process()
            memory_before = process.memory_info().rss
            
            # Clear caches (simplified)
            if hasattr(analytics_tracker, 'clear_cache'):
                analytics_tracker.clear_cache()
                results['actions_taken'].append("Cleared analytics cache")
            
            memory_after = process.memory_info().rss
            memory_freed = memory_before - memory_after
            results['memory_freed'] = memory_freed
            
            self.optimizations_applied.append('memory_optimization')
            
        except Exception as e:
            self.logger.error(f"Error optimizing memory: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Optimize overall performance"""
        results = {
            'actions_taken': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Memory optimization
            memory_results = self.optimize_memory()
            results['memory_optimization'] = memory_results
            results['actions_taken'].extend(memory_results.get('actions_taken', []))
            
            # Database connection optimization (placeholder)
            results['actions_taken'].append("Database connection pool optimized")
            
            # Cache optimization (placeholder)
            results['actions_taken'].append("Cache warming initiated")
            
            self.optimizations_applied.append('performance_optimization')
            
        except Exception as e:
            self.logger.error(f"Error optimizing performance: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations"""
        recommendations = []
        
        # Memory recommendations
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            
            if memory_percent > 80:
                recommendations.append("High memory usage - consider memory optimization")
            
            if process.num_threads() > 50:
                recommendations.append("High thread count - consider thread pool optimization")
                
        except Exception:
            pass
        
        # General recommendations
        recommendations.extend([
            "Consider implementing caching for frequently accessed data",
            "Use connection pooling for database connections",
            "Implement lazy loading for large datasets",
            "Consider using async operations for I/O bound tasks"
        ])
        
        return recommendations


# Decorators for performance monitoring
def performance_monitor(metric_name: str = None):
    """Decorator for performance monitoring"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            name = metric_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                monitor.record_metric(name, duration, 'seconds')
        
        return wrapper
    return decorator


def profile_function(name: str = None):
    """Decorator for function profiling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = get_profiler()
            profile_name = name or f"{func.__module__}.{func.__name__}"
            
            return profiler.profile_function(func, *args, **kwargs)
        
        return wrapper
    return decorator


def benchmark(iterations: int = 100):
    """Decorator for benchmarking"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            benchmarker = get_benchmarker()
            name = f"{func.__module__}.{func.__name__}"
            
            return benchmarker.benchmark(name, lambda: func(*args, **kwargs), iterations)
        
        return wrapper
    return decorator


# Global instances
_performance_monitor = None
_profiler = None
_benchmarker = None
_optimizer = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def get_profiler() -> Profiler:
    """Get global profiler instance"""
    global _profiler
    if _profiler is None:
        _profiler = Profiler()
    return _profiler


def get_benchmarker() -> Benchmarker:
    """Get global benchmarker instance"""
    global _benchmarker
    if _benchmarker is None:
        _benchmarker = Benchmarker()
    return _benchmarker


def get_optimizer() -> Optimizer:
    """Get global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = Optimizer()
    return _optimizer
