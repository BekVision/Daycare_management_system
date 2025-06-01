from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import MealService, ServiceLog, ServiceFeedback


class ServiceLogInline(admin.TabularInline):
    model = ServiceLog
    extra = 0
    readonly_fields = ('created_at',)
    fields = (
        'ingredient', 'quantity_planned', 'quantity_used',
        'stock_before', 'stock_after', 'unit_cost', 'total_cost',
        'waste_quantity', 'notes'
    )


class ServiceFeedbackInline(admin.TabularInline):
    model = ServiceFeedback
    extra = 0
    readonly_fields = ('created_at', 'feedback_by')
    fields = (
        'feedback_by', 'taste_rating', 'portion_rating',
        'overall_rating', 'comments', 'created_at'
    )


@admin.register(MealService)
class MealServiceAdmin(admin.ModelAdmin):
    list_display = (
        'meal', 'service_date', 'service_time', 'meal_type',
        'portions_planned', 'portions_served', 'status_badge',
        'served_by', 'total_cost'
    )
    list_filter = (
        'status', 'meal_type', 'service_date', 'served_by',
        'created_at'
    )
    search_fields = (
        'meal__name', 'served_by__username', 'served_by__first_name',
        'served_by__last_name', 'notes'
    )
    date_hierarchy = 'service_date'
    readonly_fields = (
        'created_at', 'updated_at', 'served_at', 'total_cost'
    )

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': (
                'meal', 'portions_planned', 'portions_served',
                'service_date', 'service_time', 'meal_type'
            )
        }),
        ('Holat', {
            'fields': ('status', 'served_by', 'served_at')
        }),
        ('Xarajatlar', {
            'fields': ('total_cost', 'waste_quantity')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    inlines = [ServiceLogInline, ServiceFeedbackInline]

    def status_badge(self, obj):
        colors = {
            'PLANNED': '#6c757d',
            'PREPARING': '#ffc107',
            'READY': '#17a2b8',
            'SERVED': '#28a745',
            'CANCELLED': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Holat'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'meal', 'served_by', 'created_by'
        )

    def save_model(self, request, obj, form, change):
        if not change:  # Yangi obyekt
            obj.created_by = request.user
            if not obj.served_by:
                obj.served_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ServiceLog)
class ServiceLogAdmin(admin.ModelAdmin):
    list_display = (
        'meal_service', 'ingredient', 'quantity_planned',
        'quantity_used', 'stock_before', 'stock_after',
        'total_cost', 'created_at'
    )
    list_filter = (
        'meal_service__meal', 'ingredient__category',
        'created_at', 'meal_service__service_date'
    )
    search_fields = (
        'meal_service__meal__name', 'ingredient__name', 'notes'
    )
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': (
                'meal_service', 'ingredient', 'quantity_planned',
                'quantity_used', 'waste_quantity'
            )
        }),
        ('Zaxira ma\'lumotlari', {
            'fields': ('stock_before', 'stock_after')
        }),
        ('Narx ma\'lumotlari', {
            'fields': ('unit_cost', 'total_cost')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes', 'created_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'meal_service__meal', 'ingredient'
        )


@admin.register(ServiceFeedback)
class ServiceFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'meal_service', 'feedback_by', 'overall_rating',
        'taste_rating', 'portion_rating', 'created_at'
    )
    list_filter = (
        'overall_rating', 'taste_rating', 'portion_rating',
        'created_at', 'meal_service__meal'
    )
    search_fields = (
        'meal_service__meal__name', 'feedback_by__username',
        'feedback_by__first_name', 'feedback_by__last_name',
        'comments'
    )
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('meal_service', 'feedback_by')
        }),
        ('Baholash', {
            'fields': (
                'overall_rating', 'taste_rating', 'portion_rating'
            )
        }),
        ('Izohlar', {
            'fields': ('comments', 'created_at')
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'meal_service__meal', 'feedback_by'
        )


# Django admin customization
admin.site.site_header = "Bog'cha Ombor Tizimi"
admin.site.site_title = "Bog'cha Admin"
admin.site.index_title = "Boshqaruv Paneli"