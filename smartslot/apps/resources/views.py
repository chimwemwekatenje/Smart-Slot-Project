from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Resource
from apps.core.models import Organisation

class ResourceListView(LoginRequiredMixin, ListView):
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organisations'] = Organisation.objects.all()
        # Pass active filters to template for pill highlighting
        context['active_q']        = self.request.GET.get('q', '')
        context['active_category'] = self.request.GET.get('category', '')
        context['active_price']    = self.request.GET.get('price', '')
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(category__icontains=search_query))
            
        category_filter = self.request.GET.get('category')
        if category_filter:
            queryset = queryset.filter(category=category_filter)
            
        price_filter = self.request.GET.get('price')
        if price_filter == 'free':
            queryset = queryset.filter(price=0)
        elif price_filter == 'paid':
            queryset = queryset.filter(price__gt=0)
            
        org_filter = self.request.GET.get('organisation')
        if org_filter:
            queryset = queryset.filter(organisation__id=org_filter)
            
        return queryset
