from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import User, UserProfile, ConnectionRequest, UserConnection
from .forms import UserRegistrationForm, UserProfileForm, ConnectionRequestForm


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard:user_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_page = request.GET.get('next', 'dashboard:user_dashboard')
            return redirect(next_page)
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


@login_required
def profile_view(request, username=None):
    """User profile view"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    context = {
        'user': user,
        'is_own_profile': user == request.user,
        'can_connect': user != request.user,
    }
    return render(request, 'accounts/profile.html', context)


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile"""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user


@login_required
@require_http_methods(["POST"])
def send_connection_request(request, user_id):
    """Send connection request to another user"""
    to_user = get_object_or_404(User, id=user_id)
    
    if to_user == request.user:
        return JsonResponse({'error': 'Cannot connect to yourself'}, status=400)
    
    # Check if connection already exists
    existing_connection = UserConnection.objects.filter(
        user1=request.user, user2=to_user
    ).exists() or UserConnection.objects.filter(
        user1=to_user, user2=request.user
    ).exists()
    
    if existing_connection:
        return JsonResponse({'error': 'Already connected'}, status=400)
    
    # Check if request already exists
    existing_request = ConnectionRequest.objects.filter(
        from_user=request.user, to_user=to_user
    ).exists()
    
    if existing_request:
        return JsonResponse({'error': 'Connection request already sent'}, status=400)
    
    # Create connection request
    ConnectionRequest.objects.create(
        from_user=request.user,
        to_user=to_user,
        message=request.POST.get('message', '')
    )
    
    return JsonResponse({'success': 'Connection request sent'})


@login_required
@require_http_methods(["POST"])
def accept_connection_request(request, request_id):
    """Accept a connection request"""
    connection_request = get_object_or_404(
        ConnectionRequest, 
        id=request_id, 
        to_user=request.user
    )
    
    if connection_request.accepted:
        return JsonResponse({'error': 'Request already accepted'}, status=400)
    
    # Accept the request
    connection_request.accepted = True
    connection_request.accepted_at = timezone.now()
    connection_request.save()
    
    # Create the connection
    UserConnection.objects.create(
        user1=connection_request.from_user,
        user2=connection_request.to_user
    )
    
    return JsonResponse({'success': 'Connection request accepted'})


@login_required
@require_http_methods(["POST"])
def reject_connection_request(request, request_id):
    """Reject a connection request"""
    connection_request = get_object_or_404(
        ConnectionRequest, 
        id=request_id, 
        to_user=request.user
    )
    
    connection_request.delete()
    return JsonResponse({'success': 'Connection request rejected'})


@login_required
def my_connections(request):
    """View user's connections"""
    connections = UserConnection.objects.filter(
        user1=request.user
    ).union(
        UserConnection.objects.filter(user2=request.user)
    ).order_by('-created_at')
    
    return render(request, 'accounts/connections.html', {
        'connections': connections
    })


@login_required
def connection_requests(request):
    """View incoming connection requests"""
    requests = ConnectionRequest.objects.filter(
        to_user=request.user, 
        accepted=False
    ).order_by('-created_at')
    
    return render(request, 'accounts/connection_requests.html', {
        'requests': requests
    })