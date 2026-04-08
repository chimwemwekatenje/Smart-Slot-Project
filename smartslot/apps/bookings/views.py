import uuid
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from apps.bookings.models import Booking
from apps.resources.models import Resource
from .forms import BookingForm


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    ordering = ['-start_time']

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)


class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('booking_list')

    def get_resource(self):
        return get_object_or_404(Resource, pk=self.kwargs['resource_pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resource'] = self.get_resource()
        return context

    def form_valid(self, form):
        resource = self.get_resource()
        booking = form.save(commit=False)
        booking.resource = resource
        booking.organisation = resource.organisation
        booking.user = self.request.user
        booking.qr_token = str(uuid.uuid4())
        booking.status = Booking.StatusChoices.PENDING
        # Store extra notes in the custom_data JSONField
        notes = form.cleaned_data.get('notes', '')
        if notes:
            booking.custom_data = {'notes': notes}
        booking.save()
        messages.success(
            self.request,
            f'Booking confirmed for "{resource.name}"! Your QR code will be issued shortly.'
        )
        return super().form_valid(form)
