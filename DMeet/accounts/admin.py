from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, ConnectionRequest, UserConnection


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_verified', 'created_at']
    list_filter = ['role', 'is_verified', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('DMeeet Info', {
            'fields': ('role', 'bio', 'avatar', 'location', 'interests', 'phone', 'date_of_birth', 'is_verified')
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user__role']
    search_fields = ['user__username']


@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'accepted', 'created_at']
    list_filter = ['accepted', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']


@admin.register(UserConnection)
class UserConnectionAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'created_at']
    search_fields = ['user1__username', 'user2__username']