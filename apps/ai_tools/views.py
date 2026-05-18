from django.shortcuts import render
from django.http import Http404
from apps.ai_tools.registry import get_tool, get_all_tools, get_tools_by_category

def ai_tools_index(request):
    """
    Renders the AI Tools discovery page.
    Groups tools by category.
    """
    tools = get_all_tools()
    
    # Group by category
    categories = {}
    for tool in tools:
        cat = tool.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)
        
    return render(request, "ai_tools/index.html", {
        "categories": categories,
        "page_title": "AI Tools Directory",
        "meta_description": "Discover all our powerful AI tools in one place."
    })

def ai_tool_detail(request, category_slug, tool_slug):
    """
    Renders the dynamic AI Tool page.
    Driven entirely by the registry metadata.
    """
    tool = get_tool(tool_slug)
    if not tool or tool.get("category") != category_slug:
        raise Http404("Tool not found")
        
    return render(request, "ai_tools/detail.html", {
        "tool": tool,
        "page_title": f"{tool['name']} - AI Tool",
        "meta_description": tool.get("system_prompt", "")[:150]
    })
