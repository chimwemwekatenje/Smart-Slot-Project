from django.views.generic import ListView
from apps.bookings.models import Booking

class BookingListView(ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    ordering = ['-start_time']

    def get_queryset(self):
        # Filter bookings based on user role
        user = self.request.user
        
        if not user.is_authenticated:
            return Booking.objects.none()
        
        # Platform admins see all bookings
        if user.role == 'PlatformAdmin':
            return Booking.objects.all()
        
        # Organisation admins and receptionists see their org's bookings
        if user.role in ['OrganisationAdmin', 'Receptionist'] and user.organisation:
            return Booking.objects.filter(
                resource__organisation=user.organisation
            ).select_related('resource', 'user')
        
        # Employees and external users see only their own bookings
        return Booking.objects.filter(user=user).select_related('resource')