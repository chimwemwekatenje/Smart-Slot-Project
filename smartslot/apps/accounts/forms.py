from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from apps.core.models import (
    ApplicationResource,
    Organisation,
    OrganisationApplication,
)

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
        queryset=Organisation.objects.filter(is_approved=True),
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
            phone=d.get('phone') or '',
            organisation=d.get('organisation'),
        )
        user.set_password(d['password'])
        user.save()
        return user


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


class OrganisationRegistrationForm(forms.Form):
    RESOURCE_SLOTS = range(1, 11)
    MAX_IMAGE_SIZE_MB = 5
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']

    organisation_name = forms.CharField(max_length=255)
    contact_name = forms.CharField(max_length=255)
    contact_email = forms.EmailField()
    contact_phone = forms.CharField(max_length=30)
    address = forms.CharField(widget=forms.Textarea, required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)
    logo = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for index in self.RESOURCE_SLOTS:
            self.fields[f'resource_{index}_name'] = forms.CharField(
                max_length=255,
                required=index == 1,
            )
            self.fields[f'resource_{index}_category'] = forms.CharField(
                max_length=255,
                required=index == 1,
            )
            self.fields[f'resource_{index}_description'] = forms.CharField(
                widget=forms.Textarea,
                required=False,
            )
            self.fields[f'resource_{index}_price'] = forms.DecimalField(
                max_digits=10,
                decimal_places=2,
                min_value=0,
                required=False,
                initial=0,
            )
            self.fields[f'resource_{index}_image'] = forms.ImageField(
                required=False,
            )

    def clean_organisation_name(self):
        name = self.cleaned_data['organisation_name'].strip()
        if Organisation.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('This organisation already exists.')
        if OrganisationApplication.objects.exclude(
            status=OrganisationApplication.StatusChoices.REJECTED
        ).filter(organisation_name__iexact=name).exists():
            raise forms.ValidationError('This organisation already has an active application.')
        return name

    def clean(self):
        cleaned = super().clean()
        resource_count = 0
        for index in self.RESOURCE_SLOTS:
            name = cleaned.get(f'resource_{index}_name')
            category = cleaned.get(f'resource_{index}_category')
            description = cleaned.get(f'resource_{index}_description')
            price = cleaned.get(f'resource_{index}_price')
            image = cleaned.get(f'resource_{index}_image')
            has_any = any([name, category, description, price, image])

            if not has_any:
                continue

            resource_count += 1
            if not name:
                self.add_error(f'resource_{index}_name', 'Resource name is required.')
            if not category:
                self.add_error(f'resource_{index}_category', 'Category is required.')

            # Validate image file size and type
            if image:
                max_bytes = self.MAX_IMAGE_SIZE_MB * 1024 * 1024
                if image.size > max_bytes:
                    self.add_error(
                        f'resource_{index}_image',
                        f'Image must be under {self.MAX_IMAGE_SIZE_MB} MB (got {image.size / 1024 / 1024:.1f} MB).',
                    )
                if hasattr(image, 'content_type') and image.content_type not in self.ALLOWED_IMAGE_TYPES:
                    self.add_error(
                        f'resource_{index}_image',
                        'Only JPEG, PNG, WebP and GIF images are allowed.',
                    )

        if resource_count == 0:
            raise forms.ValidationError('Add at least one resource for staff verification.')
        return cleaned

    def save(self):
        d = self.cleaned_data
        application = OrganisationApplication.objects.create(
            organisation_name=d['organisation_name'],
            contact_name=d['contact_name'],
            contact_email=d['contact_email'],
            contact_phone=d['contact_phone'],
            address=d.get('address', ''),
            description=d.get('description', ''),
            logo=d.get('logo'),
        )

        for index in self.RESOURCE_SLOTS:
            name = d.get(f'resource_{index}_name')
            category = d.get(f'resource_{index}_category')
            if not name or not category:
                continue

            resource = ApplicationResource.objects.create(
                application=application,
                name=name,
                category=category,
                description=d.get(f'resource_{index}_description', ''),
                price=d.get(f'resource_{index}_price') or 0,
                image=d.get(f'resource_{index}_image'),
            )

        return application

