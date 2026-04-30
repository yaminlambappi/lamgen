from django.urls import path

from generation import views

app_name = 'generation'

urlpatterns = [
    path('submit/', views.submit_job, name='submit_job'),
    path('<uuid:pk>/status/', views.job_status, name='job_status'),
    path('<uuid:pk>/status/json/', views.job_status_json, name='job_status_json'),
    path('<uuid:pk>/confirm-outline/', views.confirm_outline, name='confirm_outline'),
    path('<uuid:pk>/edit-outline/', views.edit_outline, name='edit_outline'),
]
