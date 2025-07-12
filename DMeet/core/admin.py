from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, EventCategory, Event, RSVP, Feedback, Connection


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Event)
class EventAdmin(OSMGeoAdmin):
    list_display = ['title', 'organizer', 'category', 'start_time', 'approved', 'current_attendees', 'max_attendees']
    list_filter = ['approved', 'category', 'start_time', 'created_at']
    search_fields = ['title', 'description', 'organizer__username']
    readonly_fields = ['created_at', 'updated_at', 'current_attendees']
    ordering = ['-start_time']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'organizer', 'category')
        }),
        ('Location', {
            'fields': ('location', 'address')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time', 'max_attendees')
        }),
        ('Status', {
            'fields': ('approved', 'current_attendees')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_events', 'reject_events']
    
    def approve_events(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f'{updated} events were approved.')
    approve_events.short_description = "Approve selected events"
    
    def reject_events(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f'{updated} events were rejected.')
    reject_events.short_description = "Reject selected events"


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'rsvp_time']
    list_filter = ['rsvp_time', 'event__category']
    search_fields = ['user__username', 'event__title']
    ordering = ['-rsvp_time']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'rating', 'created_at']
    list_filter = ['rating', 'created_at', 'event__category']
    search_fields = ['user__username', 'event__title', 'comment']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'event', 'created_at']
    list_filter = ['created_at', 'event__category']
    search_fields = ['from_user__username', 'to_user__username', 'event__title']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(Profile)
class ProfileAdmin(OSMGeoAdmin):
    list_display = ['user', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    filter_horizontal = ['interests']
    ordering = ['-created_at']


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Customize admin site
admin.site.site_header = "DMeet Administration"
admin.site.site_title = "DMeet Admin"
admin.site.index_title = "Welcome to DMeet Administration"
