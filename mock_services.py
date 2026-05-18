
from apps.ai_tools.services.career_tool_service import CareerToolService
from apps.ai_tools.services.writing_tool_service import WritingToolService
from apps.ai_tools.services.seo_tool_service import SEOToolService
from apps.ai_tools.services.social_tool_service import SocialToolService
from apps.ai_tools.services.developer_tool_service import DeveloperToolService
from apps.ai_tools.services.education_tool_service import EducationToolService
from apps.ai_tools.services.base_tool_service import BaseToolService

class MockCareerToolService(CareerToolService):
    def execute(self, tool_slug, user_input):
        return {"result": "This is a mock response for " + tool_slug}

class MockWritingToolService(WritingToolService):
    def execute(self, tool_slug, user_input):
        return {"result": "This is a mock response for " + tool_slug}

class MockSEOToolService(SEOToolService):
    def execute(self, tool_slug, user_input):
        return {"result": "This is a mock response for " + tool_slug}

class MockSocialToolService(SocialToolService):
    def execute(self, tool_slug, user_input):
        return {"result": "This is a mock response for " + tool_slug}

class MockDeveloperToolService(DeveloperToolService):
    def execute(self, tool_slug, user_input):
        return {"result": "This is a mock response for " + tool_slug}

class MockEducationToolService(EducationToolService):
    def execute(self, tool_slug, user_input):
        return {"result": "This is a mock response for " + tool_slug}

class MockBaseToolService(BaseToolService):
    def execute(self, tool_slug, user_input):
        return {"result": "This is a mock response for " + tool_slug}
