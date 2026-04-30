from django.urls import path

from . import views

app_name = 'thesis'

urlpatterns = [
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('status/<int:pk>/', views.ThesisStatusView.as_view(), name='status'),
    path('status/<int:pk>/json/', views.ThesisStatusJsonView.as_view(), name='status_json'),
    path('download/<int:pk>/', views.ThesisDownloadView.as_view(), name='download'),
    path('preview/<int:pk>/', views.ThesisPreviewView.as_view(), name='preview'),
    path('delete/<int:pk>/', views.ThesisDeleteView.as_view(), name='delete'),
]
