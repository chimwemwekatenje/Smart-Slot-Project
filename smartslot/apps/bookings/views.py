from django.views.generic import ListView
from apps.bookings.models import Booking

class BookingListView(ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    ordering = ['-start_time']

    # Temporarily show all bookings (we'll fix this later)
    def get_queryset(self):
        return Booking.objects.all()