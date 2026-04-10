import uuid
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from apps.bookings.models import Booking
from apps.resources.models import Resource
from .forms import InternalBookingForm, ExternalBookingStep1Form, ExternalBookingStep3Form


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = 'bookings/booking_list.html'
    context_object_name = 'bookings'

    STATUSES = ['All', 'Pending', 'Issued', 'Verified', 'Completed', 'Cancelled']

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
        status=Booking.StatusChoices.PENDING,
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
        ('Status', booking.status,                       '#F59E0B'),
    ]
    return rows


# ── Internal booking (Employee / OrgAdmin) ────────────────────────────────────

@login_required
def internal_booking_view(request, resource_pk):
    resource = get_object_or_404(Resource, pk=resource_pk)

    if request.method == 'POST':
        form = InternalBookingForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            booking = _make_booking(request, resource, {
                'start_time':  cd['start_time'],
                'end_time':    cd['end_time'],
                'department':  cd['department'],
                'reason':      cd['reason'],
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


STEPS = [('Details', 1), ('Time Slot', 2), ('Payment', 3)]

# ── External booking (3-step: details → time → payment) ──────────────────────

@login_required
def external_booking_view(request, resource_pk):
    resource = get_object_or_404(Resource, pk=resource_pk)
    step = int(request.POST.get('step', request.GET.get('step', 1)))
    session_key = f'ext_booking_{resource_pk}'

    if request.method == 'POST':
        if step == 1:
            form1 = ExternalBookingStep1Form(request.POST)
            if form1.is_valid():
                request.session[session_key] = {
                    'full_name': form1.cleaned_data['full_name'],
                    'phone':     form1.cleaned_data['phone'],
                    'email':     form1.cleaned_data['email'],
                    'reason':    form1.cleaned_data['reason'],
                }
                return render(request, 'bookings/booking_create_external.html', {
                    'resource': resource, 'step': 2, 'steps': STEPS,
                    'session_data': request.session[session_key],
                })
            return render(request, 'bookings/booking_create_external.html', {
                'resource': resource, 'step': 1, 'steps': STEPS, 'form1': form1,
            })

        elif step == 2:
            start_time = request.POST.get('start_time')
            end_time   = request.POST.get('end_time')
            if not start_time or not end_time:
                return render(request, 'bookings/booking_create_external.html', {
                    'resource': resource, 'step': 2, 'steps': STEPS,
                    'session_data': request.session.get(session_key, {}),
                    'time_error': 'Please select a start and end time.',
                })
            saved = request.session.get(session_key, {})
            saved['start_time'] = start_time
            saved['end_time']   = end_time
            request.session[session_key] = saved
            return render(request, 'bookings/booking_create_external.html', {
                'resource': resource, 'step': 3, 'steps': STEPS,
                'session_data': saved,
                'form3': ExternalBookingStep3Form(),
            })

        elif step == 3:
            form3 = ExternalBookingStep3Form(request.POST)
            saved = request.session.get(session_key, {})
            if form3.is_valid():
                from datetime import datetime
                start = datetime.fromisoformat(saved['start_time'])
                end   = datetime.fromisoformat(saved['end_time'])
                cd = form3.cleaned_data
                card_num = cd['card_number'].replace(' ', '')
                booking = _make_booking(request, resource, {
                    'start_time':     start,
                    'end_time':       end,
                    'full_name':      saved.get('full_name', ''),
                    'phone':          saved.get('phone', ''),
                    'email':          saved.get('email', ''),
                    'reason':         saved.get('reason', ''),
                    'payment_method': 'Card',
                    'card_last4':     card_num[-4:] if len(card_num) >= 4 else '****',
                })
                request.session.pop(session_key, None)
                return render(request, 'bookings/booking_receipt.html', {
                    'booking': booking,
                    'receipt_rows': _receipt_rows(booking),
                })
            return render(request, 'bookings/booking_create_external.html', {
                'resource': resource, 'step': 3, 'steps': STEPS,
                'session_data': saved, 'form3': form3,
            })

    # GET — start at step 1
    return render(request, 'bookings/booking_create_external.html', {
        'resource': resource, 'step': 1, 'steps': STEPS,
        'form1': ExternalBookingStep1Form(),
    })
