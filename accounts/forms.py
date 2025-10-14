
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import inlineformset_factory
from .models import CustomUser, Profile

# ------------------------ User Authentication Forms ----------------------------

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}) # note: this is an email NOT a username
    ) 
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'password')

class SignUpForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password1'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password2'})
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')

from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import CustomUser, Profile

# ------------------- User info form -------------------
class UserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'disabled': 'true'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

# ------------------- Profile info form -------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

# ------------------- Password change form -------------------
class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


GOAL_CHOICES = [
    ("productivity", "Productivity", "fa-solid fa-rocket"),
    ("personal_enrichment", "Personal Enrichment", "fa-solid fa-brain"),
    ("academic_success", "Academic Success", "fa-solid fa-graduation-cap"),
    ("vce_success", "VCE Success", "fa-solid fa-book-open"),
    ("selective_school_success", "Selective School Success", "fa-solid fa-school"),
    ("study_techniques", "Study Techniques", "fa-solid fa-lightbulb"),
    ("other", "Other", "fa-solid fa-pen"),
]

REFERRAL_CHOICES = [
    ("friend", "Friend", "fa-solid fa-user-friends"),
    ("facebook", "Facebook", "fa-brands fa-facebook"),
    ("tiktok", "TikTok", "fa-brands fa-tiktok"),
    ("youtube", "YouTube", "fa-brands fa-youtube"),
    ("search_engine", "Search Engine", "fa-solid fa-magnifying-glass"),
    ("advertisement", "Advertisement", "fa-solid fa-bullhorn"),
    ("flyer", "Flyer", "fa-solid fa-file-lines"),
    ("other", "Other", "fa-solid fa-pen"),
]



class OnboardingForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        label="What should we call you?",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'})
    )

    goals = forms.MultipleChoiceField(
        choices=[(value, label) for value, label, icon in GOAL_CHOICES],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    referral_source = forms.ChoiceField(
        choices=[(value, label) for value, label, icon in REFERRAL_CHOICES],
        widget=forms.RadioSelect,
        required=False
    )
    referral_other = forms.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ["username", "referral_source", "goals", "referral_other"]
