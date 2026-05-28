from django.views.generic import ListView
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from .models import Resource
from apps.bookings.models import Booking


class ResourceListView(ListView):
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'

    def get_queryset(self):
        user = self.request.user
        qs = Resource.objects.visible_to(user).select_related('organisation')

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)

        cat = self.request.GET.get('category', '')
        if cat and cat != 'All':
            qs = qs.filter(category=cat)

        return qs

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        user = self.request.user

        is_external = (
            not user.is_authenticated
            or (hasattr(user, 'role') and user.role == 'External')
        )
        ctx['is_external']      = is_external
        ctx['is_authenticated'] = user.is_authenticated

        # Build category list from the model's choices — always clean, never duplicated,
        # regardless of what inconsistent values may exist in the database.
        ctx['categories'] = ['All'] + [value for value, _ in Resource.CategoryChoices.choices]

        now  = timezone.now()
        soon = now + timezone.timedelta(minutes=30)

        # Get current active bookings (happening right now)
        booked_now_qs = Booking.objects.filter(
            status__in=Booking.ACTIVE_STATUSES,
            start_time__lte=now,
            end_time__gt=now,
        ).select_related('resource')

        booked_ids = set(b.resource_id for b in booked_now_qs)

        # Map resource_id → booking for tooltip info
        booked_info = {
            b.resource_id: b for b in booked_now_qs
        }

        upcoming_qs = Booking.objects.filter(
            status__in=Booking.ACTIVE_STATUSES,
            start_time__gt=now,
            start_time__lte=soon,
        ).select_related('resource')

        upcoming_ids = set(b.resource_id for b in upcoming_qs)
        upcoming_info = {b.resource_id: b for b in upcoming_qs}

        for resource in ctx['resources']:
            if resource.pk in booked_ids:
                resource.availability = 'booked'
                b = booked_info[resource.pk]
                resource.booked_until = b.end_time
                resource.booked_from  = b.start_time
            elif resource.pk in upcoming_ids:
                resource.availability = 'soon'
                b = upcoming_info[resource.pk]
                resource.booked_from  = b.start_time
                resource.booked_until = b.end_time
            else:
                resource.availability = 'available'
                resource.booked_from  = None
                resource.booked_until = None

        return ctx


def resource_book_redirect(request, resource_pk):
    """
    Guest-facing redirect view.

    Sets a friendly info message then sends the user to the login page.
    After login, Django's `next` parameter returns them to the correct
    booking URL for the resource they wanted.
    """
    resource = get_object_or_404(Resource, pk=resource_pk)

    # Authenticated users should never hit this view — send them straight
    # to the right booking flow instead.
    if request.user.is_authenticated:
        if request.user.role == 'External':
            return redirect('booking_create_external', resource_pk=resource_pk)
        return redirect('booking_create_internal', resource_pk=resource_pk)

    # Decide where to land after login based on the resource's price.
    # External users pay; internal users book free.
    # We don't know the role yet (guest), so default to external flow.
    booking_url = reverse('booking_create_external', kwargs={'resource_pk': resource_pk})

    messages.info(
        request,
        f'Please log in to book "{resource.name}".',
    )

    login_url = reverse('login')
    return redirect(f'{login_url}?next={booking_url}')
