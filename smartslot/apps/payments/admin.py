from django.contrib import admin
from django.utils.html import format_html
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'status_badge', 'paychangu_reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('booking__id', 'paychangu_reference')
    raw_id_fields = ('booking',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            'Pending':   ('#f59e0b', '#fef3c7'), # yellow-500, yellow-100
            'Success':   ('#10b981', '#d1fae5'), # emerald-500, emerald-100
            'Failed':    ('#ef4444', '#fee2e2'), # red-500, red-100
            'Refunded':  ('#3b82f6', '#dbeafe'), # blue-500, blue-100
        }
        fg, bg = colors.get(obj.status, ('#6b7280', '#f3f4f6')) # gray-500, gray-100
        return format_html(
            '<span style="background:{};color:{};padding:4px 12px;border-radius:12px;'
            'font-size:0.75rem;font-weight:600;display:inline-block;text-align:center;">{}</span>',
            bg, fg, obj.get_status_display(),
        )
