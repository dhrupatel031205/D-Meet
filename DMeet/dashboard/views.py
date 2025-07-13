from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from core.models import Event, RSVP, Feedback
from meetings.models import MeetingRoom, MeetingAttendance
from notifications.models import Notification
from accounts.models import UserConnection, ConnectionRequest

User = get_user_model()


@login_required
def user_dashboard(request):
    """User dashboard with personal stats and quick actions"""
    user = request.user
    
    # Redirect based on user role
    if user.is_admin:
        return redirect('dashboard:admin_dashboard')
    elif user.is_organizer:
        return redirect('dashboard:organizer_dashboard')
    
    # User stats
    my_rsvps = RSVP.objects.filter(user=user)
    upcoming_events = my_rsvps.filter(event__start_time__gte=timezone.now())[:5]
    past_events = my_rsvps.filter(event__end_time__lt=timezone.now())[:5]
    
    # Meeting stats
    meeting_attendances = MeetingAttendance.objects.filter(user=user)
    upcoming_meetings = MeetingRoom.objects.filter(
        invitations__invited_user=user,
        invitations__response='ACCEPTED',
        scheduled_start__gte=timezone.now()
    )[:5]
    
    # Connection stats
    my_connections = UserConnection.objects.filter(
        Q(user1=user) | Q(user2=user)
    ).count()
    
    pending_requests = ConnectionRequest.objects.filter(
        to_user=user,
        accepted=False
    ).count()
    
    # Notification stats
    unread_notifications = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    # Reviews to write
    events_to_review = []
    for rsvp in my_rsvps.filter(event__end_time__lt=timezone.now()):
        if not Feedback.objects.filter(user=user, event=rsvp.event).exists():
            events_to_review.append(rsvp.event)
    
    context = {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'upcoming_meetings': upcoming_meetings,
        'my_connections': my_connections,
        'pending_requests': pending_requests,
        'unread_notifications': unread_notifications,
        'events_to_review': events_to_review[:5],
        'total_rsvps': my_rsvps.count(),
        'total_meetings_attended': meeting_attendances.count(),
    }
    
    return render(request, 'dashboard/user_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_organizer)
def organizer_dashboard(request):
    """Organizer dashboard with event management and analytics"""
    user = request.user
    
    # Event stats
    my_events = Event.objects.filter(organizer=user)
    upcoming_events = my_events.filter(start_time__gte=timezone.now())
    past_events = my_events.filter(end_time__lt=timezone.now())
    pending_approval = my_events.filter(approved=False)
    
    # RSVP stats
    total_rsvps = RSVP.objects.filter(event__organizer=user).count()
    recent_rsvps = RSVP.objects.filter(
        event__organizer=user,
        rsvp_time__gte=timezone.now() - timedelta(days=7)
    )
    
    # Meeting stats
    my_meetings = MeetingRoom.objects.filter(host=user)
    upcoming_meetings = my_meetings.filter(scheduled_start__gte=timezone.now())
    
    # Feedback stats
    feedbacks = Feedback.objects.filter(event__organizer=user)
    from django.db.models import Avg
    avg_rating = feedbacks.aggregate(
        avg_rating=Avg('rating')
    )['avg_rating'] or 0
    
    context = {
        'my_events': my_events,
        'upcoming_events': upcoming_events[:5],
        'past_events': past_events[:5],
        'pending_approval': pending_approval,
        'my_meetings': my_meetings,
        'upcoming_meetings': upcoming_meetings[:5],
        'total_rsvps': total_rsvps,
        'recent_rsvps': recent_rsvps.count(),
        'avg_rating': round(avg_rating, 1),
        'total_feedbacks': feedbacks.count(),
    }
    
    return render(request, 'dashboard/organizer_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_admin)
def admin_dashboard(request):
    """Admin dashboard with system-wide analytics and management"""
    
    # User stats
    total_users = User.objects.count()
    new_users_week = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    active_users = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Event stats
    total_events = Event.objects.count()
    pending_events = Event.objects.filter(approved=False).count()
    events_this_week = Event.objects.filter(
        start_time__gte=timezone.now(),
        start_time__lt=timezone.now() + timedelta(days=7)
    ).count()
    
    # Meeting stats
    total_meetings = MeetingRoom.objects.count()
    active_meetings = MeetingRoom.objects.filter(status='ACTIVE').count()
    
    # RSVP stats
    total_rsvps = RSVP.objects.count()
    rsvps_this_week = RSVP.objects.filter(
        rsvp_time__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # System health
    recent_events = Event.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    )
    recent_users = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    )
    
    context = {
        'total_users': total_users,
        'new_users_week': new_users_week,
        'active_users': active_users,
        'total_events': total_events,
        'pending_events': pending_events,
        'events_this_week': events_this_week,
        'total_meetings': total_meetings,
        'active_meetings': active_meetings,
        'total_rsvps': total_rsvps,
        'rsvps_this_week': rsvps_this_week,
        'recent_events': recent_events[:10],
        'recent_users': recent_users[:10],
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def analytics(request):
    """Analytics page with charts and detailed metrics"""
    if not request.user.is_organizer:
        return redirect('dashboard:user_dashboard')
    
    # This would contain detailed analytics charts and metrics
    # For now, redirect to appropriate dashboard
    if request.user.is_admin:
        return redirect('dashboard:admin_dashboard')
    else:
        return redirect('dashboard:organizer_dashboard')


@login_required
@user_passes_test(lambda u: u.is_admin)
def system_health(request):
    """System health monitoring page"""
    # Database stats
    db_stats = {
        'users': User.objects.count(),
        'events': Event.objects.count(),
        'meetings': MeetingRoom.objects.count(),
        'rsvps': RSVP.objects.count(),
        'notifications': Notification.objects.count(),
    }
    
    # Recent activity
    recent_activity = []
    
    # Recent RSVPs
    recent_rsvps = RSVP.objects.select_related('user', 'event')[:10]
    for rsvp in recent_rsvps:
        recent_activity.append({
            'type': 'RSVP',
            'user': rsvp.user.username,
            'description': f"RSVPed to {rsvp.event.title}",
            'timestamp': rsvp.rsvp_time
        })
    
    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:5]
    for user in recent_users:
        recent_activity.append({
            'type': 'USER',
            'user': user.username,
            'description': f"New user registered",
            'timestamp': user.date_joined
        })
    
    # Sort by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'db_stats': db_stats,
        'recent_activity': recent_activity[:20],
    }
    
    return render(request, 'dashboard/system_health.html', context)