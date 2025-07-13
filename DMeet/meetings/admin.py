from django.contrib import admin
from .models import MeetingRoom, MeetingAttendance, MeetingInvitation, MeetingRecording, MeetingMessage


@admin.register(MeetingRoom)
class MeetingRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'provider', 'status', 'scheduled_start', 'participant_count', 'created_at']
    list_filter = ['provider', 'status', 'is_public', 'is_password_protected', 'created_at']
    search_fields = ['name', 'host__username', 'meeting_id']
    readonly_fields = ['room_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'host', 'room_id')
        }),
        ('Meeting Settings', {
            'fields': ('provider', 'meeting_url', 'meeting_id', 'meeting_password')
        }),
        ('Access Control', {
            'fields': ('is_public', 'is_password_protected', 'max_participants')
        }),
        ('Scheduling', {
            'fields': ('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def participant_count(self, obj):
        return obj.participant_count
    participant_count.short_description = 'Participants'


@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'meeting', 'joined_at', 'left_at', 'duration_minutes', 'is_active']
    list_filter = ['joined_at', 'left_at']
    search_fields = ['user__username', 'meeting__name']
    readonly_fields = ['joined_at', 'duration_minutes']
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = 'Currently Active'


@admin.register(MeetingInvitation)
class MeetingInvitationAdmin(admin.ModelAdmin):
    list_display = ['invited_user', 'meeting', 'invited_by', 'response', 'sent_at', 'responded_at']
    list_filter = ['response', 'sent_at', 'responded_at']
    search_fields = ['invited_user__username', 'meeting__name', 'invited_by__username']
    readonly_fields = ['sent_at', 'responded_at']


@admin.register(MeetingRecording)
class MeetingRecordingAdmin(admin.ModelAdmin):
    list_display = ['title', 'meeting', 'duration_formatted', 'file_size', 'is_public', 'created_at']
    list_filter = ['is_public', 'password_protected', 'created_at']
    search_fields = ['title', 'meeting__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MeetingMessage)
class MeetingMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'meeting', 'message_type', 'sent_at', 'message_preview']
    list_filter = ['message_type', 'sent_at']
    search_fields = ['user__username', 'meeting__name', 'message']
    readonly_fields = ['sent_at', 'edited_at']
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message Preview'