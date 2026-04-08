from django.contrib import admin
from django.utils.html import format_html
from .models import Organisation


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display  = ('logo_preview', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter   = ('created_at',)
    ordering      = ('-created_at',)
    readonly_fields = ('logo_preview',)

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
