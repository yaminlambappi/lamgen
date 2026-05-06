from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.tools_index_view, name='index'),
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
