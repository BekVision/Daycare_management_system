# reports/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import DailyReport, MonthlyReport, IngredientUsageReport


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_date', 'total_meals_served', 'total_portions_served',
        'efficiency_display', 'waste_display', 'total_cost', 'generated_by', 'generated_at'
    ]
    list_filter = ['report_date', 'generated_by', 'generated_at']
    search_fields = ['report_date']
    ordering = ['-report_date']
    readonly_fields = ['generated_at']
    date_hierarchy = 'report_date'

    def efficiency_display(self, obj):
        if obj.efficiency_percentage:
            color = 'green' if obj.efficiency_percentage >= 80 else 'orange' if obj.efficiency_percentage >= 60 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.efficiency_percentage
            )
        return '-'

    efficiency_display.short_description = 'Samaradorlik'

    def waste_display(self, obj):
        if obj.waste_percentage:
            color = 'red' if obj.waste_percentage >= 10 else 'orange' if obj.waste_percentage >= 5 else 'green'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.waste_percentage
            )
        return '-'

    waste_display.short_description = 'Chiqindi'

    actions = ['regenerate_reports']

    def regenerate_reports(self, request, queryset):
        # Hisobotlarni qayta yaratish funktsiyasi
        count = queryset.count()
        self.message_user(request, f'{count} ta hisobot qayta yaratildi.')

    regenerate_reports.short_description = 'Hisobotlarni qayta yaratish'


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = [
        'report_month', 'total_meals_served', 'total_portions_served',
        'efficiency_display', 'waste_display', 'cost_per_portion', 'generated_by'
    ]
    list_filter = ['report_month', 'generated_by']
    search_fields = ['report_month']
    ordering = ['-report_month']
    readonly_fields = ['generated_at']
    date_hierarchy = 'report_month'

    def efficiency_display(self, obj):
        if obj.efficiency_percentage:
            color = 'green' if obj.efficiency_percentage >= 80 else 'orange' if obj.efficiency_percentage >= 60 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.efficiency_percentage
            )
        return '-'

    efficiency_display.short_description = 'Samaradorlik'

    def waste_display(self, obj):
        if obj.waste_percentage:
            color = 'red' if obj.waste_percentage >= 10 else 'orange' if obj.waste_percentage >= 5 else 'green'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.waste_percentage
            )
        return '-'

    waste_display.short_description = 'Chiqindi'


@admin.register(IngredientUsageReport)
class IngredientUsageReportAdmin(admin.ModelAdmin):
    list_display = [
        'ingredient', 'report_date', 'opening_stock', 'stock_used',
        'stock_waste', 'closing_stock', 'usage_display', 'total_cost'
    ]
    list_filter = ['report_date', 'ingredient__category', 'created_at']
    search_fields = ['ingredient__name', 'report_date']
    ordering = ['-report_date', 'ingredient__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'report_date'

    def usage_display(self, obj):
        if obj.usage_percentage:
            color = 'red' if obj.usage_percentage >= 90 else 'orange' if obj.usage_percentage >= 70 else 'green'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.usage_percentage
            )
        return '-'

    usage_display.short_description = 'Ishlatilish'