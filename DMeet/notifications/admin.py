from django.contrib import admin
from .models import Notification, EmailTemplate, EmailLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'recipient__username', 'message']
    readonly_fields = ['created_at', 'read_at']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'subject']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['subject', 'recipient', 'is_sent', 'sent_at', 'created_at']
    list_filter = ['is_sent', 'sent_at', 'created_at']
    search_fields = ['subject', 'recipient']
    readonly_fields = ['created_at', 'sent_at']