from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse
from django.core.paginator import Paginator

from .models import MeetingRoom, MeetingAttendance, MeetingInvitation, MeetingRecording
from .forms import MeetingRoomForm, MeetingInvitationForm
from .providers import get_meeting_provider


@login_required
def meeting_list(request):
    """List all meetings for the current user"""
    # Get meetings where user is host or invited
    hosted_meetings = MeetingRoom.objects.filter(host=request.user)
    invited_meetings = MeetingRoom.objects.filter(
        invitations__invited_user=request.user,
        invitations__response='ACCEPTED'
    )
    
    all_meetings = hosted_meetings.union(invited_meetings).order_by('-scheduled_start')
    
    # Pagination
    paginator = Paginator(all_meetings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'hosted_count': hosted_meetings.count(),
        'invited_count': invited_meetings.count(),
    }
    
    return render(request, 'meetings/meeting_list.html', context)


@login_required
def meeting_detail(request, room_id):
    """Meeting detail view"""
    meeting = get_object_or_404(MeetingRoom, room_id=room_id)
    
    # Check if user can access this meeting
    can_access = (
        meeting.host == request.user or
        meeting.invitations.filter(invited_user=request.user, response='ACCEPTED').exists() or
        meeting.is_public
    )
    
    if not can_access:
        messages.error(request, 'You do not have permission to access this meeting.')
        return redirect('meetings:meeting_list')
    
    context = {
        'meeting': meeting,
        'can_join': meeting.can_join,
        'is_host': meeting.host == request.user,
        'attendances': meeting.attendances.all()[:10],
        'invitations': meeting.invitations.all()[:10],
    }
    
    return render(request, 'meetings/meeting_detail.html', context)


@login_required
def create_meeting(request):
    """Create a new meeting"""
    if request.method == 'POST':
        form = MeetingRoomForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.host = request.user
            meeting.save()
            
            # Create meeting room with provider
            provider = get_meeting_provider(meeting.provider)
            meeting_data = provider.create_meeting(meeting)
            
            meeting.meeting_url = meeting_data.get('meeting_url')
            meeting.meeting_id = meeting_data.get('meeting_id')
            meeting.save()
            
            messages.success(request, 'Meeting created successfully!')
            return redirect('meetings:meeting_detail', room_id=meeting.room_id)
    else:
        form = MeetingRoomForm()
    
    return render(request, 'meetings/create_meeting.html', {'form': form})


@login_required
def join_meeting(request, room_id):
    """Join a meeting"""
    meeting = get_object_or_404(MeetingRoom, room_id=room_id)
    
    # Check if user can join
    if not meeting.can_join:
        messages.error(request, 'This meeting is not available for joining.')
        return redirect('meetings:meeting_detail', room_id=room_id)
    
    # Check access permissions
    can_access = (
        meeting.host == request.user or
        meeting.invitations.filter(invited_user=request.user, response='ACCEPTED').exists() or
        meeting.is_public
    )
    
    if not can_access:
        messages.error(request, 'You do not have permission to join this meeting.')
        return redirect('meetings:meeting_detail', room_id=room_id)
    
    # Check if meeting is at capacity
    if meeting.participant_count >= meeting.max_participants:
        messages.error(request, 'Meeting is at maximum capacity.')
        return redirect('meetings:meeting_detail', room_id=room_id)
    
    # Create or get attendance record
    attendance, created = MeetingAttendance.objects.get_or_create(
        meeting=meeting,
        user=request.user,
        defaults={
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )
    
    # If user already joined and left, mark as rejoined
    if attendance.left_at:
        attendance.left_at = None
        attendance.save()
    
    context = {
        'meeting': meeting,
        'attendance': attendance,
        'is_host': meeting.host == request.user,
    }
    
    return render(request, 'meetings/join_meeting.html', context)


@login_required
@require_http_methods(["POST"])
def leave_meeting(request, room_id):
    """Leave a meeting"""
    meeting = get_object_or_404(MeetingRoom, room_id=room_id)
    
    try:
        attendance = MeetingAttendance.objects.get(
            meeting=meeting,
            user=request.user
        )
        attendance.leave_meeting()
        return JsonResponse({'success': 'Left meeting successfully'})
    except MeetingAttendance.DoesNotExist:
        return JsonResponse({'error': 'Not in meeting'}, status=400)


@login_required
@require_http_methods(["POST"])
def start_meeting(request, room_id):
    """Start a meeting (host only)"""
    meeting = get_object_or_404(MeetingRoom, room_id=room_id, host=request.user)
    
    if meeting.status != 'PENDING':
        return JsonResponse({'error': 'Meeting already started or ended'}, status=400)
    
    meeting.start_meeting()
    return JsonResponse({'success': 'Meeting started'})


@login_required
@require_http_methods(["POST"])
def end_meeting(request, room_id):
    """End a meeting (host only)"""
    meeting = get_object_or_404(MeetingRoom, room_id=room_id, host=request.user)
    
    if meeting.status != 'ACTIVE':
        return JsonResponse({'error': 'Meeting is not active'}, status=400)
    
    meeting.end_meeting()
    return JsonResponse({'success': 'Meeting ended'})


@login_required
def invite_users(request, room_id):
    """Invite users to a meeting"""
    meeting = get_object_or_404(MeetingRoom, room_id=room_id, host=request.user)
    
    if request.method == 'POST':
        form = MeetingInvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.meeting = meeting
            invitation.invited_by = request.user
            invitation.save()
            
            messages.success(request, f'Invitation sent to {invitation.invited_user.username}')
            return redirect('meetings:meeting_detail', room_id=room_id)
    else:
        form = MeetingInvitationForm()
    
    context = {
        'meeting': meeting,
        'form': form,
    }
    
    return render(request, 'meetings/invite_users.html', context)


@login_required
@require_http_methods(["POST"])
def respond_to_invitation(request, invitation_id):
    """Respond to a meeting invitation"""
    invitation = get_object_or_404(
        MeetingInvitation,
        id=invitation_id,
        invited_user=request.user
    )
    
    response = request.POST.get('response')
    
    if response == 'accept':
        invitation.accept()
        return JsonResponse({'success': 'Invitation accepted'})
    elif response == 'decline':
        invitation.decline()
        return JsonResponse({'success': 'Invitation declined'})
    else:
        return JsonResponse({'error': 'Invalid response'}, status=400)


@login_required
def my_invitations(request):
    """View user's meeting invitations"""
    invitations = MeetingInvitation.objects.filter(
        invited_user=request.user
    ).order_by('-sent_at')
    
    # Separate pending and responded invitations
    pending = invitations.filter(response='PENDING')
    responded = invitations.exclude(response='PENDING')
    
    context = {
        'pending_invitations': pending,
        'responded_invitations': responded,
    }
    
    return render(request, 'meetings/my_invitations.html', context)


@login_required
def meeting_recordings(request, room_id):
    """View recordings for a meeting"""
    meeting = get_object_or_404(MeetingRoom, room_id=room_id)
    
    # Check access permissions
    can_access = (
        meeting.host == request.user or
        meeting.invitations.filter(invited_user=request.user, response='ACCEPTED').exists()
    )
    
    if not can_access:
        messages.error(request, 'You do not have permission to access these recordings.')
        return redirect('meetings:meeting_list')
    
    recordings = meeting.recordings.all()
    
    context = {
        'meeting': meeting,
        'recordings': recordings,
    }
    
    return render(request, 'meetings/recordings.html', context)


@login_required
def meeting_attendance(request, room_id):
    """View attendance for a meeting (host only)"""
    meeting = get_object_or_404(MeetingRoom, room_id=room_id, host=request.user)
    
    attendances = meeting.attendances.all().order_by('-joined_at')
    
    context = {
        'meeting': meeting,
        'attendances': attendances,
    }
    
    return render(request, 'meetings/attendance.html', context)