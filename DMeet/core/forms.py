from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, HTML
from crispy_forms.bootstrap import PrependedText, AppendedText
from .models import Event, EventCategory, Profile, Feedback, Connection, RSVP


class CustomUserCreationForm(UserCreationForm):
    """Extended user registration form"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """User profile form with location and interests"""
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Profile
        fields = ['bio', 'interests']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'interests': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Profile Information',
                'bio',
                'interests',
                HTML('<div class="form-group"><label>Location</label><div id="profile-map" style="height: 300px;"></div><small class="form-text text-muted">Click on the map to set your location</small></div>'),
                'latitude',
                'longitude',
            ),
            Submit('submit', 'Save Profile', css_class='btn btn-primary')
        )

    def save(self, commit=True):
        profile = super().save(commit=False)
        latitude = self.cleaned_data.get('latitude')
        longitude = self.cleaned_data.get('longitude')
        
        if latitude and longitude:
            profile.location = Point(longitude, latitude)
        
        if commit:
            profile.save()
            self.save_m2m()
        return profile


class EventForm(forms.ModelForm):
    """Event creation/editing form"""
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=True)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'address', 'start_time', 'end_time', 'max_attendees']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Event Details',
                'title',
                'description',
                Row(
                    Column('category', css_class='form-group col-md-6 mb-0'),
                    Column('max_attendees', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Location',
                'address',
                HTML('<div class="form-group"><label>Event Location</label><div id="event-map" style="height: 300px;"></div><small class="form-text text-muted">Click on the map to set event location</small></div>'),
                'latitude',
                'longitude',
            ),
            Fieldset(
                'Schedule',
                Row(
                    Column('start_time', css_class='form-group col-md-6 mb-0'),
                    Column('end_time', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Submit('submit', 'Create Event', css_class='btn btn-primary')
        )

    def save(self, commit=True):
        event = super().save(commit=False)
        latitude = self.cleaned_data['latitude']
        longitude = self.cleaned_data['longitude']
        event.location = Point(longitude, latitude)
        
        if commit:
            event.save()
        return event


class EventFilterForm(forms.Form):
    """Form for filtering events on homepage"""
    DISTANCE_CHOICES = [
        ('', 'Any Distance'),
        ('5', 'Within 5km'),
        ('10', 'Within 10km'),
        ('20', 'Within 20km'),
        ('50', 'Within 50km'),
    ]

    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.all(),
        required=False,
        empty_label="All Categories"
    )
    distance = forms.ChoiceField(
        choices=DISTANCE_CHOICES,
        required=False
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('category', css_class='form-group col-md-3 mb-0'),
                Column('distance', css_class='form-group col-md-3 mb-0'),
                Column('date_from', css_class='form-group col-md-3 mb-0'),
                Column('date_to', css_class='form-group col-md-3 mb-0'),
            ),
            Submit('filter', 'Filter Events', css_class='btn btn-outline-primary')
        )


class FeedbackForm(forms.ModelForm):
    """Feedback form for events"""
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience at this event...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Your Feedback',
                'rating',
                'comment',
            ),
            Submit('submit', 'Submit Feedback', css_class='btn btn-primary')
        )


class ConnectionForm(forms.ModelForm):
    """Form for making connections with other event attendees"""
    class Meta:
        model = Connection
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Send a message with your connection request (optional)...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Connect',
                'message',
            ),
            Submit('submit', 'Send Connection Request', css_class='btn btn-primary')
        )


class RSVPForm(forms.Form):
    """Simple form for RSVP actions"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Submit('rsvp', 'RSVP to Event', css_class='btn btn-success'),
        )


class SearchForm(forms.Form):
    """Search form for events"""
    query = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search events...',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-10 mb-0'),
                Column(Submit('search', 'Search', css_class='btn btn-primary'), css_class='form-group col-md-2 mb-0'),
            )
        )