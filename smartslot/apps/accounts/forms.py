from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from apps.core.models import Organisation

User = get_user_model()


class SignupForm(forms.Form):
    first_name    = forms.CharField(max_length=100)
    last_name     = forms.CharField(max_length=100)
    username      = forms.CharField(max_length=150)
    email         = forms.EmailField()
    phone         = forms.CharField(max_length=20, required=False)
    password      = forms.CharField(widget=forms.PasswordInput)
    password2     = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')
    role          = forms.ChoiceField(choices=[('Employee', 'Employee'), ('External', 'External')])
    organisation  = forms.ModelChoiceField(
        queryset=Organisation.objects.all(),
        required=False,
        empty_label='Select your organisation',
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            self.add_error('password2', 'Passwords do not match.')
        if User.objects.filter(username=cleaned.get('username')).exists():
            self.add_error('username', 'Username already taken.')
        if User.objects.filter(email=cleaned.get('email')).exists():
            self.add_error('email', 'Email already registered.')
        if cleaned.get('role') == 'Employee' and not cleaned.get('organisation'):
            self.add_error('organisation', 'Please select your organisation.')
        return cleaned

    def save(self):
        d = self.cleaned_data
        user = User(
            username=d['username'],
            email=d['email'],
            first_name=d['first_name'],
            last_name=d['last_name'],
            role=d['role'],
        )
        user.set_password(d['password'])
        user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
