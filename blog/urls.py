from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.blog_index, name="index"),
    path("<slug:content_type>/", views.blog_type_index, name="type_index"),
    path("<slug:content_type>/<slug:slug>/", views.article_view, name="article"),
]
