"""
Test views for API endpoints without decorators
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .json_formatter import JSONFormatterAPI
from .base64_encoder import Base64EncoderAPI
from .regex_tester import RegexTesterAPI


@csrf_exempt
@require_POST
def test_json_formatter(request):
    """Test JSON formatter API without decorators"""
    api = JSONFormatterAPI()
    return api.handle_request(request)


@csrf_exempt
@require_POST
def test_base64_encoder(request):
    """Test Base64 encoder API without decorators"""
    api = Base64EncoderAPI()
    return api.handle_request(request)


@csrf_exempt
@require_POST
def test_regex_tester(request):
    """Test Regex tester API without decorators"""
    api = RegexTesterAPI()
    return api.handle_request(request)
