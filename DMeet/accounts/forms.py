from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import User, UserProfile, ConnectionRequest

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    """User registration form"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=User.USER_ROLES, initial='USER')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
            UserProfile.objects.create(user=user)
        
        return user


class UserProfileForm(forms.ModelForm):
    """User profile update form"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio', 'avatar', 'location', 'phone', 'date_of_birth']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class ConnectionRequestForm(forms.ModelForm):
    """Connection request form"""
    class Meta:
        model = ConnectionRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional message...'})
        }