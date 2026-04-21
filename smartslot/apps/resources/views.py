from django.views.generic import ListView
from .models import Resource


class ResourceListView(ListView):
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        cat = self.request.GET.get('category')
        if cat and cat != 'All':
            qs = qs.filter(category=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        # Logged-in employee/admin → free, internal booking
        # Logged-in external → paid, external booking
        # Not logged in → show prices, redirect to login on book
        ctx['is_external'] = not user.is_authenticated or (
            hasattr(user, 'role') and user.role == 'External'
        )
        ctx['is_authenticated'] = user.is_authenticated
        ctx['categories'] = ['All'] + list(
            Resource.objects.values_list('category', flat=True).distinct()
        )
        return ctx
