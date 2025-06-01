# notifications/admin.py
from django.contrib import admin
from .models import Notification, NotificationPreference, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'type', 'priority', 'is_read', 'is_seen', 'created_at']
    list_filter = ['type', 'priority', 'is_read', 'is_seen', 'created_at']
    search_fields = ['title', 'message', 'recipient__username', 'recipient__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'sent_at', 'read_at']

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} ta bildirishnoma o\'qilgan deb belgilandi.')

    mark_as_read.short_description = 'O\'qilgan deb belgilash'

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'{queryset.count()} ta bildirishnoma o\'qilmagan deb belgilandi.')

    mark_as_unread.short_description = 'O\'qilmagan deb belgilash'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_notifications', 'browser_notifications', 'low_stock_alerts',
                    'notification_frequency']
    list_filter = ['email_notifications', 'browser_notifications', 'notification_frequency']
    search_fields = ['user__username', 'user__email']
    ordering = ['user__username']


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'is_active', 'created_at']
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'subject_template', 'message_template']
    ordering = ['name']