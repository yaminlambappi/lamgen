from django.urls import path
from . import views
from .view_modules.authority_pages import guide_view, compare_view, learn_view, best_tools_view, workflow_view

app_name = 'seo'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('category/<slug:category_slug>/', views.category_view, name='category'),
    path('category/<slug:category_slug>/page/<slug:page_slug>/', views.page_view, name='page'),
    # Authority pages
    path('guides/', guide_view, name='guide'),
    path('guides/<slug:guide_slug>/', guide_view, name='guide'),
    path('compare/', compare_view, name='compare'),
    path('compare/<slug:compare_slug>/', compare_view, name='compare'),
    path('learn/', learn_view, name='learn'),
    path('learn/<slug:topic_slug>/', learn_view, name='learn'),
    path('best-tools/', best_tools_view, name='best_tools'),
    path('best-tools/<slug:category_slug>/', best_tools_view, name='best_tools'),
    path('workflows/', workflow_view, name='workflow'),
    path('workflows/<slug:workflow_slug>/', workflow_view, name='workflow'),
]
