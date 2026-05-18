from .core import Tool, Category, registry
from config.tool_categories import TOOL_CATEGORIES

def _get_tool_type(t_data):
    if t_data.get('is_ai_powered'):
        return 'ai'
    # we can infer more logic here, or default to browser
    slug = t_data.get('slug', '')
    if 'ai-' in slug or 'generator' in slug and t_data.get('is_ai_powered', False):
        return 'ai'
    return 'browser'

def load_registry():
    for c_data in TOOL_CATEGORIES:
        category = Category(
            slug=c_data['slug'],
            name=c_data['name'],
            description=c_data.get('short_desc', ''),
            icon=c_data.get('icon', ''),
            color_from=c_data.get('color_from', '#000000'),
            color_to=c_data.get('color_to', '#ffffff')
        )
        registry.register_category(category)
        
        for t_data in c_data.get('tools', []):
            tool_type = _get_tool_type(t_data)
            tags = t_data.get('tags', '')
            keywords = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            tool = Tool(
                slug=t_data['slug'],
                title=t_data['name'],
                description=t_data.get('short_desc', ''),
                category_slug=c_data['slug'],
                tool_type=tool_type,
                icon=t_data.get('icon', 'bi-tools'),
                route=f"/tools/{t_data['slug']}/",  # NEW Dynamic route
                seo_title=f"{t_data['name']} - Free Online Tool | LamGen",
                seo_description=t_data.get('short_desc', ''),
                keywords=keywords,
                model="gemini-2.5-flash" if tool_type == 'ai' else "",
                featured=t_data.get('is_featured', False),
                homepage_visibility=True,
                template_name=t_data.get('template_name')
            )
            registry.register_tool(tool)

load_registry()
