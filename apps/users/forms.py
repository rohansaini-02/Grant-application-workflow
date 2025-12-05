"""
Forms for user management.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    """Form for new user registration with role selection."""
    
    ROLE_CHOICES = [
        ('APPLICANT', 'Applicant'),
        ('REVIEWER', 'Reviewer'),
        ('ADMIN', 'Admin'),
    ]
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    organization = forms.CharField(required=False, help_text="Your university or institution")
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, label="Register as")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'organization', 'role')


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile information."""
    
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    organization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization'})
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell us about yourself...', 'rows': 4})
    )
    expertise_tags_input = forms.CharField(
        required=False,
        label='Expertise Areas',
        help_text='Enter comma-separated expertise areas (e.g., biology, chemistry, physics)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., biology, chemistry, physics'})
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'organization', 'bio')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate expertise_tags for reviewers
        if self.instance and self.instance.expertise_tags:
            self.fields['expertise_tags_input'].initial = ', '.join(self.instance.expertise_tags)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Process expertise_tags from comma-separated input
        expertise_input = self.cleaned_data.get('expertise_tags_input', '')
        if expertise_input:
            user.expertise_tags = [tag.strip() for tag in expertise_input.split(',') if tag.strip()]
        else:
            user.expertise_tags = []
        if commit:
            user.save()
        return user
