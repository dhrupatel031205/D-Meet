from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='profile_detail'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('connections/', views.my_connections, name='connections'),
    path('connection-requests/', views.connection_requests, name='connection_requests'),
    path('send-connection-request/<int:user_id>/', views.send_connection_request, name='send_connection_request'),
    path('accept-connection-request/<int:request_id>/', views.accept_connection_request, name='accept_connection_request'),
    path('reject-connection-request/<int:request_id>/', views.reject_connection_request, name='reject_connection_request'),
]