from django.contrib import admin
from django.utils.html import format_html
from .models import Organisation, OrganisationApplication, ApplicationResource


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display       = ('logo_preview', 'name', 'created_at', 'updated_at')
    # logo_preview returns HTML — point the edit link at 'name' instead.
    list_display_links = ('name',)
    search_fields      = ('name',)
    list_filter        = ('created_at',)
    ordering           = ('-created_at',)
    readonly_fields    = ('logo_preview', 'created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'logo', 'logo_preview'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="height:48px;width:48px;object-fit:cover;'
                'border-radius:8px;border:1px solid #334155;" />',
                obj.logo.url
            )
        return format_html(
            '<div style="height:48px;width:48px;border-radius:8px;background:#1e2937;'
            'border:1px solid #334155;display:flex;align-items:center;justify-content:center;'
            'font-size:20px;">🏢</div>'
        )
    logo_preview.short_description = 'Logo'


class ApplicationResourceInline(admin.TabularInline):
    model = ApplicationResource
    extra = 0
    readonly_fields = ('verified_at', 'created_at', 'updated_at')
    show_change_link = True


@admin.register(OrganisationApplication)
class OrganisationApplicationAdmin(admin.ModelAdmin):
    list_display = ('organisation_name', 'contact_email', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('organisation_name', 'contact_name', 'contact_email')
    readonly_fields = ('verification_token', 'submitted_at', 'updated_at')
    inlines = (ApplicationResourceInline,)


@admin.register(ApplicationResource)
class ApplicationResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'application', 'category', 'price', 'status', 'verified_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('name', 'application__organisation_name')
    readonly_fields = ('verified_at', 'created_at', 'updated_at')
