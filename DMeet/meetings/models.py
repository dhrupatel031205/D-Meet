from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import secrets
import string

User = get_user_model()


class MeetingRoom(models.Model):
    """Model for video meeting rooms"""
    PROVIDER_CHOICES = [
        ('daily', 'Daily.co'),
        ('zoom', 'Zoom'),
        ('agora', 'Agora'),
        ('jitsi', 'Jitsi'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('ENDED', 'Ended'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Basic info
    room_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Meeting details
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='daily')
    meeting_url = models.URLField(blank=True)
    meeting_id = models.CharField(max_length=100, blank=True)
    meeting_password = models.CharField(max_length=50, blank=True)
    
    # Access control
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_meetings')
    is_password_protected = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(default=50)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_start']
    
    def __str__(self):
        return f"{self.name} - {self.scheduled_start}"
    
    def save(self, *args, **kwargs):
        if not self.meeting_password:
            self.meeting_password = self.generate_password()
        super().save(*args, **kwargs)
    
    def generate_password(self):
        """Generate a random meeting password"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(8))
    
    @property
    def is_live(self):
        """Check if the meeting is currently live"""
        now = timezone.now()
        return (self.status == 'ACTIVE' and 
                self.scheduled_start <= now <= self.scheduled_end)
    
    @property
    def can_join(self):
        """Check if users can join the meeting"""
        now = timezone.now()
        return (self.status == 'ACTIVE' and 
                self.scheduled_start <= now <= self.scheduled_end)
    
    @property
    def participant_count(self):
        """Get current participant count"""
        return self.attendances.filter(left_at__isnull=True).count()
    
    def start_meeting(self):
        """Start the meeting"""
        self.status = 'ACTIVE'
        self.actual_start = timezone.now()
        self.save()
    
    def end_meeting(self):
        """End the meeting"""
        self.status = 'ENDED'
        self.actual_end = timezone.now()
        self.save()
        
        # End all active attendances
        self.attendances.filter(left_at__isnull=True).update(left_at=timezone.now())


class MeetingAttendance(models.Model):
    """Model to track meeting attendance"""
    meeting = models.ForeignKey(MeetingRoom, on_delete=models.CASCADE, related_name='attendances')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_attendances')
    
    # Attendance tracking
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    
    # Connection info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['meeting', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.meeting.name}"
    
    def leave_meeting(self):
        """Mark user as having left the meeting"""
        if not self.left_at:
            self.left_at = timezone.now()
            self.duration_minutes = int((self.left_at - self.joined_at).total_seconds() / 60)
            self.save()
    
    @property
    def is_active(self):
        """Check if user is currently in the meeting"""
        return self.left_at is None


class MeetingInvitation(models.Model):
    """Model for meeting invitations"""
    meeting = models.ForeignKey(MeetingRoom, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    
    # Invitation details
    message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    # Response tracking
    responded_at = models.DateTimeField(null=True, blank=True)
    response = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined'),
    ], default='PENDING')
    
    class Meta:
        unique_together = ['meeting', 'invited_user']
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.invited_user.username} invited to {self.meeting.name}"
    
    def accept(self):
        """Accept the invitation"""
        self.response = 'ACCEPTED'
        self.responded_at = timezone.now()
        self.save()
    
    def decline(self):
        """Decline the invitation"""
        self.response = 'DECLINED'
        self.responded_at = timezone.now()
        self.save()


class MeetingRecording(models.Model):
    """Model for meeting recordings"""
    meeting = models.ForeignKey(MeetingRoom, on_delete=models.CASCADE, related_name='recordings')
    
    # Recording details
    title = models.CharField(max_length=200)
    file_url = models.URLField(blank=True)
    file_size = models.BigIntegerField(default=0)  # in bytes
    duration_seconds = models.PositiveIntegerField(default=0)
    
    # Access control
    is_public = models.BooleanField(default=False)
    password_protected = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recording: {self.title}"
    
    @property
    def duration_formatted(self):
        """Get formatted duration"""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"


class MeetingMessage(models.Model):
    """Model for meeting chat messages"""
    meeting = models.ForeignKey(MeetingRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_messages')
    
    # Message content
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=[
        ('TEXT', 'Text'),
        ('SYSTEM', 'System'),
        ('FILE', 'File'),
    ], default='TEXT')
    
    # Metadata
    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['sent_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"