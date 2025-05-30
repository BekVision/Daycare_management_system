
from django.contrib import admin
from .models import AppSettings, ActivityLog, SystemHealth


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'data_type', 'is_editable', 'updated_at']
    list_filter = ['data_type', 'is_editable']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'object_type', 'timestamp']
    list_filter = ['action', 'object_type', 'timestamp']
    search_fields = ['user__username', 'action', 'object_type']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ['component', 'status', 'response_time', 'checked_at']
    list_filter = ['component', 'status', 'checked_at']
    readonly_fields = ['checked_at']
    date_hierarchy = 'checked_at'
