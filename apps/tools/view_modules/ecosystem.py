"""
Ecosystem Views
API endpoints for related tools, workflow chaining, and user session data
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.core.cache import cache
from apps.tools.models import Tool
from apps.tools.services.ecosystem import tool_ecosystem
import json
import time


@require_GET
def related_tools_api(request, tool_id):
    """API endpoint for related tools"""
    try:
        tool = get_object_or_404(Tool, id=tool_id, is_active=True)
        limit = int(request.GET.get('limit', 8))
        offset = int(request.GET.get('offset', 0))
        
        # Get related tools
        related_tools = tool_ecosystem.get_related_tools(tool, limit + offset)
        
        # Paginate results
        has_more = len(related_tools) > limit
        tools_to_return = related_tools[:limit]
        
        # Format response
        response_data = {
            'tools': [{
                'id': item['tool'].id,
                'name': item['tool'].name,
                'slug': item['tool'].slug,
                'short_desc': item['tool'].short_desc,
                'category_name': item['tool'].category.name,
                'category_slug': item['tool'].category.slug,
                'icon': item['tool'].icon,
                'relevance_score': item['relevance_score'],
                'relationship_type': item['relationship_type'],
                'reason': item['reason'],
                'usage_count': item['tool'].usage_count,
                'view_count': item['tool'].view_count
            } for item in tools_to_return],
            'has_more': has_more,
            'total': len(related_tools)
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'tools': [],
            'has_more': False
        }, status=500)


@require_GET
def people_also_use_api(request, tool_id):
    """API endpoint for people also use tools"""
    try:
        tool = get_object_or_404(Tool, id=tool_id, is_active=True)
        limit = int(request.GET.get('limit', 6))
        offset = int(request.GET.get('offset', 0))
        
        # Get popular tools in same category
        people_also_use = tool_ecosystem.get_people_also_use(tool, limit + offset)
        
        # Paginate results
        has_more = len(people_also_use) > limit
        tools_to_return = people_also_use[:limit]
        
        # Format response
        response_data = {
            'tools': [{
                'id': item['tool'].id,
                'name': item['tool'].name,
                'slug': item['tool'].slug,
                'short_desc': item['tool'].short_desc,
                'category_name': item['tool'].category.name,
                'category_slug': item['tool'].category.slug,
                'icon': item['tool'].icon,
                'usage_count': item['usage_count'],
                'view_count': item['view_count'],
                'position': item['position']
            } for item in tools_to_return],
            'has_more': has_more,
            'total': len(people_also_use)
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'tools': [],
            'has_more': False
        }, status=500)


@require_GET
def workflow_options_api(request, tool_id):
    """API endpoint for workflow options"""
    try:
        tool = get_object_or_404(Tool, id=tool_id, is_active=True)
        
        # Get workflow suggestions
        workflow_suggestions = tool_ecosystem.get_workflow_suggestions(tool)
        
        # Format response
        response_data = {
            'workflow_options': [{
                'tool_id': item['tool'].id,
                'tool_name': item['tool'].name,
                'tool_slug': item['tool'].slug,
                'tool_icon': item['tool'].icon,
                'workflow_name': item['workflow_name'],
                'description': item['workflow_description'],
                'relevance_score': item['relevance_score'],
                'position': item['position']
            } for item in workflow_suggestions]
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'workflow_options': []
        }, status=500)


@require_GET
def user_session_api(request):
    """API endpoint for user session data"""
    try:
        # Get or create session key
        session_key = request.GET.get('session_key') or request.session.session_key
        
        # Get user session data
        session_data = tool_ecosystem.get_user_session_data(session_key)
        
        # Get recent tools with full data
        recent_tools = []
        for item in session_data.get('recent_tools', [])[:10]:
            try:
                tool = Tool.objects.get(id=item['id'], is_active=True)
                recent_tools.append({
                    'id': tool.id,
                    'name': tool.name,
                    'slug': tool.slug,
                    'category_name': tool.category.name,
                    'category_slug': tool.category.slug,
                    'icon': tool.icon,
                    'timestamp': item['timestamp']
                })
            except Tool.DoesNotExist:
                continue
        
        # Format response
        response_data = {
            'session_key': session_key,
            'recent_tools': recent_tools,
            'saved_workflows': session_data.get('saved_workflows', []),
            'tool_history': session_data.get('tool_history', {}),
            'preferences': session_data.get('preferences', {}),
            'session_start': session_data.get('session_start', time.time())
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'session_key': '',
            'recent_tools': [],
            'saved_workflows': [],
            'tool_history': {},
            'preferences': {}
        }, status=500)


@require_GET
def category_hub_api(request, category_slug):
    """API endpoint for category hub data"""
    try:
        from apps.tools.models import ToolCategory
        category = get_object_or_404(ToolCategory, slug=category_slug, is_active=True)
        
        # Get category hub data
        hub_data = tool_ecosystem.get_category_hub_data(category)
        
        # Format response
        response_data = {
            'category': {
                'id': hub_data['category'].id,
                'name': hub_data['category'].name,
                'slug': hub_data['category'].slug,
                'description': hub_data['category'].description,
                'short_desc': hub_data['category'].short_desc,
                'icon': hub_data['category'].icon,
                'color_from': hub_data['category'].color_from,
                'color_to': hub_data['category'].color_to
            },
            'total_tools': hub_data['total_tools'],
            'total_usage': hub_data['total_usage'],
            'total_views': hub_data['total_views'],
            'featured_tools': [{
                'id': tool.id,
                'name': tool.name,
                'slug': tool.slug,
                'short_desc': tool.short_desc,
                'icon': tool.icon,
                'usage_count': tool.usage_count,
                'view_count': tool.view_count
            } for tool in hub_data['featured_tools']],
            'trending_tools': [{
                'id': tool.id,
                'name': tool.name,
                'slug': tool.slug,
                'short_desc': tool.short_desc,
                'icon': tool.icon,
                'usage_count': tool.usage_count,
                'view_count': tool.view_count
            } for tool in hub_data['trending_tools']],
            'newest_tools': [{
                'id': tool.id,
                'name': tool.name,
                'slug': tool.slug,
                'short_desc': tool.short_desc,
                'icon': tool.icon,
                'created_at': tool.created_at.isoformat()
            } for tool in hub_data['newest_tools']],
            'subcategories': hub_data['subcategories'],
            'related_categories': [{
                'category': {
                    'id': item['category'].id,
                    'name': item['category'].name,
                    'slug': item['category'].slug,
                    'icon': item['category'].icon
                },
                'similarity_score': item['similarity_score'],
                'overlapping_keywords': item['overlapping_keywords'],
                'tool_count': item['tool_count']
            } for item in hub_data['related_categories']],
            'category_description': hub_data['category_description'],
            'category_intro': hub_data['category_intro'],
            'best_use_cases': hub_data['best_use_cases'],
            'category_faq': hub_data['category_faq'],
            'seo_metadata': hub_data['seo_metadata']
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'category': None,
            'total_tools': 0,
            'featured_tools': [],
            'trending_tools': [],
            'newest_tools': [],
            'subcategories': [],
            'related_categories': []
        }, status=500)


@require_GET
def update_session_api(request):
    """API endpoint to update user session"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        data = json.loads(request.body)
        tool_id = data.get('tool_id')
        action = data.get('action', 'used')
        session_key = data.get('session_key') or request.session.session_key
        
        if not tool_id:
            return JsonResponse({'error': 'Tool ID required'}, status=400)
        
        # Get tool
        tool = get_object_or_404(Tool, id=tool_id, is_active=True)
        
        # Update session
        session_data = tool_ecosystem.update_user_session(session_key, tool, action)
        
        return JsonResponse({
            'success': True,
            'session_data': session_data,
            'message': f'Tool {action} successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False,
            'message': 'Failed to update session'
        }, status=500)


@require_GET
def workflow_chain_api(request, workflow_id):
    """API endpoint for workflow chain"""
    try:
        # Get workflow chain
        workflow_data = tool_ecosystem.get_workflow_chain(workflow_id)
        
        if not workflow_data:
            return JsonResponse({
                'error': 'Workflow not found',
                'workflow': None
            }, status=404)
        
        return JsonResponse({
            'workflow': workflow_data,
            'success': True
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'workflow': None,
            'success': False
        }, status=500)


@require_GET
def save_workflow_chain_api(request):
    """API endpoint to save workflow chain"""
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        data = json.loads(request.body)
        workflow_id = data.get('workflow_id')
        workflow_data = data.get('workflow_data')
        
        if not workflow_id or not workflow_data:
            return JsonResponse({'error': 'Workflow ID and data required'}, status=400)
        
        # Save workflow
        saved_workflow = tool_ecosystem.save_workflow_chain(workflow_id, workflow_data)
        
        return JsonResponse({
            'success': True,
            'workflow_id': workflow_id,
            'message': 'Workflow saved successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False,
            'message': 'Failed to save workflow'
        }, status=500)
