import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView

from apps.bookings.models import Booking
from apps.resources.models import Resource

from .forms import BookingForm


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'
    ordering = ['-start_time']

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related('resource')


class BookingCreateView(LoginRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    template_name = 'bookings/booking_form.html'
    success_url = reverse_lazy('booking_list')

    def get_resource(self):
        return get_object_or_404(Resource, pk=self.kwargs['resource_pk'])

    def get_form_kwargs(self):
        """Pass the resource into the form so it can run overlap validation."""
        kwargs = super().get_form_kwargs()
        kwargs['resource'] = self.get_resource()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.get_resource()
        context['resource'] = resource
        # Show upcoming confirmed/pending bookings so users see what's taken
        context['upcoming_bookings'] = (
            Booking.objects
            .filter(resource=resource, end_time__gte=timezone.now())
            .exclude(status=Booking.StatusChoices.CANCELLED)
            .order_by('start_time')[:8]
        )
        return context

    def form_valid(self, form):
        resource = self.get_resource()
        start_time = form.cleaned_data['start_time']
        end_time = form.cleaned_data['end_time']

        # Conflict detection — prevent overlapping active bookings
        conflicts = Booking.objects.filter(
            resource=resource,
            status__in=[
                Booking.StatusChoices.PENDING,
                Booking.StatusChoices.ISSUED,
                Booking.StatusChoices.VERIFIED,
            ],
        ).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        )

        if conflicts.exists():
            messages.error(
                self.request,
                'This resource is already booked for part of that time. '
                'Please choose a different slot.'
            )
            return self.form_invalid(form)

        booking = form.save(commit=False)
        booking.resource = resource
        booking.organisation = resource.organisation
        booking.user = self.request.user
        booking.qr_token = str(uuid.uuid4())
        booking.status = Booking.StatusChoices.PENDING

        notes = form.cleaned_data.get('notes', '')
        if notes:
            booking.custom_data = {'notes': notes}

        booking.save()
        messages.success(
            self.request,
            f'Booking confirmed for "{resource.name}"! '
            'Your QR code will be issued shortly.'
        )
        return super().form_valid(form)
