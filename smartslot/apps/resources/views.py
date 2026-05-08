from django.views.generic import ListView
from django.utils import timezone
from .models import Resource
from apps.bookings.models import Booking


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

        ctx['is_external'] = not user.is_authenticated or (
            hasattr(user, 'role') and user.role == 'External'
        )
        ctx['is_authenticated'] = user.is_authenticated
        ctx['categories'] = ['All'] + list(
            Resource.objects.values_list('category', flat=True).distinct()
        )

        # Annotate each resource with its current booking status
        now = timezone.now()
        booked_ids = set(
            Booking.objects
            .filter(
                status__in=Booking.ACTIVE_STATUSES,
                start_time__lte=now,
                end_time__gt=now,
            )
            .values_list('resource_id', flat=True)
        )

        # Also find resources booked in the next 30 minutes (upcoming)
        soon = now + timezone.timedelta(minutes=30)
        upcoming_ids = set(
            Booking.objects
            .filter(
                status__in=Booking.ACTIVE_STATUSES,
                start_time__gt=now,
                start_time__lte=soon,
            )
            .values_list('resource_id', flat=True)
        )

        for resource in ctx['resources']:
            if resource.pk in booked_ids:
                resource.availability = 'booked'
            elif resource.pk in upcoming_ids:
                resource.availability = 'soon'
            else:
                resource.availability = 'available'

        return ctx
