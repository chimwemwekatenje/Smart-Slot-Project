"""
apps/bookings/views.py
----------------------
Multi-tenant booking views.

Access rules
------------
- PlatformAdmin        → sees ALL bookings across every organisation.
- OrganisationAdmin    → sees all bookings within their own organisation.
- Employee / External  → sees ONLY their own personal bookings.

All Firestore access goes through  apps.bookings.services.
"""

import uuid
from datetime import datetime
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator

from apps.core.services import get_org_id_for_user, assert_same_org
from apps.bookings.services import (
    BookingStatus,
    get_bookings_for_organisation,
    get_bookings_for_user,
    get_all_bookings,
    get_booking_by_id,
    create_booking,
    cancel_booking,
)
from apps.resources.services import get_resource_by_id
from .forms import InternalBookingForm, ExternalBookingStep1Form, ExternalBookingStep3Form


# ── Roles that can see the whole organisation's bookings ──────────────────────
_ORG_WIDE_ROLES = {'super_admin', 'org_admin'}


@method_decorator(login_required, name='dispatch')
class BookingListView(LoginRequiredMixin, View):
    """
    Display a list of bookings.

    - PlatformAdmin           → all bookings, all organisations
    - OrgAdmin                → all bookings in their organisation
    - Employee / External     → only their own bookings
    """

    template_name = 'bookings/booking_list.html'
    STATUSES = ['All'] + BookingStatus.ALL

    def get(self, request):
        user = request.user
        status = request.GET.get('status', 'All')

        try:
            org_id = get_org_id_for_user(user)  # None for PlatformAdmin
        except PermissionDenied as exc:
            return render(request, 'errors/403.html', {'message': str(exc)}, status=403)

        # ── Fetch bookings based on role ───────────────────────────────────
        if user.is_platform_admin:
            bookings = get_all_bookings(status=status)
        elif user.role in _ORG_WIDE_ROLES:
            bookings = get_bookings_for_organisation(org_id, status=status)
        else:
            # Employee / External — own bookings only
            bookings = get_bookings_for_user(org_id, user_id=user.pk, status=status)

        context = {
            'bookings':        bookings,
            'statuses':        self.STATUSES,
            'current_status':  status,
        }
        return render(request, self.template_name, context)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _receipt_context(booking: dict) -> list[tuple]:
    """Build receipt rows from a Firestore booking dict."""
    fmt = lambda s: s if s else '-'
    rows = [
        ('Resource',     booking.get('resource_name', ''), None),
        ('Organisation', booking.get('organisation_id', ''), None),
        ('Title',        booking.get('title', ''), None),
        ('Purpose',      booking.get('purpose', ''), None),
    ]
    if booking.get('notes'):
        rows.append(('Notes', booking.get('notes'), None))
    rows += [
        ('From',    fmt(booking.get('start_time')),  None),
        ('To',      fmt(booking.get('end_time')),    None),
        ('Status',  booking.get('status', ''),       '#F59E0B'),
    ]
    return rows


def _get_resource_for_request(request, resource_id: int) -> tuple:
    """
    Look up a resource by pk, enforcing org-scoped access.

    Returns (resource_dict, org_id) or raises PermissionDenied / Http404.
    """
    from django.http import Http404
    from apps.resources.services import get_all_resources

    user = request.user
    try:
        org_id = get_org_id_for_user(user)
    except PermissionDenied:
        raise

    if user.is_platform_admin:
        # PlatformAdmin can book any resource across all orgs
        all_resources = get_all_resources()
        matches = [r for r in all_resources if r['id'] == int(resource_id)]
        if not matches:
            raise Http404(f"Resource {resource_id!r} not found.")
        resource = matches[0]
        return resource, resource['organisation_id']
    else:
        resource = get_resource_by_id(org_id, int(resource_id))
        if resource is None:
            raise Http404(f"Resource {resource_id!r} not found in your organisation.")
        return resource, org_id


# ── Internal booking (Employee / OrgAdmin) ────────────────────────────────────

@login_required
def internal_booking_view(request, resource_id: str):
    """
    Create a booking for an internal user (Employee, OrgAdmin).

    The resource is looked up from Firestore; the booking is scoped to the
    user's organisation automatically.
    """
    try:
        resource, org_id = _get_resource_for_request(request, resource_id)
    except PermissionDenied as exc:
        return render(request, 'errors/403.html', {'message': str(exc)}, status=403)

    if request.method == 'POST':
        form = InternalBookingForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            booking_id = create_booking(
                organisation_id=org_id,
                resource_id=resource['id'],
                resource_name=resource['name'],
                user=request.user,
                start_time=cd['start_time'],
                end_time=cd['end_time'],
                title=cd['title'],
                purpose=cd['purpose'],
            )
            booking = get_booking_by_id(org_id, booking_id)
            return render(request, 'bookings/booking_receipt.html', {
                'booking':      booking,
                'receipt_rows': _receipt_context(booking),
            })
    else:
        form = InternalBookingForm()

    return render(request, 'bookings/booking_create_internal.html', {
        'form':     form,
        'resource': resource,
    })


STEPS = [('Details', 1), ('Time Slot', 2), ('Payment', 3)]


# ── External booking (3-step: details → time → payment) ──────────────────────

@login_required
def external_booking_view(request, resource_id: str):
    """
    3-step booking flow for External users (paid bookings).

    Step 1: Personal details
    Step 2: Time slot selection
    Step 3: Payment details
    """
    try:
        resource, org_id = _get_resource_for_request(request, resource_id)
    except PermissionDenied as exc:
        return render(request, 'errors/403.html', {'message': str(exc)}, status=403)

    step = int(request.POST.get('step', request.GET.get('step', 1)))
    session_key = f'ext_booking_{resource_id}'

    if request.method == 'POST':
        if step == 1:
            form1 = ExternalBookingStep1Form(request.POST)
            if form1.is_valid():
                request.session[session_key] = {
                    'full_name': form1.cleaned_data['full_name'],
                    'phone':     form1.cleaned_data['phone'],
                    'email':     form1.cleaned_data['email'],
                    'title':     form1.cleaned_data['title'],
                    'purpose':   form1.cleaned_data['purpose'],
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
            saved.update({'start_time': start_time, 'end_time': end_time})
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
                start = datetime.fromisoformat(saved['start_time'])
                end   = datetime.fromisoformat(saved['end_time'])
                cd = form3.cleaned_data
                card_num = cd['card_number'].replace(' ', '')
                booking_id = create_booking(
                    organisation_id=org_id,
                    resource_id=resource['id'],
                    resource_name=resource['name'],
                    user=request.user,
                    start_time=start,
                    end_time=end,
                    title=saved.get('title', ''),
                    purpose=saved.get('purpose', ''),
                    notes=f"Payment: Card ending in {card_num[-4:] if len(card_num) >= 4 else '****'}\nName: {saved.get('full_name', '')}\nPhone: {saved.get('phone', '')}\nEmail: {saved.get('email', '')}",
                )
                request.session.pop(session_key, None)
                booking = get_booking_by_id(org_id, booking_id)
                return render(request, 'bookings/booking_receipt.html', {
                    'booking':      booking,
                    'receipt_rows': _receipt_context(booking),
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
