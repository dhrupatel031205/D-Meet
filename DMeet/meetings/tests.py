from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import MeetingRoom, MeetingAttendance, MeetingInvitation
from .providers import get_meeting_provider

User = get_user_model()


class MeetingRoomModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.meeting = MeetingRoom.objects.create(
            name='Test Meeting',
            host=self.user,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            provider='jitsi'
        )
    
    def test_meeting_creation(self):
        self.assertEqual(self.meeting.name, 'Test Meeting')
        self.assertEqual(self.meeting.host, self.user)
        self.assertEqual(self.meeting.status, 'PENDING')
        self.assertTrue(self.meeting.meeting_password)
    
    def test_meeting_properties(self):
        self.assertFalse(self.meeting.is_live)
        self.assertFalse(self.meeting.can_join)
        self.assertEqual(self.meeting.participant_count, 0)
    
    def test_start_meeting(self):
        self.meeting.start_meeting()
        self.assertEqual(self.meeting.status, 'ACTIVE')
        self.assertIsNotNone(self.meeting.actual_start)
    
    def test_end_meeting(self):
        self.meeting.start_meeting()
        self.meeting.end_meeting()
        self.assertEqual(self.meeting.status, 'ENDED')
        self.assertIsNotNone(self.meeting.actual_end)


class MeetingAttendanceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.meeting = MeetingRoom.objects.create(
            name='Test Meeting',
            host=self.user,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            provider='jitsi'
        )
        
        self.attendance = MeetingAttendance.objects.create(
            meeting=self.meeting,
            user=self.user
        )
    
    def test_attendance_creation(self):
        self.assertEqual(self.attendance.meeting, self.meeting)
        self.assertEqual(self.attendance.user, self.user)
        self.assertTrue(self.attendance.is_active)
    
    def test_leave_meeting(self):
        self.attendance.leave_meeting()
        self.assertFalse(self.attendance.is_active)
        self.assertIsNotNone(self.attendance.left_at)
        self.assertGreater(self.attendance.duration_minutes, 0)


class MeetingInvitationTest(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            username='host',
            email='host@example.com',
            password='testpass123'
        )
        
        self.invitee = User.objects.create_user(
            username='invitee',
            email='invitee@example.com',
            password='testpass123'
        )
        
        self.meeting = MeetingRoom.objects.create(
            name='Test Meeting',
            host=self.host,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            provider='jitsi'
        )
        
        self.invitation = MeetingInvitation.objects.create(
            meeting=self.meeting,
            invited_by=self.host,
            invited_user=self.invitee,
            message='Join our meeting!'
        )
    
    def test_invitation_creation(self):
        self.assertEqual(self.invitation.meeting, self.meeting)
        self.assertEqual(self.invitation.invited_by, self.host)
        self.assertEqual(self.invitation.invited_user, self.invitee)
        self.assertEqual(self.invitation.response, 'PENDING')
    
    def test_accept_invitation(self):
        self.invitation.accept()
        self.assertEqual(self.invitation.response, 'ACCEPTED')
        self.assertIsNotNone(self.invitation.responded_at)
    
    def test_decline_invitation(self):
        self.invitation.decline()
        self.assertEqual(self.invitation.response, 'DECLINED')
        self.assertIsNotNone(self.invitation.responded_at)


class MeetingProviderTest(TestCase):
    def test_get_provider(self):
        provider = get_meeting_provider('jitsi')
        self.assertIsNotNone(provider)
        
        provider = get_meeting_provider('daily')
        self.assertIsNotNone(provider)
        
        provider = get_meeting_provider('unknown')
        self.assertIsNotNone(provider)  # Should fallback to Jitsi


class MeetingViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.meeting = MeetingRoom.objects.create(
            name='Test Meeting',
            host=self.user,
            scheduled_start=timezone.now() + timedelta(hours=1),
            scheduled_end=timezone.now() + timedelta(hours=2),
            provider='jitsi'
        )
    
    def test_meeting_list_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('meetings:meeting_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Meeting')
    
    def test_meeting_detail_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('meetings:meeting_detail', kwargs={'room_id': self.meeting.room_id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Meeting')
    
    def test_create_meeting_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('meetings:create_meeting'))
        self.assertEqual(response.status_code, 200)
        
        # Test POST
        start_time = timezone.now() + timedelta(hours=1)
        end_time = timezone.now() + timedelta(hours=2)
        
        response = self.client.post(reverse('meetings:create_meeting'), {
            'name': 'New Meeting',
            'description': 'Test description',
            'provider': 'jitsi',
            'scheduled_start': start_time.strftime('%Y-%m-%dT%H:%M'),
            'scheduled_end': end_time.strftime('%Y-%m-%dT%H:%M'),
            'max_participants': 50,
            'is_public': True,
            'is_password_protected': False,
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertTrue(MeetingRoom.objects.filter(name='New Meeting').exists())