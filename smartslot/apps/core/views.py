from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from apps.resources.models import Resource
from apps.bookings.models import Booking
from apps.core.models import Organisation

class OrganisationAdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/org_admin_dashboard.html'
    
    def test_func(self):
        return self.request.user.role == 'OrganisationAdmin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Determine organisation (assuming the first one if user is not explicitly tied)
        organisation = Organisation.objects.first()
        context['organisation'] = organisation
        
        today = timezone.now().date()
        month_start = today.replace(day=1)

        if organisation:
            context['total_resources'] = Resource.objects.filter(organisation=organisation).count()
            context['active_bookings_today'] = Booking.objects.filter(
                resource__organisation=organisation,
                start_time__date=today,
                status__in=['Pending', 'Issued', 'Verified']
            ).count()
            context['total_bookings_this_month'] = Booking.objects.filter(
                resource__organisation=organisation,
                start_time__date__gte=month_start
            ).count()
            context['recent_bookings'] = Booking.objects.filter(
                resource__organisation=organisation
            ).order_by('-created_at')[:5]
        else:
            context['total_resources'] = 0
            context['active_bookings_today'] = 0
            context['total_bookings_this_month'] = 0
            context['recent_bookings'] = []

        return context
