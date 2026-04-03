from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'status', 'paychangu_reference', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('booking__id', 'paychangu_reference')
    raw_id_fields = ('booking',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
