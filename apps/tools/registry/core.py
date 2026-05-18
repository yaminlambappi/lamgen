from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Tool:
    slug: str
    title: str
    description: str
    category_slug: str
    tool_type: str  # 'ai', 'browser', 'hybrid'
    icon: str
    route: str
    seo_title: str
    seo_description: str
    keywords: List[str]
    model: str = "gemini-2.5-flash"
    prompt_ref: Optional[str] = None
    featured: bool = False
    homepage_visibility: bool = True
    template_name: Optional[str] = None

@dataclass
class Category:
    slug: str
    name: str
    description: str
    icon: str
    color_from: str
    color_to: str
    tools: List[Tool] = field(default_factory=list)

class ToolRegistry:
    def __init__(self):
        self.categories = {}
        self.tools = {}

    def register_category(self, category: Category):
        self.categories[category.slug] = category

    def register_tool(self, tool: Tool):
        self.tools[tool.slug] = tool
        if tool.category_slug in self.categories:
            self.categories[tool.category_slug].tools.append(tool)

    def get_tool(self, slug: str) -> Optional[Tool]:
        return self.tools.get(slug)

    def get_all_tools(self) -> List[Tool]:
        return list(self.tools.values())

    def get_tools_by_type(self, tool_type: str) -> List[Tool]:
        return [t for t in self.tools.values() if t.tool_type == tool_type]

registry = ToolRegistry()
