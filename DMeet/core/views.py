from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
import json

from .models import Event, EventCategory, RSVP, Feedback, Connection, Profile
from .forms import (
    EventForm, EventFilterForm, FeedbackForm, ConnectionForm, SearchForm
)

User = get_user_model()


def home(request):
    """Homepage with event listing, filtering, and map"""
    events = Event.objects.filter(approved=True, start_time__gte=timezone.now())
    form = EventFilterForm(request.GET)
    
    # Apply filters
    if form.is_valid():
        category = form.cleaned_data.get('category')
        distance = form.cleaned_data.get('distance')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if category:
            events = events.filter(category=category)
        
        if date_from:
            events = events.filter(start_time__date__gte=date_from)
        
        if date_to:
            events = events.filter(start_time__date__lte=date_to)
        
        # Distance filtering (disabled temporarily until GeoDjango is configured)
        # if distance and request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.location:
        #     distance_km = int(distance)
        #     user_location = request.user.profile.location
        #     events = events.filter(location__distance_lte=(user_location, D(km=distance_km)))
    
    # Search functionality
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        if query:
            events = events.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(address__icontains=query)
            )
    
    # Pagination
    paginator = Paginator(events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get event data for map (disabled temporarily until GeoDjango is configured)
    events_for_map = []
    # for event in events[:50]:  # Limit for performance
    #     events_for_map.append({
    #         'id': event.id,
    #         'title': event.title,
    #         'lat': event.location.y,
    #         'lng': event.location.x,
    #         'start_time': event.start_time.isoformat(),
    #         'category': event.category.name,
    #         'url': event.get_absolute_url()
    #     })
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'search_form': search_form,
        'events_for_map': json.dumps(events_for_map),
        'categories': EventCategory.objects.all(),
    }
    return render(request, 'core/home.html', context)


def event_detail(request, pk):
    """Event detail page with RSVP, feedback, and connections"""
    event = get_object_or_404(Event, pk=pk, approved=True)
    user_rsvped = False
    user_feedback = None
    user_connections = []
    attendees = []
    can_give_feedback = False
    
    if request.user.is_authenticated:
        user_rsvped = RSVP.objects.filter(user=request.user, event=event).exists()
        
        # Check if user can give feedback
        if user_rsvped and event.is_past:
            can_give_feedback = True
            try:
                user_feedback = Feedback.objects.get(user=request.user, event=event)
            except Feedback.DoesNotExist:
                pass
        
        # Get user's connections for this event
        user_connections = Connection.objects.filter(from_user=request.user, event=event)
        
        # Get attendees for potential connections (if event is past)
        if event.is_past and user_rsvped:
            attendees = RSVP.objects.filter(event=event).exclude(user=request.user)
    
    # Get all feedback for this event
    feedbacks = Feedback.objects.filter(event=event).order_by('-created_at')
    
    context = {
        'event': event,
        'user_rsvped': user_rsvped,
        'user_feedback': user_feedback,
        'user_connections': user_connections,
        'attendees': attendees,
        'can_give_feedback': can_give_feedback,
        'feedbacks': feedbacks,
        'event_json': json.dumps({
            'lat': event.location.y,
            'lng': event.location.x,
            'title': event.title,
            'address': event.address
        })
    }
    return render(request, 'core/event_detail.html', context)


@login_required
def rsvp_event(request, pk):
    """RSVP to an event"""
    event = get_object_or_404(Event, pk=pk, approved=True)
    
    if event.can_user_rsvp(request.user):
        RSVP.objects.create(user=request.user, event=event)
        messages.success(request, f'Successfully RSVPed to {event.title}!')
    else:
        messages.error(request, 'Unable to RSVP to this event.')
    
    return redirect('event_detail', pk=pk)


@login_required
def cancel_rsvp(request, pk):
    """Cancel RSVP to an event"""
    event = get_object_or_404(Event, pk=pk)
    
    try:
        rsvp = RSVP.objects.get(user=request.user, event=event)
        rsvp.delete()
        messages.success(request, f'RSVP cancelled for {event.title}')
    except RSVP.DoesNotExist:
        messages.error(request, 'No RSVP found to cancel.')
    
    return redirect('event_detail', pk=pk)


class EventCreateView(LoginRequiredMixin, CreateView):
    """Create new event"""
    model = Event
    form_class = EventForm
    template_name = 'core/event_form.html'
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, 'Event created! It will be visible after admin approval.')
        return super().form_valid(form)


@login_required
def give_feedback(request, pk):
    """Give feedback for an event"""
    event = get_object_or_404(Event, pk=pk)
    
    # Check if user can give feedback
    if not RSVP.objects.filter(user=request.user, event=event).exists():
        messages.error(request, 'You can only give feedback for events you RSVPed to.')
        return redirect('event_detail', pk=pk)
    
    if not event.is_past:
        messages.error(request, 'You can only give feedback after the event has ended.')
        return redirect('event_detail', pk=pk)
    
    # Check if feedback already exists
    feedback, created = Feedback.objects.get_or_create(
        user=request.user, 
        event=event,
        defaults={'rating': 3}  # Default rating
    )
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            form.save()
            if created:
                messages.success(request, 'Thank you for your feedback!')
            else:
                messages.success(request, 'Your feedback has been updated!')
            return redirect('event_detail', pk=pk)
    else:
        form = FeedbackForm(instance=feedback)
    
    context = {
        'form': form,
        'event': event,
        'feedback': feedback
    }
    return render(request, 'core/feedback_form.html', context)


@login_required
def make_connection(request, event_pk, user_pk):
    """Make a connection with another attendee"""
    event = get_object_or_404(Event, pk=event_pk)
    to_user = get_object_or_404(User, pk=user_pk)
    
    # Validate connection
    can_connect, message = Connection.can_user_connect(request.user, to_user, event)
    
    if not can_connect:
        messages.error(request, message)
        return redirect('event_detail', pk=event_pk)
    
    if request.method == 'POST':
        form = ConnectionForm(request.POST)
        if form.is_valid():
            connection = form.save(commit=False)
            connection.from_user = request.user
            connection.to_user = to_user
            connection.event = event
            connection.save()
            messages.success(request, f'Connection request sent to {to_user.get_full_name() or to_user.username}!')
            return redirect('event_detail', pk=event_pk)
    else:
        form = ConnectionForm()
    
    context = {
        'form': form,
        'event': event,
        'to_user': to_user
    }
    return render(request, 'core/connection_form.html', context)


@login_required
def dashboard(request):
    """User dashboard with RSVPs, hosted events, feedback, and connections"""
    # Upcoming RSVPs
    upcoming_rsvps = RSVP.objects.filter(
        user=request.user, 
        event__start_time__gte=timezone.now(),
        event__approved=True
    ).order_by('event__start_time')
    
    # Past events (for feedback)
    past_events = RSVP.objects.filter(
        user=request.user,
        event__end_time__lt=timezone.now(),
        event__approved=True
    ).order_by('-event__end_time')
    
    # Hosted events
    hosted_events = Event.objects.filter(organizer=request.user).order_by('-start_time')
    
    # User's connections
    connections_made = Connection.objects.filter(from_user=request.user).order_by('-created_at')
    connections_received = Connection.objects.filter(to_user=request.user).order_by('-created_at')
    
    # Feedback given
    feedbacks_given = Feedback.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'upcoming_rsvps': upcoming_rsvps,
        'past_events': past_events,
        'hosted_events': hosted_events,
        'connections_made': connections_made,
        'connections_received': connections_received,
        'feedbacks_given': feedbacks_given,
    }
    return render(request, 'core/dashboard.html', context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile"""
    model = Profile
    form_class = ProfileForm
    template_name = 'core/profile_form.html'
    success_url = reverse_lazy('dashboard')
    
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to DMeet!')
            return redirect('profile_update')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def map_view(request):
    """Dedicated map view showing all events"""
    events = Event.objects.filter(approved=True, start_time__gte=timezone.now())
    
    # Apply filters if provided
    form = EventFilterForm(request.GET)
    if form.is_valid():
        category = form.cleaned_data.get('category')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if category:
            events = events.filter(category=category)
        if date_from:
            events = events.filter(start_time__date__gte=date_from)
        if date_to:
            events = events.filter(start_time__date__lte=date_to)
    
    # Prepare event data for map
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'lat': event.location.y,
            'lng': event.location.x,
            'start_time': event.start_time.isoformat(),
            'category': event.category.name,
            'address': event.address,
            'organizer': event.organizer.get_full_name() or event.organizer.username,
            'attendees': event.current_attendees,
            'max_attendees': event.max_attendees,
            'url': event.get_absolute_url()
        })
    
    context = {
        'events_data': json.dumps(events_data),
        'form': form,
        'categories': EventCategory.objects.all(),
    }
    return render(request, 'core/map.html', context)


def about(request):
    """About page"""
    return render(request, 'core/about.html')


# Import User model for connection view
from django.contrib.auth.models import User
