from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()

class SignupForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, required=True, label="Full Name")
    username = forms.CharField(max_length=150, required=True, label="Username")
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(max_length=20, required=True, label="Phone Number")
    organisation_name = forms.CharField(max_length=255, required=False, label="Organisation Name", help_text="Leave blank if you are an external user")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ("username", "email")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")

        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', "A user with that email already exists.")
            
        username = cleaned_data.get("username")
        if username and User.objects.filter(username=username).exists():
            self.add_error('username', "A user with that username already exists.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        full_name = self.cleaned_data.get("full_name", "")
        parts = full_name.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.email = self.cleaned_data.get("email")
        user.username = self.cleaned_data.get("username")

        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class CustomLoginForm(AuthenticationForm):
    """
    Standard Auth Form but ensuring the label is explicitly 'Username:'
    """
    username = forms.CharField(label="Username:")
    password = forms.CharField(label="Password:", widget=forms.PasswordInput)

