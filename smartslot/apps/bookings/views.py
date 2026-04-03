from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Booking

class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
