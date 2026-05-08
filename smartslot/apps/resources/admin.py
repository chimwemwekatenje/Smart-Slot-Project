from django.contrib import admin
from django.utils.html import format_html
from .models import Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display       = ('photo_preview', 'name', 'category',
                          'price_display', 'organisation', 'created_at')
    list_display_links = ('name',)
    list_filter        = ('category', 'organisation', 'created_at')
    search_fields      = ('name', 'description', 'category')
    ordering           = ('-created_at',)
    readonly_fields    = ('photo_preview', 'created_at', 'updated_at')
    autocomplete_fields = ('organisation',)

    fieldsets = (
        (None, {
            'fields': ('organisation', 'name', 'category', 'price', 'description'),
        }),
        ('Photo', {
            'fields': ('photo', 'photo_preview'),
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
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
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:60px;width:80px;object-fit:cover;'
                'border-radius:8px;border:1px solid #334155;" />',
                obj.photo.url,
            )
        return format_html(
            '<div style="height:60px;width:80px;border-radius:8px;background:#1e2937;'
            'border:1px solid #334155;display:flex;align-items:center;'
            'justify-content:center;font-size:24px;">📦</div>'
        )
    photo_preview.short_description = 'Photo'

    @admin.display(description='Price', ordering='price')
    def price_display(self, obj):
        price_int = int(obj.price)
        if price_int == 0:
            return format_html('<span style="color:#22c55e;font-weight:600;">Free</span>')
        return format_html(
            '<span style="color:#f59e0b;font-weight:600;">MWK {}</span>',
            '{:,}'.format(price_int),
        )
