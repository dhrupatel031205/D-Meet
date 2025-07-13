from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.user_dashboard, name='user_dashboard'),
    path('organizer/', views.organizer_dashboard, name='organizer_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('system-health/', views.system_health, name='system_health'),
]