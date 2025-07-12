from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse


class EventCategory(models.Model):
    """Categories for events like Music, Sports, Technology, etc."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Event Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Profile(models.Model):
    """Extended user profile with location and interests"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.PointField(help_text="User's location for event discovery", null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    interests = models.ManyToManyField(EventCategory, blank=True, help_text="Categories user is interested in")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_absolute_url(self):
        return reverse('profile', kwargs={'pk': self.pk})


class Event(models.Model):
    """Main event model with location and details"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.PointField(help_text="Event location coordinates")
    address = models.CharField(max_length=300, help_text="Human readable address")
    category = models.ForeignKey(EventCategory, on_delete=models.CASCADE)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_attendees = models.PositiveIntegerField(default=50)
    
    approved = models.BooleanField(default=False, help_text="Admin approval required")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return self.title

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")
        
        if self.start_time <= timezone.now():
            raise ValidationError("Event start time must be in the future.")

    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'pk': self.pk})

    @property
    def is_past(self):
        return self.end_time < timezone.now()

    @property
    def is_upcoming(self):
        return self.start_time > timezone.now()

    @property
    def is_happening_now(self):
        return self.start_time <= timezone.now() <= self.end_time

    @property
    def current_attendees(self):
        return self.rsvps.count()

    @property
    def spots_remaining(self):
        return max(0, self.max_attendees - self.current_attendees)

    @property
    def is_full(self):
        return self.current_attendees >= self.max_attendees

    def can_user_rsvp(self, user):
        """Check if user can RSVP to this event"""
        if not user.is_authenticated:
            return False
        if self.is_past:
            return False
        if self.is_full:
            return False
        if RSVP.objects.filter(user=user, event=self).exists():
            return False
        return True


class RSVP(models.Model):
    """User RSVP to events"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rsvps')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    rsvp_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-rsvp_time']

    def __str__(self):
        return f"{self.user.username} -> {self.event.title}"


class Feedback(models.Model):
    """User feedback on events after attending"""
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.event.title}: {self.rating}/5"

    def clean(self):
        # Check if user RSVPed to the event
        if not RSVP.objects.filter(user=self.user, event=self.event).exists():
            raise ValidationError("You can only provide feedback for events you RSVPed to.")
        
        # Check if event has ended
        if not self.event.is_past:
            raise ValidationError("You can only provide feedback after the event has ended.")


class Connection(models.Model):
    """User connections made at events (max 3 per user per event)"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_made')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_received')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='connections')
    created_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(max_length=300, blank=True, help_text="Optional message when connecting")

    class Meta:
        unique_together = ['from_user', 'to_user', 'event']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user.username} connected with {self.to_user.username} at {self.event.title}"

    def clean(self):
        # Check if both users RSVPed to the event
        if not RSVP.objects.filter(user=self.from_user, event=self.event).exists():
            raise ValidationError("You can only connect with people at events you RSVPed to.")
        
        if not RSVP.objects.filter(user=self.to_user, event=self.event).exists():
            raise ValidationError("You can only connect with people who also RSVPed to this event.")
        
        # Check if event has ended
        if not self.event.is_past:
            raise ValidationError("You can only make connections after the event has ended.")
        
        # Check connection limit (max 3 per user per event)
        existing_connections = Connection.objects.filter(
            from_user=self.from_user, 
            event=self.event
        ).count()
        
        if existing_connections >= 3 and not self.pk:  # Don't count current instance if updating
            raise ValidationError("You can only make up to 3 connections per event.")

    @classmethod
    def get_user_connections_for_event(cls, user, event):
        """Get all connections a user made for a specific event"""
        return cls.objects.filter(from_user=user, event=event)

    @classmethod
    def can_user_connect(cls, from_user, to_user, event):
        """Check if user can connect with another user at an event"""
        # Check if both users attended the event
        if not RSVP.objects.filter(user=from_user, event=event).exists():
            return False, "You must have RSVPed to this event to make connections."
        
        if not RSVP.objects.filter(user=to_user, event=event).exists():
            return False, "The other user must have also RSVPed to this event."
        
        # Check if event has ended
        if not event.is_past:
            return False, "You can only make connections after the event has ended."
        
        # Check if connection already exists
        if cls.objects.filter(from_user=from_user, to_user=to_user, event=event).exists():
            return False, "You have already connected with this user for this event."
        
        # Check connection limit
        existing_connections = cls.objects.filter(from_user=from_user, event=event).count()
        if existing_connections >= 3:
            return False, "You have reached the maximum of 3 connections for this event."
        
        return True, "Connection allowed."


# Signal to create profile when user is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
