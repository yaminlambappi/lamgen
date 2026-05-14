"""
Analytics Framework - Production Analytics for LamGen Tools

Provides comprehensive analytics tracking, user behavior analysis,
and performance monitoring for the tools ecosystem.
"""

import json
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.tools.models import Tool, ToolUsageHistory

User = get_user_model()
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Analytics event types"""
    TOOL_USAGE = "tool_usage"
    TOOL_ERROR = "tool_error"
    TOOL_SHARE = "tool_share"
    TOOL_DOWNLOAD = "tool_download"
    TOOL_BOOKMARK = "tool_bookmark"
    PAGE_VIEW = "page_view"
    USER_REGISTRATION = "user_registration"
    USER_LOGIN = "user_login"


@dataclass
class AnalyticsEvent:
    """Standard analytics event structure"""
    event_type: EventType
    tool_slug: Optional[str] = None
    user_id: Optional[int] = None
    session_key: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = timezone.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'event_type': self.event_type.value,
            'tool_slug': self.tool_slug,
            'user_id': self.user_id,
            'session_key': self.session_key,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class AnalyticsTracker:
    """
    Production analytics tracker with multiple storage backends.
    Supports real-time tracking, aggregation, and reporting.
    """
    
    def __init__(self):
        self.cache_prefix = "analytics"
        self.batch_size = 100
        self.flush_interval = 300  # 5 minutes
        
    def track_event(self, event: AnalyticsEvent) -> None:
        """Track a single analytics event"""
        try:
            # Add to batch cache
            batch_key = f"{self.cache_prefix}:batch"
            current_batch = cache.get(batch_key, [])
            current_batch.append(asdict(event))
            
            # Flush if batch is full
            if len(current_batch) >= self.batch_size:
                self._flush_batch(current_batch)
                cache.set(batch_key, [], self.flush_interval)
            else:
                cache.set(batch_key, current_batch, self.flush_interval)
                
        except Exception as e:
            logger.error(f"Failed to track analytics event: {e}")
    
    def track_tool_usage(self, tool_slug: str, user=None, session_key: str = None, 
                       status: str = "success", processing_time_ms: int = 0) -> None:
        """Track tool usage event"""
        event = AnalyticsEvent(
            event_type=EventType.TOOL_USAGE,
            tool_slug=tool_slug,
            user_id=user.id if user and user.is_authenticated else None,
            session_key=session_key,
            metadata={
                'status': status,
                'processing_time_ms': processing_time_ms,
                'user_agent': self._get_user_agent(),
                'ip_address': self._get_client_ip()
            }
        )
        self.track_event(event)
    
    def track_tool_error(self, tool_slug: str, error_message: str, user=None, 
                      session_key: str = None) -> None:
        """Track tool error event"""
        event = AnalyticsEvent(
            event_type=EventType.TOOL_ERROR,
            tool_slug=tool_slug,
            user_id=user.id if user and user.is_authenticated else None,
            session_key=session_key,
            metadata={
                'error_message': error_message,
                'user_agent': self._get_user_agent(),
                'ip_address': self._get_client_ip()
            }
        )
        self.track_event(event)
    
    def track_page_view(self, page_path: str, user=None, session_key: str = None) -> None:
        """Track page view event"""
        event = AnalyticsEvent(
            event_type=EventType.PAGE_VIEW,
            user_id=user.id if user and user.is_authenticated else None,
            session_key=session_key,
            metadata={
                'page_path': page_path,
                'user_agent': self._get_user_agent(),
                'ip_address': self._get_client_ip()
            }
        )
        self.track_event(event)
    
    def track_tool_share(self, tool_slug: str, share_method: str, user=None, 
                      session_key: str = None) -> None:
        """Track tool share event"""
        event = AnalyticsEvent(
            event_type=EventType.TOOL_SHARE,
            tool_slug=tool_slug,
            user_id=user.id if user and user.is_authenticated else None,
            session_key=session_key,
            metadata={
                'share_method': share_method,  # 'copy', 'download', 'social'
                'user_agent': self._get_user_agent(),
                'ip_address': self._get_client_ip()
            }
        )
        self.track_event(event)
    
    def _flush_batch(self, batch: List[Dict[str, Any]]) -> None:
        """Flush batch of events to persistent storage"""
        try:
            with transaction.atomic():
                for event_data in batch:
                    # Store in database for long-term analysis
                    self._store_event_in_db(event_data)
            
            # Also store in cache for real-time analytics
            self._update_real_time_stats(batch)
            
        except Exception as e:
            logger.error(f"Failed to flush analytics batch: {e}")
    
    def _store_event_in_db(self, event_data: Dict[str, Any]) -> None:
        """Store event in database (simplified for demo)"""
        # In a real implementation, this would store in a dedicated analytics table
        # For now, we'll use the existing ToolUsageHistory model for tool usage events
        if event_data['event_type'] == EventType.TOOL_USAGE.value:
            try:
                tool = Tool.objects.get(slug=event_data['tool_slug'])
                ToolUsageHistory.objects.create(
                    user_id=event_data['user_id'],
                    session_key=event_data['session_key'],
                    tool=tool,
                    used_at=timezone.now()
                )
            except Tool.DoesNotExist:
                pass  # Tool not found, skip
            except Exception as e:
                logger.error(f"Failed to store tool usage: {e}")
    
    def _update_real_time_stats(self, batch: List[Dict[str, Any]]) -> None:
        """Update real-time statistics in cache"""
        current_hour = timezone.now().strftime("%Y%m%d%H")
        
        for event in batch:
            # Update hourly usage counts
            if event['event_type'] == EventType.TOOL_USAGE.value:
                key = f"{self.cache_prefix}:hourly:{current_hour}:{event['tool_slug']}"
                cache.incr(key)
                cache.expire(key, 86400)  # Keep for 24 hours
            
            # Update error counts
            elif event['event_type'] == EventType.TOOL_ERROR.value:
                key = f"{self.cache_prefix}:errors:{current_hour}:{event['tool_slug']}"
                cache.incr(key)
                cache.expire(key, 86400)
    
    def get_tool_stats(self, tool_slug: str, hours: int = 24) -> Dict[str, Any]:
        """Get usage statistics for a specific tool"""
        stats = {
            'total_usage': 0,
            'error_count': 0,
            'success_rate': 0.0,
            'avg_processing_time': 0
        }
        
        current_time = timezone.now()
        
        # Get usage data from cache
        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y%m%d%H")
            
            usage_key = f"{self.cache_prefix}:hourly:{hour_key}:{tool_slug}"
            error_key = f"{self.cache_prefix}:errors:{hour_key}:{tool_slug}"
            
            usage_count = cache.get(usage_key, 0)
            error_count = cache.get(error_key, 0)
            
            stats['total_usage'] += usage_count
            stats['error_count'] += error_count
        
        # Calculate success rate
        if stats['total_usage'] > 0:
            stats['success_rate'] = ((stats['total_usage'] - stats['error_count']) / stats['total_usage']) * 100
        
        return stats
    
    def get_popular_tools(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        """Get most popular tools in the last N hours"""
        tool_usage = {}
        
        current_time = timezone.now()
        
        # Aggregate usage across all tools
        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y%m%d%H")
            
            # Get all keys for this hour
            for key in cache.keys(f"{self.cache_prefix}:hourly:{hour_key}:*"):
                tool_slug = key.split(':')[-1]
                usage = cache.get(key, 0)
                tool_usage[tool_slug] = tool_usage.get(tool_slug, 0) + usage
        
        # Sort by usage and return top N
        sorted_tools = sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {'tool_slug': slug, 'usage_count': count}
            for slug, count in sorted_tools
        ]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        error_summary = {}
        
        current_time = timezone.now()
        
        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y%m%d%H")
            
            # Get all error keys for this hour
            for key in cache.keys(f"{self.cache_prefix}:errors:{hour_key}:*"):
                tool_slug = key.split(':')[-1]
                error_count = cache.get(key, 0)
                error_summary[tool_slug] = error_summary.get(tool_slug, 0) + error_count
        
        return error_summary
    
    def _get_user_agent(self) -> str:
        """Get user agent from request context (simplified)"""
        # In a real implementation, this would come from the request
        return "Unknown"
    
    def _get_client_ip(self) -> str:
        """Get client IP from request context (simplified)"""
        # In a real implementation, this would come from the request
        return "Unknown"


class PerformanceMonitor:
    """
    Performance monitoring for tools and system components.
    Tracks response times, error rates, and system health.
    """
    
    def __init__(self):
        self.cache_prefix = "performance"
        
    def track_tool_performance(self, tool_slug: str, processing_time_ms: int, 
                           status: str = "success") -> None:
        """Track performance metrics for a tool"""
        timestamp = int(time.time())
        key = f"{self.cache_prefix}:{tool_slug}:{timestamp}"
        
        performance_data = {
            'processing_time_ms': processing_time_ms,
            'status': status,
            'timestamp': timestamp
        }
        
        cache.set(key, performance_data, 3600)  # Keep for 1 hour
        
        # Update aggregated stats
        self._update_aggregated_stats(tool_slug, processing_time_ms, status)
    
    def _update_aggregated_stats(self, tool_slug: str, processing_time_ms: int, status: str) -> None:
        """Update aggregated performance statistics"""
        current_hour = timezone.now().strftime("%Y%m%d%H")
        
        # Update processing time stats
        time_key = f"{self.cache_prefix}:time:{current_hour}:{tool_slug}"
        current_times = cache.get(time_key, [])
        current_times.append(processing_time_ms)
        
        # Keep only last 1000 measurements
        if len(current_times) > 1000:
            current_times = current_times[-1000:]
        
        cache.set(time_key, current_times, 86400)
        
        # Update status counts
        status_key = f"{self.cache_prefix}:status:{current_hour}:{tool_slug}"
        current_counts = cache.get(status_key, {'success': 0, 'error': 0})
        current_counts[status] = current_counts.get(status, 0) + 1
        cache.set(status_key, current_counts, 86400)
    
    def get_tool_performance(self, tool_slug: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics for a tool"""
        current_time = timezone.now()
        all_times = []
        status_counts = {'success': 0, 'error': 0}
        
        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y%m%d%H")
            
            time_key = f"{self.cache_prefix}:time:{hour_key}:{tool_slug}"
            status_key = f"{self.cache_prefix}:status:{hour_key}:{tool_slug}"
            
            times = cache.get(time_key, [])
            counts = cache.get(status_key, {'success': 0, 'error': 0})
            
            all_times.extend(times)
            for status, count in counts.items():
                status_counts[status] += count
        
        # Calculate statistics
        stats = {
            'avg_processing_time_ms': 0,
            'min_processing_time_ms': 0,
            'max_processing_time_ms': 0,
            'success_rate': 0.0,
            'total_requests': sum(status_counts.values())
        }
        
        if all_times:
            stats['avg_processing_time_ms'] = sum(all_times) / len(all_times)
            stats['min_processing_time_ms'] = min(all_times)
            stats['max_processing_time_ms'] = max(all_times)
        
        if stats['total_requests'] > 0:
            stats['success_rate'] = (status_counts['success'] / stats['total_requests']) * 100
        
        return stats


# Global instances
analytics_tracker = AnalyticsTracker()
performance_monitor = PerformanceMonitor()
