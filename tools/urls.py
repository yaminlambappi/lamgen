from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
    path('', views.workspaces_view, name='index'),
    path('search/', views.search_view, name='search'),
    path('trending/', views.trending_view, name='trending'),
    path('bookmark/toggle/', views.toggle_bookmark, name='bookmark'),
    path('<slug:category_slug>/', views.category_view, name='category'),
    path('<slug:category_slug>/<slug:tool_slug>/', views.tool_view, name='tool'),
]
