from django.urls import path
from . import views

app_name = 'meetings'

urlpatterns = [
    # Meeting CRUD
    path('', views.meeting_list, name='meeting_list'),
    path('create/', views.create_meeting, name='create_meeting'),
    path('<uuid:room_id>/', views.meeting_detail, name='meeting_detail'),
    
    # Meeting actions
    path('<uuid:room_id>/join/', views.join_meeting, name='join_meeting'),
    path('<uuid:room_id>/leave/', views.leave_meeting, name='leave_meeting'),
    path('<uuid:room_id>/start/', views.start_meeting, name='start_meeting'),
    path('<uuid:room_id>/end/', views.end_meeting, name='end_meeting'),
    
    # Invitations
    path('<uuid:room_id>/invite/', views.invite_users, name='invite_users'),
    path('invitations/', views.my_invitations, name='my_invitations'),
    path('invitations/<int:invitation_id>/respond/', views.respond_to_invitation, name='respond_to_invitation'),
    
    # Meeting data
    path('<uuid:room_id>/recordings/', views.meeting_recordings, name='meeting_recordings'),
    path('<uuid:room_id>/attendance/', views.meeting_attendance, name='meeting_attendance'),
]