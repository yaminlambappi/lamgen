from django.urls import path
from . import views

app_name = 'seo'

urlpatterns = [
    path('<slug:category_slug>/', views.category_view, name='category'),
    path('<slug:category_slug>/<slug:page_slug>/', views.page_view, name='page'),
]
