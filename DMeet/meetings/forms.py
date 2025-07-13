from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import MeetingRoom, MeetingInvitation

User = get_user_model()


class MeetingRoomForm(forms.ModelForm):
    """Form for creating/editing meeting rooms"""
    
    class Meta:
        model = MeetingRoom
        fields = [
            'name', 'description', 'provider', 'scheduled_start', 'scheduled_end',
            'is_password_protected', 'is_public', 'max_participants'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'scheduled_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'scheduled_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('scheduled_start')
        end_time = cleaned_data.get('scheduled_end')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("End time must be after start time.")
            
            if start_time <= timezone.now():
                raise forms.ValidationError("Start time must be in the future.")
        
        return cleaned_data


class MeetingInvitationForm(forms.ModelForm):
    """Form for inviting users to meetings"""
    
    class Meta:
        model = MeetingInvitation
        fields = ['invited_user', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional invitation message...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invited_user'].queryset = User.objects.filter(is_active=True)
        self.fields['invited_user'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Select user to invite...'
        })


class MeetingPasswordForm(forms.Form):
    """Form for entering meeting password"""
    password = forms.CharField(
        max_length=50,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter meeting password...'
        })
    )