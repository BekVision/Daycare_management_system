from django.contrib import admin
from .models import AppSettings, ActivityLog, SystemHealth


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'data_type', 'is_editable', 'created_at', 'updated_at']
    list_filter = ['data_type', 'is_editable', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('key', 'value', 'data_type')
        }),
        ('Qo\'shimcha', {
            'fields': ('description', 'is_editable')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.is_editable:
            return self.readonly_fields + ('key', 'value', 'data_type', 'is_editable')
        return self.readonly_fields


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'object_type', 'object_repr', 'timestamp']
    list_filter = ['action', 'object_type', 'timestamp']
    search_fields = ['user__username', 'object_repr', 'ip_address']
    readonly_fields = ['user', 'action', 'object_type', 'object_id', 'object_repr',
                       'changes', 'ip_address', 'user_agent', 'timestamp']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Faoliyat ma\'lumotlari', {
            'fields': ('user', 'action', 'timestamp')
        }),
        ('Ob\'ekt ma\'lumotlari', {
            'fields': ('object_type', 'object_id', 'object_repr', 'changes')
        }),
        ('Texnik ma\'lumotlar', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ['component', 'status', 'response_time', 'checked_at']
    list_filter = ['component', 'status', 'checked_at']
    search_fields = ['component', 'error_message']
    readonly_fields = ['checked_at']

    fieldsets = (
        ('Komponent ma\'lumotlari', {
            'fields': ('component', 'status', 'response_time')
        }),
        ('Xato ma\'lumotlari', {
            'fields': ('error_message', 'details'),
            'classes': ('collapse',)
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('checked_at',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-checked_at')

    actions = ['mark_as_healthy']

    def mark_as_healthy(self, request, queryset):
        updated = queryset.update(status=SystemHealth.StatusChoices.HEALTHY)
        self.message_user(request, f'{updated} ta komponent sog\'lom deb belgilandi.')

    mark_as_healthy.short_description = "Tanlangan komponentlarni sog'lom deb belgilash"