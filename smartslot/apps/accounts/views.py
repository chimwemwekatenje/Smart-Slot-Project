from django.views.generic import TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.urls import reverse_lazy
from .forms import SignupForm


class HomeView(TemplateView):
    """
    Public homepage shown to all visitors.
    Authenticated users see the full welcome dashboard.
    Unauthenticated users see a landing page with prompts to login/register.
    """
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['show_welcome'] = True
        return context


class SignupView(CreateView):
    form_class = SignupForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('resource_list')

    def form_valid(self, form):
        """Auto-login the user after successful registration."""
        response = super().form_valid(form)
        login(self.request, self.object)
        return response