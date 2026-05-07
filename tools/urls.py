from django.urls import path
from . import views
from .api.json_formatter import JSONFormatterAPI
from .api.base64_encoder import Base64EncoderAPI
from .api.regex_tester import RegexTesterAPI
from .api.test_views import test_json_formatter, test_base64_encoder, test_regex_tester
from .api.minimal_test import minimal_json_test

app_name = 'tools'

urlpatterns = [
    path('', views.tools_index_view, name='index'),
    path('api/islamic-panel/', views.islamic_panel_api, name='islamic_panel_api'),
    # Minimal test endpoint
    path('api/minimal/json-test/', minimal_json_test, name='minimal_json_test'),
    # Test endpoints without decorators
    path('api/test/json-formatter/', test_json_formatter, name='test_json_formatter_api'),
    path('api/test/base64-encoder/', test_base64_encoder, name='test_base64_encoder_api'),
    path('api/test/regex-tester/', test_regex_tester, name='test_regex_tester_api'),
    # Production endpoints
    path('api/json-formatter/', JSONFormatterAPI().handle_request, name='json_formatter_api'),
    path('api/base64-encoder/', Base64EncoderAPI().handle_request, name='base64_encoder_api'),
    path('api/regex-tester/', RegexTesterAPI().handle_request, name='regex_tester_api'),
    path('search/', views.search_view, name='search'),
    path('trending/', views.trending_view, name='trending'),
    path('bookmark/toggle/', views.toggle_bookmark, name='bookmark'),
    path('bookmark/save/', views.toggle_bookmark_auth, name='bookmark_auth'),
    path('usage/record/', views.record_usage, name='record_usage'),
    path('<slug:category_slug>/<slug:tool_slug>/embed/', views.embed_view, name='embed'),
    path('<slug:category_slug>/<slug:tool_slug>/<slug:variant_slug>/', views.longtail_view, name='longtail'),
    path('<slug:category_slug>/', views.category_view, name='category'),
    path('<slug:category_slug>/<slug:tool_slug>/', views.tool_view, name='tool'),
]
