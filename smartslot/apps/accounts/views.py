from django.views.generic import TemplateView

class HomeView(TemplateView):
    template_name = 'base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Welcome to SmartSlot"
        context['show_welcome'] = True
        return context