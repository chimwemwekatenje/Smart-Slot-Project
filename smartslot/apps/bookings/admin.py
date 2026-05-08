from django.contrib import admin
from django.utils.html import format_html
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display       = ('id', 'user', 'resource', 'organisation',
                          'status_badge', 'start_time', 'end_time')
    list_display_links = ('id',)
    list_filter        = ('status', 'organisation', 'start_time')
    search_fields      = ('user__username', 'resource__name', 'qr_token', 'status')
    date_hierarchy     = 'start_time'
    ordering           = ('-start_time',)
    autocomplete_fields = ('user', 'resource', 'organisation')
    readonly_fields    = ('issued_at', 'verified_at', 'created_at', 'updated_at')

    fieldsets = (
        ('Booking Details', {
            'fields': ('organisation', 'user', 'resource', 'status'),
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time'),
        }),
        ('QR Token', {
            'fields': ('qr_token',),
        }),
        ('Verification Timestamps', {
            'fields': ('issued_at', 'verified_at'),
            'classes': ('collapse',),
        }),
        ('Custom Data', {
            'fields': ('custom_data',),
            'classes': ('collapse',),
        }),
        ('Record Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ------------------------------------------------------------------
    # Multi-tenancy
    # ------------------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'PlatformAdmin':
            return qs
        if request.user.role == 'OrganisationAdmin' and request.user.organisation:
            return qs.filter(organisation=request.user.organisation)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if (
            not request.user.is_superuser
            and request.user.role == 'OrganisationAdmin'
            and request.user.organisation
        ):
            obj.organisation = request.user.organisation
        super().save_model(request, obj, form, change)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------
    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colours = {
            'Pending':   ('#f59e0b', '#1c1400'),
            'Issued':    ('#3b82f6', '#0c1a2e'),
            'Verified':  ('#14b8a6', '#042f2e'),
            'Completed': ('#22c55e', '#052e16'),
            'Cancelled': ('#ef4444', '#450a0a'),
            'NoShow':    ('#94a3b8', '#1e293b'),
        }
        fg, bg = colours.get(obj.status, ('#94a3b8', '#1e293b'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:12px;'
            'font-size:0.78rem;font-weight:600;">{}</span>',
            bg, fg, obj.get_status_display(),
        )
