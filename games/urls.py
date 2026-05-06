from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.game_index, name='index'),
    path('api/rtc/create/', views.create_room, name='create_room'),
    path('api/rtc/post/<str:code>/', views.post_signal, name='post_signal'),
    path('api/rtc/get/<str:code>/', views.get_signal, name='get_signal'),
]
