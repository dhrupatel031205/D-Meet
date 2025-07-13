from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Custom user model with roles and additional fields"""
    USER_ROLES = (
        ('USER', 'User'),
        ('ORGANIZER', 'Organizer'),
        ('ADMIN', 'Admin'),
    )
    
    role = models.CharField(max_length=20, choices=USER_ROLES, default='USER')
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    interests = models.JSONField(default=list, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_organizer(self):
        return self.role in ['ORGANIZER', 'ADMIN']
    
    @property
    def is_admin(self):
        return self.role == 'ADMIN'


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    notification_preferences = models.JSONField(default=dict)
    privacy_settings = models.JSONField(default=dict)
    social_links = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class ConnectionRequest(models.Model):
    """Model for user connection requests"""
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    message = models.TextField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['from_user', 'to_user']
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}"


class UserConnection(models.Model):
    """Model for established user connections"""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
    
    def __str__(self):
        return f"{self.user1.username} <-> {self.user2.username}"