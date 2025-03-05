from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Event

CustomUser = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

class EditProfileForm(forms.ModelForm):
    """
    Form for updating user profile information.
    Assumes your CustomUser model includes profile_picture and phone_number fields.
    """
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'profile_picture', 'phone_number')

class EventForm(forms.ModelForm):
    # Override the date field to use an HTML5 datetime-local input.
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']  # Format expected from the widget.
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'category', 'image']
