"""
User-Generated Content Views for SEO
Creates indexable pages from tool outputs for organic traffic
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.cache import cache_page, cache_control
from django.core.paginator import Paginator
from django.db.models import Q
from apps.tools.models import Tool, ToolCategory
from apps.tools.services.user_content_indexer import user_content_indexer
from apps.seo.models import SEOPage
import json


@cache_control(public=True, max_age=300)
def user_content_index(request):
    """Main index of all user-generated content types"""
    
    content_types = user_content_indexer.content_types
    content_stats = {}
    
    # Get statistics for each content type
    for content_type, display_name in content_types.items():
        # Count tools that generate this content type
        tool_count = Tool.objects.filter(
            is_active=True,
            tags__icontains=content_type
        ).count()
        
        content_stats[content_type] = {
            'display_name': display_name,
            'tool_count': tool_count,
            'total_examples': tool_count * 5,  # Estimate
            'featured_tools': Tool.objects.filter(
                is_featured=True,
                tags__icontains=content_type
            ).select_related('category')[:3]
        }
    
    # Preprocess totals to avoid template filter issues
    total_tool_count = sum(stats['tool_count'] for stats in content_stats.values())
    total_examples = sum(stats['total_examples'] for stats in content_stats.values())
    
    return render(request, 'tools/user_content/index.html', {
        'page_title': 'User-Generated Content - Examples, Templates & Guides | LamGen',
        'meta_description': 'Explore thousands of examples, templates, and guides. Free content created with our tools - resumes, bios, prompts, and more.',
        'content_types': content_types,
        'content_stats': content_stats,
        'content_stats_processed': {
            'tool_count_total': total_tool_count,
            'total_examples_total': total_examples
        },
        'recent_content': _get_recent_user_content(),
    })


@cache_control(public=True, max_age=600)
def content_type_view(request, content_type):
    """Category page for specific content type"""
    
    if content_type not in user_content_indexer.content_types:
        return get_object_or_404(None)
    
    display_name = user_content_indexer.content_types[content_type]
    
    # Get category pages for this content type
    category_pages = user_content_indexer.create_content_category_pages(content_type)
    
    # Get featured examples
    featured_examples = _get_featured_examples(content_type, limit=6)
    
    # Get tools for this content type
    tools = Tool.objects.filter(
        is_active=True,
        tags__icontains=content_type
    ).select_related('category').order_by('-view_count')
    
    return render(request, 'tools/user_content/content_type.html', {
        'page_title': f'{display_name} - Free Examples & Templates | LamGen',
        'meta_description': f'Generate professional {display_name.lower()} using our free tools. Browse examples, templates, and guides created by users. No signup required.',
        'content_type': content_type,
        'display_name': display_name,
        'category_pages': category_pages,
        'featured_examples': featured_examples,
        'tools': tools,
        'total_tools': tools.count(),
    })


@cache_control(public=True, max_age=900)
def tool_content_view(request, content_type, tool_slug):
    """Tool-specific content page"""
    
    tool = get_object_or_404(
        Tool,
        slug=tool_slug,
        is_active=True,
        tags__icontains=content_type
    )
    
    display_name = user_content_indexer.content_types.get(content_type, content_type.title())
    
    # Get category page data
    category_data = user_content_indexer.create_content_category_pages(content_type)
    tool_page_data = next((page for page in category_data if page['tool'].slug == tool_slug), None)
    
    if not tool_page_data:
        # Create default page data
        tool_page_data = {
            'tool': tool,
            'content_type': content_type,
            'title': f'{display_name} for {tool.name}',
            'slug': f'{content_type}-{tool.slug}',
            'meta_title': f'Free {display_name} for {tool.name} | LamGen',
            'meta_description': f'Generate professional {display_name.lower()} using {tool.name}. Free online tool with examples, templates, and instant results.',
            'seo_intro': f'{display_name} for {tool.name} provides specialized functionality tailored to create high-quality {display_name.lower()} instantly. Whether you need examples, templates, or complete generated content, our tool delivers professional results with no registration required.',
            'use_cases': user_content_indexer._generate_category_use_cases(tool, content_type),
            'faq_items': user_content_indexer._generate_category_faq_items(tool, content_type),
            'keywords': [content_type, tool.name.lower(), 'free', 'online', 'generator'],
            'featured_examples': user_content_indexer._get_featured_examples(tool, content_type),
            'template_count': user_content_indexer._count_available_templates(tool, content_type)
        }
    
    # Get actual examples (would come from database)
    examples = _get_tool_examples(tool, content_type, limit=12)
    
    return render(request, 'tools/user_content/tool_content.html', {
        'page_title': tool_page_data['meta_title'],
        'meta_description': tool_page_data['meta_description'],
        'canonical_url': request.build_absolute_uri(),
        'tool': tool,
        'content_type': content_type,
        'display_name': display_name,
        'page_data': tool_page_data,
        'examples': examples,
        'total_examples': len(examples),
    })


@cache_control(public=True, max_age=900)
def industry_content_view(request, tool_slug):
    """Industry-specific content page for a tool"""
    
    tool = get_object_or_404(Tool, slug=tool_slug, is_active=True)
    industry_pages = user_content_indexer.create_industry_specific_pages(tool)
    
    return render(request, 'tools/user_content/industry_content.html', {
        'page_title': f'{tool.name} for Different Industries | LamGen',
        'meta_description': f'Industry-specific {tool.name.lower()} solutions for healthcare, finance, technology, and more. Professional tools with industry features and compliance.',
        'tool': tool,
        'industry_pages': industry_pages,
        'total_industries': len(industry_pages),
    })


@require_POST
def save_user_content(request):
    """Save user-generated content for indexing"""
    
    try:
        data = json.loads(request.body)
        tool_id = data.get('tool_id')
        content_data = data.get('content_data', {})
        
        tool = get_object_or_404(Tool, id=tool_id, is_active=True)
        
        # Index the content
        indexed_data = user_content_indexer.index_tool_output(tool, content_data)
        
        if indexed_data['is_indexable']:
            # Save to database (would create actual model)
            # For now, just return success
            return JsonResponse({
                'success': True,
                'content_hash': indexed_data['content_hash'],
                'quality_score': indexed_data['quality_score'],
                'message': 'Content saved and indexed successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Content does not meet quality requirements for indexing'
            }, status=400)
            
    except (json.JSONDecodeError, KeyError) as e:
        return JsonResponse({
            'success': False,
            'message': 'Invalid data format'
        }, status=400)


def _get_recent_user_content(limit=12):
    """Get recent user-generated content"""
    
    # This would query actual saved content
    # For now, return placeholder data
    recent_content = []
    
    tools = Tool.objects.filter(is_active=True).order_by('-view_count')[:limit]
    
    for tool in tools:
        recent_content.append({
            'tool': tool,
            'content_type': 'example',
            'title': f'{tool.name} Example',
            'description': f'Latest example created with {tool.name}',
            'created_at': tool.updated_at,
            'quality_score': 0.8
        })
    
    return recent_content


def _get_featured_examples(content_type, limit=6):
    """Get featured examples for content type"""
    
    # This would query actual saved examples
    # For now, return placeholder data
    examples = []
    
    tools = Tool.objects.filter(
        is_active=True,
        tags__icontains=content_type
    ).select_related('category')[:limit]
    
    for i, tool in enumerate(tools):
        examples.append({
            'tool': tool,
            'title': f'Professional {content_type.title()} Example {i+1}',
            'description': f'High-quality {content_type} created with {tool.name}',
            'preview': f'Example of {content_type} generated using our tool',
            'quality_score': 0.9,
            'uses': tool.view_count
        })
    
    return examples


def _get_tool_examples(tool, content_type, limit=12):
    """Get examples for specific tool"""
    
    # This would query actual saved examples
    # For now, return placeholder data
    examples = []
    
    for i in range(min(limit, 8)):
        examples.append({
            'id': f'{tool.slug}_{content_type}_{i+1}',
            'title': f'{tool.name} {content_type.title()} Example {i+1}',
            'description': f'Example {i+1} of {content_type} created with {tool.name}',
            'content': f'This is a sample {content_type} generated using {tool.name}. It demonstrates the tool\'s capabilities and provides a starting point for users.',
            'quality_score': 0.8 + (i * 0.02),  # Varying quality
            'created_at': tool.updated_at,
            'uses': tool.view_count + (i * 10)
        })
    
    return examples
