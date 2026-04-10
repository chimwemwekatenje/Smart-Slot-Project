from django.views.generic import TemplateView
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import SignupForm


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
