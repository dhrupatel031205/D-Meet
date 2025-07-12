from django.urls import path
from . import views

urlpatterns = [
    # Home and main pages
    path('', views.home, name='home'),
    path('map/', views.map_view, name='map'),
    path('about/', views.about, name='about'),
    
    # Event URLs
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('event/create/', views.EventCreateView.as_view(), name='event_create'),
    
    # RSVP URLs
    path('event/<int:pk>/rsvp/', views.rsvp_event, name='rsvp_event'),
    path('event/<int:pk>/cancel-rsvp/', views.cancel_rsvp, name='cancel_rsvp'),
    
    # Feedback URLs
    path('event/<int:pk>/feedback/', views.give_feedback, name='give_feedback'),
    
    # Connection URLs
    path('event/<int:event_pk>/connect/<int:user_pk>/', views.make_connection, name='make_connection'),
    
    # User URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('register/', views.register, name='register'),
]