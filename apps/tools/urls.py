from django.urls import path
from . import views
from .view_modules import ecosystem
from .api.json_formatter import JSONFormatterAPI
from .api.base64_encoder import Base64EncoderAPI
from .api.regex_tester import RegexTesterAPI
from .api.test_views import test_json_formatter, test_base64_encoder, test_regex_tester
from .api.minimal_test import minimal_json_test

app_name = 'tools'

urlpatterns = [
    path('', views.tools_index_view, name='index'),

    # Minimal test endpoint
    path('api/minimal/json-test/', minimal_json_test, name='minimal_json_test'),
    # Games data API endpoint
    path('api/games-data/', views.games_data_api, name='games_data_api'),
    # Test endpoints without decorators
    path('api/test/json-formatter/', test_json_formatter, name='test_json_formatter_api'),
    path('api/test/base64-encoder/', test_base64_encoder, name='test_base64_encoder_api'),
    path('api/test/regex-tester/', test_regex_tester, name='test_regex_tester_api'),
    # Production endpoints
    path('api/json-formatter/', JSONFormatterAPI().handle_request, name='json_formatter_api'),
    path('api/base64-encoder/', Base64EncoderAPI().handle_request, name='base64_encoder_api'),
    path('api/regex-tester/', RegexTesterAPI().handle_request, name='regex_tester_api'),
    # Ecosystem API endpoints
    path('api/related-tools/<int:tool_id>/', ecosystem.related_tools_api, name='related_tools_api'),
    path('api/people-also-use/<int:tool_id>/', ecosystem.people_also_use_api, name='people_also_use_api'),
    path('api/workflow-options/<int:tool_id>/', ecosystem.workflow_options_api, name='workflow_options_api'),
    path('api/user-session/', ecosystem.user_session_api, name='user_session_api'),
    path('api/update-session/', ecosystem.update_session_api, name='update_session_api'),
    path('api/workflow/<str:workflow_id>/', ecosystem.workflow_chain_api, name='workflow_chain_api'),
    path('api/save-workflow/', ecosystem.save_workflow_chain_api, name='save_workflow_chain_api'),
    path('api/category/<slug:category_slug>/', ecosystem.category_hub_api, name='category_hub_api'),
    # Existing endpoints
    path('search/', views.search_view, name='search'),
    path('trending/', views.trending_view, name='trending'),
    path('api/tool-counts/', views.tool_counts_api, name='tool_counts_api'),
    path('bookmark/toggle/', views.toggle_bookmark, name='bookmark'),
    path('bookmark/save/', views.toggle_bookmark_auth, name='bookmark_auth'),
    path('usage/record/', views.record_usage, name='record_usage'),
    
    # Old routing redirect (SEO fallback)
    path('<slug:category_slug>/<slug:tool_slug>/embed/', views.embed_view, name='embed'),
    path('<slug:category_slug>/<slug:tool_slug>/<slug:variant_slug>/', views.longtail_redirect_view, name='longtail'),
    path('<slug:category_slug>/<slug:tool_slug>/', views.tool_redirect_view, name='tool_redirect_old'),
    
    # New Dynamic Routing & Dispatcher
    path('<slug:category_slug>/', views.category_or_tool_dispatcher, name='category'),
    path('<slug:tool_slug>/', views.category_or_tool_dispatcher, name='tool'),
]
