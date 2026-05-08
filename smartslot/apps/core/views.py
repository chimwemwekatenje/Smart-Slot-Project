from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncHour
from django import forms as dj_forms
from apps.resources.models import Resource
from apps.bookings.models import Booking
from apps.core.models import Organisation
from apps.core.mixins import OrgScopedMixin
import json


# ── Admin login ───────────────────────────────────────────────────────────────

def admin_login_view(request):
    """Custom admin login — redirects to dashboard based on role."""
    if request.user.is_authenticated and request.user.role in ('PlatformAdmin', 'OrganisationAdmin'):
        return redirect('org_admin_dashboard')
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('org_admin_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            allowed = user.is_superuser or user.role in ('PlatformAdmin', 'OrganisationAdmin')
            if allowed:
                login(request, user)
                return redirect('org_admin_dashboard')
            else:
                error = 'Your account does not have admin access.'
        else:
            error = 'Invalid username or password.'

    return render(request, 'dashboard/admin_login.html', {'error': error})


# ── Organisation form ─────────────────────────────────────────────────────────

class OrganisationForm(dj_forms.ModelForm):
    class Meta:
        model = Organisation
        fields = ['name', 'logo']

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Organisation.objects.filter(name=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise dj_forms.ValidationError('An organisation with this name already exists.')
        return name


# ── Dashboard home ────────────────────────────────────────────────────────────

class OrganisationAdminDashboardView(OrgScopedMixin, TemplateView):
    template_name = 'dashboard/org_admin_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        organisation = self.get_org()  # None for PlatformAdmin/superuser
        booking_qs   = self.scope_qs(Booking.objects.all())
        resource_qs  = self.scope_qs(Resource.objects.all())

        ctx['organisation']              = organisation  # None = shows SmartSlot in sidebar
        today                            = timezone.now().date()
        month_start                      = today.replace(day=1)
        ctx['total_resources']           = resource_qs.count()
        ctx['active_bookings_today']     = booking_qs.filter(
            start_time__date=today, status='Booked').count()
        ctx['total_bookings_this_month'] = booking_qs.filter(
            start_time__date__gte=month_start).count()
        ctx['booked_count']              = booking_qs.filter(status='Booked').count()
        ctx['recent_bookings']           = booking_qs.order_by('-created_at')[:5]
        return ctx


# ── Dashboard resource list ───────────────────────────────────────────────────

class DashboardResourceListView(OrgScopedMixin, TemplateView):
    template_name = 'dashboard/resources.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['resources']    = self.scope_qs(Resource.objects.all()).order_by('name')
        ctx['organisation'] = self.get_org()  # None for super admin
        return ctx


# ── Dashboard booking list ────────────────────────────────────────────────────

class DashboardBookingListView(OrgScopedMixin, TemplateView):
    template_name = 'dashboard/bookings.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.scope_qs(Booking.objects.all()).order_by('-start_time')
        status_filter = self.request.GET.get('status')
        if status_filter and status_filter != 'All':
            qs = qs.filter(status=status_filter)
        ctx['bookings']       = qs
        ctx['statuses']       = ['All', 'Booked', 'Cancelled']
        ctx['current_status'] = status_filter or 'All'
        ctx['organisation']   = self.get_org()  # None for super admin
        return ctx


# ── Platform Admin — Organisation management ──────────────────────────────────

class DashboardOrgListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/organisations.html'

    def test_func(self):
        return self.request.user.role == 'PlatformAdmin' or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['organisations'] = Organisation.objects.all().order_by('name')
        ctx['organisation']  = None
        return ctx


class DashboardOrgCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Organisation
    form_class = OrganisationForm
    template_name = 'dashboard/organisation_form.html'

    def test_func(self):
        return self.request.user.role == 'PlatformAdmin' or self.request.user.is_superuser

    def get_success_url(self):
        from django.urls import reverse
        return reverse('dashboard_organisations')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['organisation'] = None
        ctx['form_title']   = 'Create Organisation'
        return ctx

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, f'Organisation "{form.instance.name}" created successfully.')
        return super().form_valid(form)


class DashboardOrgEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Organisation
    form_class = OrganisationForm
    template_name = 'dashboard/organisation_form.html'

    def test_func(self):
        return self.request.user.role == 'PlatformAdmin' or self.request.user.is_superuser

    def get_success_url(self):
        from django.urls import reverse
        return reverse('dashboard_organisations')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['organisation'] = None
        ctx['form_title']   = f'Edit Organisation: {self.object.name}'
        return ctx

    def form_valid(self, form):
        from django.contrib import messages
        messages.success(self.request, f'Organisation "{form.instance.name}" updated successfully.')
        return super().form_valid(form)


# ── Super Admin — User management ────────────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def dashboard_users_view(request):
    """Super Admin: list all users, create Org Admins, activate/deactivate/delete."""
    from django.contrib.auth import get_user_model
    from django.contrib import messages
    User = get_user_model()

    if not (request.user.is_superuser or request.user.role == 'PlatformAdmin'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    error = None

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Create new Org Admin ──────────────────────────────────────
        if action == 'create':
            username   = request.POST.get('username', '').strip()
            email      = request.POST.get('email', '').strip()
            password   = request.POST.get('password', '')
            first_name = request.POST.get('first_name', '').strip()
            last_name  = request.POST.get('last_name', '').strip()
            org_id     = request.POST.get('organisation')

            if User.objects.filter(username=username).exists():
                error = f'Username "{username}" is already taken.'
            elif not password:
                error = 'Password is required.'
            else:
                try:
                    org = Organisation.objects.get(pk=org_id) if org_id else None
                    user = User(
                        username=username, email=email,
                        first_name=first_name, last_name=last_name,
                        role='OrganisationAdmin', organisation=org,
                    )
                    user.set_password(password)
                    user.save()
                    messages.success(request, f'Org Admin "{username}" created successfully.')
                    return redirect('dashboard_users')
                except Exception as e:
                    error = str(e)

        # ── Activate user ─────────────────────────────────────────────
        elif action == 'activate':
            uid = request.POST.get('user_id')
            target = get_object_or_404(User, pk=uid)
            if target != request.user:
                User.objects.filter(pk=uid).update(is_active=True)
                messages.success(request, f'"{target.username}" has been activated.')
            return redirect('dashboard_users')

        # ── Deactivate user ───────────────────────────────────────────
        elif action == 'deactivate':
            uid = request.POST.get('user_id')
            target = get_object_or_404(User, pk=uid)
            if target != request.user:
                User.objects.filter(pk=uid).update(is_active=False)
                messages.success(request, f'"{target.username}" has been deactivated.')
            else:
                messages.error(request, "You can't deactivate your own account.")
            return redirect('dashboard_users')

        # ── Delete user ───────────────────────────────────────────────
        elif action == 'delete':
            uid = request.POST.get('user_id')
            target = get_object_or_404(User, pk=uid)
            if target != request.user:
                name = target.username
                target.delete()
                messages.success(request, f'User "{name}" has been deleted.')
            else:
                messages.error(request, "You can't delete your own account.")
            return redirect('dashboard_users')

    all_users = User.objects.exclude(
        username=request.user.username
    ).select_related('organisation').order_by('role', 'username')

    return render(request, 'dashboard/users.html', {
        'all_users':     all_users,
        'organisations': Organisation.objects.all().order_by('name'),
        'organisation':  None,
        'error':         error,
        'form_data':     request.POST if error else {},
    })


# ── Super Admin Analysis ──────────────────────────────────────────────────────

class SuperAdminAnalysisView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/super_admin_analysis.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'PlatformAdmin'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()

        org_id    = self.request.GET.get('organisation')
        category  = self.request.GET.get('category')
        date_from = self.request.GET.get('date_from')
        date_to   = self.request.GET.get('date_to')

        qs = Booking.objects.select_related('resource', 'user', 'organisation')
        if org_id:    qs = qs.filter(organisation_id=org_id)
        if category:  qs = qs.filter(resource__category=category)
        if date_from: qs = qs.filter(start_time__date__gte=date_from)
        if date_to:   qs = qs.filter(start_time__date__lte=date_to)

        ctx['total_bookings']      = qs.count()
        ctx['active_bookings']     = qs.filter(status='Booked').count()
        ctx['cancelled_bookings']  = qs.filter(status='Cancelled').count()
        ctx['total_revenue']       = qs.filter(status='Booked').aggregate(
            rev=Sum('resource__price'))['rev'] or 0
        ctx['total_organisations'] = Organisation.objects.count()
        ctx['total_resources']     = Resource.objects.count()

        ctx['top_resources'] = (
            qs.values('resource__name', 'resource__category')
            .annotate(count=Count('id')).order_by('-count')[:8]
        )

        status_data = qs.values('status').annotate(count=Count('id')).order_by('-count')
        ctx['status_labels'] = json.dumps([s['status'] for s in status_data])
        ctx['status_counts'] = json.dumps([s['count'] for s in status_data])

        thirty_days_ago = today - timezone.timedelta(days=29)
        trend = (Booking.objects.filter(start_time__date__gte=thirty_days_ago)
                 .annotate(day=TruncDate('start_time')).values('day')
                 .annotate(count=Count('id')).order_by('day'))
        trend_map = {str(t['day']): t['count'] for t in trend}
        trend_labels, trend_values = [], []
        for i in range(30):
            d = str(thirty_days_ago + timezone.timedelta(days=i))
            trend_labels.append(d[5:])
            trend_values.append(trend_map.get(d, 0))
        ctx['trend_labels'] = json.dumps(trend_labels)
        ctx['trend_values'] = json.dumps(trend_values)

        peak = (qs.annotate(hour=TruncHour('start_time')).values('hour')
                .annotate(count=Count('id')).order_by('hour'))
        hour_map = {}
        for p in peak:
            if p['hour']:
                h = p['hour'].hour
                hour_map[h] = hour_map.get(h, 0) + p['count']
        ctx['peak_labels'] = json.dumps([f"{h:02d}:00" for h in range(24)])
        ctx['peak_values'] = json.dumps([hour_map.get(h, 0) for h in range(24)])

        rev_by_org = (Booking.objects.filter(status='Booked')
                      .values('organisation__name').annotate(rev=Sum('resource__price'))
                      .order_by('-rev')[:8])
        ctx['rev_org_labels'] = json.dumps([r['organisation__name'] or 'Unknown' for r in rev_by_org])
        ctx['rev_org_values'] = json.dumps([float(r['rev'] or 0) for r in rev_by_org])

        cat_data = qs.values('resource__category').annotate(count=Count('id')).order_by('-count')
        ctx['cat_labels'] = json.dumps([c['resource__category'] or 'Other' for c in cat_data])
        ctx['cat_values'] = json.dumps([c['count'] for c in cat_data])

        ctx['organisations']      = Organisation.objects.all()
        ctx['categories']         = Resource.objects.values_list('category', flat=True).distinct()
        ctx['selected_org']       = org_id
        ctx['selected_category']  = category
        ctx['selected_date_from'] = date_from
        ctx['selected_date_to']   = date_to
        ctx['recent_bookings']    = qs.order_by('-created_at')[:10]
        ctx['organisation']       = None  # super admin — show SmartSlot in sidebar
        return ctx


# ── Org Admin — manage their org's users ─────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def dashboard_org_users_view(request):
    """Org Admin: view and manage users in their organisation."""
    from django.contrib.auth import get_user_model
    from django.contrib import messages
    User = get_user_model()

    user = request.user
    if not (user.is_superuser or user.role in ('PlatformAdmin', 'OrganisationAdmin')):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    org = user.organisation if user.role == 'OrganisationAdmin' else None

    if request.method == 'POST':
        action = request.POST.get('action')
        uid = request.POST.get('user_id')
        target = get_object_or_404(User, pk=uid)

        # Ensure org admin can only act on their own org's users
        if org and target.organisation != org:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        if action == 'activate':
            User.objects.filter(pk=uid).update(is_active=True)
            messages.success(request, f'"{target.username}" activated.')
        elif action == 'deactivate':
            if target != request.user:
                User.objects.filter(pk=uid).update(is_active=False)
                messages.success(request, f'"{target.username}" deactivated.')
        elif action == 'delete':
            if target != request.user:
                name = target.username
                target.delete()
                messages.success(request, f'User "{name}" deleted.')
        return redirect('dashboard_org_users')

    qs = User.objects.select_related('organisation')
    if org:
        qs = qs.filter(organisation=org)
    qs = qs.exclude(pk=request.user.pk).order_by('role', 'username')

    return render(request, 'dashboard/org_users.html', {
        'org_users':    qs,
        'organisation': org,
    })


# ── Org Admin — manage their org's resources ─────────────────────────────────

@login_required(login_url='/dashboard/login/')
def dashboard_org_resources_view(request):
    """Org Admin: create, edit, delete resources in their organisation."""
    from django.contrib import messages
    user = request.user

    if not (user.is_superuser or user.role in ('PlatformAdmin', 'OrganisationAdmin')):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    org = user.organisation if user.role == 'OrganisationAdmin' else None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            name        = request.POST.get('name', '').strip()
            category    = request.POST.get('category', '').strip()
            description = request.POST.get('description', '').strip()
            price       = request.POST.get('price', '0') or '0'
            if name and category and org:
                Resource.objects.create(
                    name=name, category=category,
                    description=description,
                    price=float(price),
                    organisation=org,
                )
                messages.success(request, f'Resource "{name}" created.')
            return redirect('dashboard_org_resources')

        elif action == 'delete':
            rid = request.POST.get('resource_id')
            res = get_object_or_404(Resource, pk=rid)
            if org and res.organisation != org:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied
            name = res.name
            res.delete()
            messages.success(request, f'Resource "{name}" deleted.')
            return redirect('dashboard_org_resources')

    qs = Resource.objects.select_related('organisation')
    if org:
        qs = qs.filter(organisation=org)
    qs = qs.order_by('name')

    return render(request, 'dashboard/org_resources.html', {
        'resources':    qs,
        'organisation': org,
        'categories':   ['Boardroom', 'Vehicle', 'Equipment', 'Other'],
    })


# ── Platform Admin — Delete organisation ─────────────────────────────────────

@login_required(login_url='/dashboard/login/')
def dashboard_org_delete_view(request, pk):
    from django.contrib import messages
    if not (request.user.is_superuser or request.user.role == 'PlatformAdmin'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    org = get_object_or_404(Organisation, pk=pk)
    if request.method == 'POST':
        name = org.name
        org.delete()
        messages.success(request, f'Organisation "{name}" and all its data have been deleted.')
        return redirect('dashboard_organisations')
    return redirect('dashboard_organisations')
