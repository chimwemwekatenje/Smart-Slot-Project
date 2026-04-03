from django.contrib import admin
from .models import Resource

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'organisation', 'created_at')
    list_filter = ('category', 'organisation', 'created_at')
    search_fields = ('name', 'description', 'category')
    raw_id_fields = ('organisation',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
