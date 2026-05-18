from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.career_tool_service import CareerToolService
from ..services.writing_tool_service import WritingToolService
from ..services.seo_tool_service import SEOToolService
from ..services.social_tool_service import SocialToolService
from ..services.developer_tool_service import DeveloperToolService
from ..services.education_tool_service import EducationToolService
from ..services.base_tool_service import BaseToolService
from mock_services import (
    MockCareerToolService,
    MockWritingToolService,
    MockSEOToolService,
    MockSocialToolService,
    MockDeveloperToolService,
    MockEducationToolService,
    MockBaseToolService,
)

# Career AI
class AIResumeBuilderView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockCareerToolService(user=request.user)
        result = service.execute("resume-builder", user_input)
        return Response(result)

class ATSCheckerView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockCareerToolService(user=request.user)
        result = service.execute("ats-checker", user_input)
        return Response(result)

class CoverLetterGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockCareerToolService(user=request.user)
        result = service.execute("cover-letter-generator", user_input)
        return Response(result)

class LinkedInHeadlineGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSocialToolService(user=request.user)
        result = service.execute("linkedin-headline-generator", user_input)
        return Response(result)

class LinkedInPostGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSocialToolService(user=request.user)
        result = service.execute("linkedin-post-generator", user_input)
        return Response(result)

# Writing AI
class AIHumanizerView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockWritingToolService(user=request.user)
        result = service.execute("ai-humanizer", user_input)
        return Response(result)

class EssayWriterView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockWritingToolService(user=request.user)
        result = service.execute("essay-writer", user_input)
        return Response(result)

class ParaphrasingToolView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockWritingToolService(user=request.user)
        result = service.execute("paraphrasing-tool", user_input)
        return Response(result)

class GrammarCheckerView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockWritingToolService(user=request.user)
        result = service.execute("grammar-checker", user_input)
        return Response(result)

class EmailWriterView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockWritingToolService(user=request.user)
        result = service.execute("email-writer", user_input)
        return Response(result)

class ColdEmailGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockWritingToolService(user=request.user)
        result = service.execute("cold-email-generator", user_input)
        return Response(result)

# SEO / Content AI
class BlogWriterView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSEOToolService(user=request.user)
        result = service.execute("blog-writer", user_input)
        return Response(result)

class SEOArticleGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSEOToolService(user=request.user)
        result = service.execute("seo-article-generator", user_input)
        return Response(result)

class MetaDescriptionGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSEOToolService(user=request.user)
        result = service.execute("meta-description-generator", user_input)
        return Response(result)

class KeywordClusterGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSEOToolService(user=request.user)
        result = service.execute("keyword-cluster-generator", user_input)
        return Response(result)

# Creator AI
class YouTubeScriptGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSocialToolService(user=request.user)
        result = service.execute("youtube-script-generator", user_input)
        return Response(result)

class YouTubeTitleGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSocialToolService(user=request.user)
        result = service.execute("youtube-title-generator", user_input)
        return Response(result)

class ThumbnailPromptGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSocialToolService(user=request.user)
        result = service.execute("thumbnail-prompt-generator", user_input)
        return Response(result)

class InstagramCaptionGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSocialToolService(user=request.user)
        result = service.execute("instagram-caption-generator", user_input)
        return Response(result)

class TweetGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockSocialToolService(user=request.user)
        result = service.execute("tweet-generator", user_input)
        return Response(result)

# Business AI
class StartupNameGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockBaseToolService(user=request.user)
        result = service.execute("startup-name-generator", user_input)
        return Response(result)

class BusinessPlanGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockBaseToolService(user=request.user)
        result = service.execute("business-plan-generator", user_input)
        return Response(result)

class LogoPromptGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockBaseToolService(user=request.user)
        result = service.execute("logo-prompt-generator", user_input)
        return Response(result)

class ImagePromptGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockBaseToolService(user=request.user)
        result = service.execute("image-prompt-generator", user_input)
        return Response(result)

# Student AI
class NotesGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockEducationToolService(user=request.user)
        result = service.execute("notes-generator", user_input)
        return Response(result)

class QuizGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockEducationToolService(user=request.user)
        result = service.execute("quiz-generator", user_input)
        return Response(result)

class FlashcardGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockEducationToolService(user=request.user)
        result = service.execute("flashcard-generator", user_input)
        return Response(result)

# Developer AI
class SQLQueryGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockDeveloperToolService(user=request.user)
        result = service.execute("sql-query-generator", user_input)
        return Response(result)

class RegexGeneratorView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockDeveloperToolService(user=request.user)
        result = service.execute("regex-generator", user_input)
        return Response(result)

class CodeDebuggerView(APIView):
    def post(self, request, *args, **kwargs):
        user_input = request.data.get("prompt", "")
        service = MockDeveloperToolService(user=request.user)
        result = service.execute("code-debugger", user_input)
        return Response(result)
