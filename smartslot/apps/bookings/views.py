import uuid
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from apps.bookings.models import Booking
from apps.resources.models import Resource
from .forms import InternalBookingForm, ExternalBookingStep1Form, ExternalBookingStep3Form


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'

    STATUSES = ['All', 'Booked', 'Cancelled']

    def get_queryset(self):
        qs = Booking.objects.filter(user=self.request.user).order_by('-start_time')
        status = self.request.GET.get('status', 'All')
        if status and status != 'All':
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['statuses'] = self.STATUSES
        ctx['current_status'] = self.request.GET.get('status', 'All')
        return ctx


def _make_booking(request, resource, custom_data):
    """Helper — creates and saves a booking, returns the booking object."""
    start = custom_data.pop('start_time')
    end = custom_data.pop('end_time')
    booking = Booking(
        resource=resource,
        organisation=resource.organisation,
        user=request.user,
        start_time=start,
        end_time=end,
        qr_token=str(uuid.uuid4()),
        status=Booking.StatusChoices.BOOKED,  # auto-confirmed
        custom_data=custom_data,
    )
    booking.save()
    return booking


def _receipt_rows(booking):
    fmt = lambda dt: dt.strftime('%a %d %b %Y, %H:%M') if dt else '-'
    cd = booking.custom_data
    rows = [
        ('Resource',     booking.resource.name,              None),
        ('Category',     booking.resource.category,          None),
        ('Organisation', booking.organisation.name,          None),
    ]
    if cd.get('department'):
        rows.append(('Department', cd['department'], None))
    if cd.get('full_name'):
        rows.append(('Name',       cd['full_name'],  None))
    if cd.get('phone'):
        rows.append(('Phone',      cd['phone'],      None))
    if cd.get('email'):
        rows.append(('Email',      cd['email'],      None))
    if cd.get('reason'):
        rows.append(('Reason',     cd['reason'],     None))
    rows += [
        ('From',   fmt(booking.start_time.astimezone()), None),
        ('To',     fmt(booking.end_time.astimezone()),   None),
        ('Status', booking.status, '#14B8A6'),
    ]
    return rows


# ── Internal booking (Employee / OrgAdmin) ────────────────────────────────────

def _make_internal_booking(request, resource, start, end, department, reason):
    """Helper — creates and saves an internal booking from the authenticated user."""
    user = request.user
    full_name = f"{user.first_name} {user.last_name}".strip() or user.username
    email = user.email
    booking = Booking(
        resource=resource,
        organisation=resource.organisation,
        user=user,
        start_time=start,
        end_time=end,
        qr_token=str(uuid.uuid4()),
        status=Booking.StatusChoices.BOOKED,  # auto-confirmed
        custom_data={
            'full_name':  full_name,
            'email':      email,
            'department': department,
            'reason':     reason,
        },
    )
    booking.save()
    return booking


@login_required
def internal_booking_view(request, resource_pk):
    resource = get_object_or_404(Resource, pk=resource_pk)

    if request.method == 'POST':
        form = InternalBookingForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                booking = _make_internal_booking(
                    request, resource,
                    start=cd['start_time'],
                    end=cd['end_time'],
                    department=cd['department'],
                    reason=cd['reason'],
                )
            except ValidationError as e:
                return render(request, 'bookings/booking_create_internal.html', {
                    'form': form,
                    'resource': resource,
                    'overlap_error': e.message,
                })
            return render(request, 'bookings/booking_receipt.html', {
                'booking': booking,
                'receipt_rows': _receipt_rows(booking),
            })
    else:
        form = InternalBookingForm()

    return render(request, 'bookings/booking_create_internal.html', {
        'form': form,
        'resource': resource,
    })


STEPS = [('Time Slot', 1), ('Confirm', 2)]
STEPS_PAID = [('Time Slot', 1), ('Payment', 2)]

# ── External booking (2-step for logged-in: time → confirm/pay) ──────────────

@login_required
def external_booking_view(request, resource_pk):
    resource = get_object_or_404(Resource, pk=resource_pk)
    steps = STEPS_PAID if resource.price > 0 else STEPS
    step = int(request.POST.get('step', request.GET.get('step', 1)))
    session_key = f'ext_booking_{resource_pk}'

    # Pre-fill user details silently from profile
    user = request.user
    full_name = f"{user.first_name} {user.last_name}".strip() or user.username
    user_data = {
        'full_name': full_name,
        'email':     user.email,
        'phone':     getattr(user, 'phone', '') or '',
        'reason':    '',
    }

    if request.method == 'POST':

        if step == 1:
            # Step 1 is now time slot selection
            start_time = request.POST.get('start_time')
            end_time   = request.POST.get('end_time')
            if not start_time or not end_time:
                return render(request, 'bookings/booking_create_external.html', {
                    'resource': resource, 'step': 1, 'steps': steps,
                    'session_data': {},
                    'time_error': 'Please select a start and end time.',
                })
            from datetime import datetime as dt_cls
            try:
                start_dt = dt_cls.fromisoformat(start_time)
                end_dt   = dt_cls.fromisoformat(end_time)
                if end_dt <= start_dt:
                    raise ValueError("End time must be after start time.")
                conflict = Booking.objects.filter(
                    resource=resource,
                    status__in=Booking.ACTIVE_STATUSES,
                    start_time__lt=end_dt,
                    end_time__gt=start_dt,
                ).first()
                if conflict:
                    time_error = (
                        f"Occupied — booked until "
                        f"{conflict.end_time.strftime('%d %b %Y, %H:%M')}."
                    )
                    return render(request, 'bookings/booking_create_external.html', {
                        'resource': resource, 'step': 1, 'steps': steps,
                        'session_data': {},
                        'time_error': time_error,
                    })
            except ValueError as e:
                return render(request, 'bookings/booking_create_external.html', {
                    'resource': resource, 'step': 1, 'steps': steps,
                    'session_data': {},
                    'time_error': str(e),
                })
            saved = {**user_data, 'start_time': start_time, 'end_time': end_time}
            request.session[session_key] = saved
            return render(request, 'bookings/booking_create_external.html', {
                'resource': resource, 'step': 2, 'steps': steps,
                'session_data': saved,
            })

        elif step == 2:
            saved = request.session.get(session_key, {})
            if not saved.get('start_time'):
                saved = {**user_data,
                         'start_time': request.POST.get('sd_start_time', ''),
                         'end_time':   request.POST.get('sd_end_time', '')}

            from datetime import datetime
            start = datetime.fromisoformat(saved['start_time'])
            end   = datetime.fromisoformat(saved['end_time'])

            if resource.price == 0:
                # Free — confirm directly
                booking = _make_booking(request, resource, {
                    'start_time': start, 'end_time': end,
                    'full_name':  saved.get('full_name', ''),
                    'email':      saved.get('email', ''),
                    'phone':      saved.get('phone', ''),
                    'reason':     saved.get('reason', ''),
                })
                request.session.pop(session_key, None)
                return render(request, 'bookings/booking_receipt.html', {
                    'booking': booking,
                    'receipt_rows': _receipt_rows(booking),
                })
            else:
                # Paid — redirect to PayChangu
                booking = _make_booking(request, resource, {
                    'start_time':     start, 'end_time': end,
                    'full_name':      saved.get('full_name', ''),
                    'email':          saved.get('email', ''),
                    'phone':          saved.get('phone', ''),
                    'reason':         saved.get('reason', ''),
                    'payment_method': 'PayChangu',
                })
                request.session.pop(session_key, None)
                from apps.payments.services import initiate_payment
                name_parts = saved.get('full_name', '').split(' ', 1)
                try:
                    checkout_url, tx_ref = initiate_payment(
                        booking=booking,
                        customer_email=saved.get('email', ''),
                        customer_first_name=name_parts[0],
                        customer_last_name=name_parts[1] if len(name_parts) > 1 else '',
                    )
                    booking.custom_data['tx_ref'] = tx_ref
                    booking.save()
                    return redirect(checkout_url)
                except Exception as e:
                    return render(request, 'bookings/booking_receipt.html', {
                        'booking': booking,
                        'receipt_rows': _receipt_rows(booking),
                        'payment_error': str(e),
                    })

    # GET — start at step 1 (time slot)
    return render(request, 'bookings/booking_create_external.html', {
        'resource': resource, 'step': 1, 'steps': steps,
        'session_data': {},
    })


# ── PDF Receipt download ──────────────────────────────────────────────────────

@login_required
def booking_pdf_view(request, booking_id):
    from django.http import HttpResponse, Http404
    from django.core.exceptions import PermissionDenied
    from apps.bookings.pdf import generate_booking_pdf

    try:
        booking = Booking.objects.get(pk=booking_id)
    except Booking.DoesNotExist:
        raise Http404("Booking not found.")

    if booking.user != request.user:
        raise PermissionDenied

    buffer = generate_booking_pdf(booking)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="booking-{booking_id}.pdf"'
    return response


# ── Cancel booking ────────────────────────────────────────────────────────────

@login_required
def cancel_booking_view(request, booking_pk):
    from django.shortcuts import get_object_or_404
    from django.contrib import messages

    booking = get_object_or_404(Booking, pk=booking_pk, user=request.user)

    if request.method == 'POST':
        if booking.status == Booking.StatusChoices.BOOKED:
            booking.status = Booking.StatusChoices.CANCELLED
            # Skip full_clean on cancel — no overlap check needed
            Booking.objects.filter(pk=booking.pk).update(status=Booking.StatusChoices.CANCELLED)
            messages.success(request, f'Booking for {booking.resource.name} has been cancelled. The slot is now available.')
        return redirect('booking_list')

    return redirect('booking_list')
