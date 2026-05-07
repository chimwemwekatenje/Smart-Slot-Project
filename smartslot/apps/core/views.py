from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate, TruncHour
from django import forms as dj_forms
from apps.resources.models import Resource
from apps.bookings.models import Booking
from apps.core.models import Organisation
from apps.core.mixins import OrgScopedMixin
import json


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
        context = super().get_context_data(**kwargs)

        organisation = self.get_org() or Organisation.objects.first()
        booking_qs   = self.scope_qs(Booking.objects.all())
        resource_qs  = self.scope_qs(Resource.objects.all())

        context['organisation'] = organisation
        today       = timezone.now().date()
        month_start = today.replace(day=1)

        context['total_resources']           = resource_qs.count()
        context['active_bookings_today']     = booking_qs.filter(
            start_time__date=today,
            status__in=['Pending', 'Issued', 'Verified'],
        ).count()
        context['total_bookings_this_month'] = booking_qs.filter(
            start_time__date__gte=month_start,
        ).count()
        context['pending_bookings_count']    = booking_qs.filter(status='Pending').count()
        context['recent_bookings']           = booking_qs.order_by('-created_at')[:5]

        return context


# ── Dashboard resource list ───────────────────────────────────────────────────

class DashboardResourceListView(OrgScopedMixin, TemplateView):
    template_name = 'dashboard/resources.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['resources']     = self.scope_qs(Resource.objects.all()).order_by('name')
        ctx['organisation']  = self.get_org() or Organisation.objects.first()
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
        ctx['statuses']       = ['All', 'Pending', 'Issued', 'Verified', 'Completed', 'Cancelled']
        ctx['current_status'] = status_filter or 'All'
        ctx['organisation']   = self.get_org() or Organisation.objects.first()
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


# ── Super Admin Analysis ──────────────────────────────────────────────────────

class SuperAdminAnalysisView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'dashboard/super_admin_analysis.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'PlatformAdmin'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now   = timezone.now()
        today = now.date()

        # ── Filters from GET params ──────────────────────────────────
        org_id    = self.request.GET.get('organisation')
        category  = self.request.GET.get('category')
        date_from = self.request.GET.get('date_from')
        date_to   = self.request.GET.get('date_to')

        qs = Booking.objects.select_related('resource', 'user', 'organisation')

        if org_id:
            qs = qs.filter(organisation_id=org_id)
        if category:
            qs = qs.filter(resource__category=category)
        if date_from:
            qs = qs.filter(start_time__date__gte=date_from)
        if date_to:
            qs = qs.filter(start_time__date__lte=date_to)

        # ── Top-level KPIs ───────────────────────────────────────────
        ctx['total_bookings']     = qs.count()
        ctx['active_bookings']    = qs.filter(status__in=['Pending', 'Issued', 'Verified']).count()
        ctx['completed_bookings'] = qs.filter(status='Completed').count()
        ctx['cancelled_bookings'] = qs.filter(status__in=['Cancelled', 'NoShow']).count()
        ctx['total_revenue']      = qs.filter(
            status__in=['Completed', 'Issued', 'Verified']
        ).aggregate(rev=Sum('resource__price'))['rev'] or 0
        ctx['total_organisations'] = Organisation.objects.count()
        ctx['total_resources']     = Resource.objects.count()

        # ── Most booked resources (top 8) ────────────────────────────
        ctx['top_resources'] = (
            qs.values('resource__name', 'resource__category')
            .annotate(count=Count('id'))
            .order_by('-count')[:8]
        )

        # ── Bookings by status (for doughnut chart) ──────────────────
        status_data = (
            qs.values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        ctx['status_labels'] = json.dumps([s['status'] for s in status_data])
        ctx['status_counts'] = json.dumps([s['count'] for s in status_data])

        # ── Booking trend — last 30 days (for line chart) ────────────
        thirty_days_ago = today - timezone.timedelta(days=29)
        trend = (
            Booking.objects
            .filter(start_time__date__gte=thirty_days_ago)
            .annotate(day=TruncDate('start_time'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        trend_map = {str(t['day']): t['count'] for t in trend}
        trend_labels, trend_values = [], []
        for i in range(30):
            d = str(thirty_days_ago + timezone.timedelta(days=i))
            trend_labels.append(d[5:])   # MM-DD
            trend_values.append(trend_map.get(d, 0))
        ctx['trend_labels'] = json.dumps(trend_labels)
        ctx['trend_values'] = json.dumps(trend_values)

        # ── Peak hours (for bar chart) ────────────────────────────────
        peak = (
            qs.annotate(hour=TruncHour('start_time'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        hour_map = {}
        for p in peak:
            if p['hour']:
                h = p['hour'].hour
                hour_map[h] = hour_map.get(h, 0) + p['count']
        ctx['peak_labels'] = json.dumps([f"{h:02d}:00" for h in range(24)])
        ctx['peak_values'] = json.dumps([hour_map.get(h, 0) for h in range(24)])

        # ── Revenue by organisation ───────────────────────────────────
        rev_by_org = (
            Booking.objects
            .filter(status__in=['Completed', 'Issued', 'Verified'])
            .values('organisation__name')
            .annotate(rev=Sum('resource__price'))
            .order_by('-rev')[:8]
        )
        ctx['rev_org_labels'] = json.dumps([r['organisation__name'] or 'Unknown' for r in rev_by_org])
        ctx['rev_org_values'] = json.dumps([float(r['rev'] or 0) for r in rev_by_org])

        # ── Bookings by category ──────────────────────────────────────
        cat_data = (
            qs.values('resource__category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        ctx['cat_labels'] = json.dumps([c['resource__category'] or 'Other' for c in cat_data])
        ctx['cat_values'] = json.dumps([c['count'] for c in cat_data])

        # ── Filter form data ─────────────────────────────────────────
        ctx['organisations']      = Organisation.objects.all()
        ctx['categories']         = Resource.objects.values_list('category', flat=True).distinct()
        ctx['selected_org']       = org_id
        ctx['selected_category']  = category
        ctx['selected_date_from'] = date_from
        ctx['selected_date_to']   = date_to

        # ── Recent bookings table ─────────────────────────────────────
        ctx['recent_bookings'] = qs.order_by('-created_at')[:10]

        # ── Sidebar org (for base_dashboard sidebar) ──────────────────
        ctx['organisation'] = Organisation.objects.first()

        return ctx
