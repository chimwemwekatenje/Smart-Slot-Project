import uuid
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from apps.bookings.models import Booking
from apps.resources.models import Resource
from .forms import BookingForm


class BookingListView(ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    ordering = ['-start_time']

    def get_queryset(self):
        return Booking.objects.all()


class BookingCreateView(CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_create.html'
    success_url = reverse_lazy('booking_list')

    def get_resource(self):
        return get_object_or_404(Resource, pk=self.kwargs['resource_pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['resource'] = self.get_resource()
        return ctx

    def form_valid(self, form):
        resource = self.get_resource()
        booking = form.save(commit=False)
        booking.resource = resource
        booking.organisation = resource.organisation
        # Temporary: assign first available user until auth is wired up
        from django.contrib.auth import get_user_model
        User = get_user_model()
        booking.user = User.objects.first()
        booking.qr_token = str(uuid.uuid4())
        booking.status = Booking.StatusChoices.PENDING
        booking.save()
        return super().form_valid(form)
