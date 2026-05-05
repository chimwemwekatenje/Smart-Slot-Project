from django.contrib import admin
from .models import VerificationLog


@admin.register(VerificationLog)
class VerificationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'verified_by', 'action', 'success', 'timestamp')
    list_filter = ('action', 'success', 'timestamp')
    search_fields = ('qr_token', 'notes', 'booking__id')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Verification logs are created automatically, not manually
        return False
    
    def has_change_permission(self, request, obj=None):
        # Logs should not be edited
        return False
