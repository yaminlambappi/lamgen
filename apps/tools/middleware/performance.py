"""
Performance Optimization Middleware
Optimizes responses for Core Web Vitals and <100kb payload
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.conf import settings
from apps.tools.services.performance_optimizer import performance_optimizer
import gzip


class PerformanceMiddleware(MiddlewareMixin):
    """Middleware to optimize responses for performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.optimizer = performance_optimizer
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only optimize HTML responses
        if (hasattr(response, 'content') and 
            response.get('Content-Type', '').startswith('text/html')):
            
            # Skip optimization for certain paths
            skip_paths = ['/admin/', '/api/', '/static/']
            if any(request.path.startswith(path) for path in skip_paths):
                return response
            
            try:
                # Optimize the HTML content
                optimization_result = self.optimizer.optimize_html(
                    response.content, 
                    self._get_page_type(request)
                )
                
                # Update response with optimized content
                response.content = optimization_result['content']
                response['Content-Length'] = str(len(optimization_result['content']))
                
                # Add compression headers
                for header, value in optimization_result['headers'].items():
                    response[header] = value
                
                # Cache performance metrics
                self.optimizer.set_performance_metrics(
                    request.get_full_path(),
                    optimization_result['metrics']
                )
                
            except Exception as e:
                # Log error but don't break response
                if settings.DEBUG:
                    print(f"Performance optimization error: {e}")
        
        return response
    
    def _get_page_type(self, request) -> str:
        """Determine page type from request path"""
        
        path = request.path
        
        if '/tools/' in path:
            if '/category/' in path:
                return 'category'
            elif path.count('/') >= 4:  # /tools/category/tool/variant/
                return 'longtail'
            else:
                return 'tool'
        elif '/user-content/' in path:
            return 'user_content'
        elif '/seo/' in path:
            return 'seo_page'
        else:
            return 'general'
