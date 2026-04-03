from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'resource', 'status', 'start_time', 'end_time', 'organisation')
    list_filter = ('status', 'start_time', 'end_time', 'organisation')
    search_fields = ('user__username', 'resource__name', 'qr_token', 'status')
    raw_id_fields = ('user', 'resource', 'organisation')
    date_hierarchy = 'start_time'
    ordering = ('-start_time',)
