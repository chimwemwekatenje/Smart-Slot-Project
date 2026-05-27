from django.views.generic import TemplateView
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import OrganisationRegistrationForm, SignupForm


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['show_welcome'] = True
        return ctx


def signup_view(request):
    from apps.core.models import Organisation
    organisations = Organisation.objects.all()

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('resource_list')
    else:
        form = SignupForm()

    return render(request, 'registration/register.html', {
        'form': form,
        'organisations': organisations,
    })


def organisation_signup_view(request):
    if request.method == 'POST':
        form = OrganisationRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()
            return render(request, 'registration/organisation_submitted.html', {
                'application': application,
            })
    else:
        form = OrganisationRegistrationForm()

    return render(request, 'registration/organisation_register.html', {
        'form': form,
        'resource_slots': OrganisationRegistrationForm.RESOURCE_SLOTS,
    })


def set_password_view(request, uidb64, token):
    from django.contrib.auth import get_user_model
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from django.contrib.auth.tokens import PasswordResetTokenGenerator
    from django.contrib import messages

    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()
    if user is not None and token_generator.check_token(user, token):
        if request.method == 'POST':
            pwd = request.POST.get('password')
            confirm_pwd = request.POST.get('confirm_password')
            if not pwd or len(pwd) < 8:
                return render(request, 'registration/set_password.html', {
                    'error_message': 'Password must be at least 8 characters long.'
                })
            if pwd != confirm_pwd:
                return render(request, 'registration/set_password.html', {
                    'error_message': 'Passwords do not match.'
                })

            user.set_password(pwd)
            user.save()
            # Authenticate and login
            login(request, user)
            messages.success(request, 'Password configured successfully. Welcome to your dashboard!')
            return redirect('org_admin_dashboard')

        return render(request, 'registration/set_password.html')
    else:
        return render(request, 'registration/set_password.html', {
            'error_message': 'The password configuration link is invalid or has expired.'
        })
