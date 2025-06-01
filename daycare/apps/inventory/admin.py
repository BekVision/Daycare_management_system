from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import IngredientCategory, Ingredient, Stock, StockTransaction


@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'ingredient_count', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['display_order', 'is_active']
    ordering = ['display_order', 'name']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'description')
        }),
        ('Sozlamalar', {
            'fields': ('display_order', 'is_active')
        }),
    )

    def ingredient_count(self, obj):
        count = obj.ingredients.count()
        if count > 0:
            return format_html(
                '<a href="{}?category__id__exact={}">{} ta</a>',
                reverse('admin:inventory_ingredient_changelist'),
                obj.id,
                count
            )
        return '0 ta'

    ingredient_count.short_description = 'Ingredientlar soni'


class StockInline(admin.StackedInline):
    model = Stock
    extra = 0
    readonly_fields = ['last_updated']
    fields = ['current_quantity', 'reserved_quantity', 'last_restock_date', 'expiry_date', 'last_updated_by']


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit', 'current_stock', 'stock_status', 'cost_per_unit', 'is_active']
    list_filter = ['category', 'unit', 'is_active', 'created_at']
    search_fields = ['name', 'barcode', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [StockInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'category', 'unit', 'description')
        }),
        ('Zaxira sozlamalari', {
            'fields': ('min_threshold', 'max_threshold', 'cost_per_unit')
        }),
        ('Qo\'shimcha', {
            'fields': ('barcode', 'is_active')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def current_stock(self, obj):
        try:
            return f"{obj.stock.current_quantity} {obj.unit}"
        except Stock.DoesNotExist:
            return "Mavjud emas"

    current_stock.short_description = 'Joriy zaxira'

    def stock_status(self, obj):
        try:
            stock = obj.stock
            available = stock.available_quantity()
            if available <= 0:
                return format_html('<span style="color: red;">Tugagan</span>')
            elif available <= obj.min_threshold:
                return format_html('<span style="color: orange;">Kam</span>')
            else:
                return format_html('<span style="color: green;">Yetarli</span>')
        except Stock.DoesNotExist:
            return format_html('<span style="color: gray;">-</span>')

    stock_status.short_description = 'Holati'

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('created_by',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['activate_ingredients', 'deactivate_ingredients']

    def activate_ingredients(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} ta ingredient faollashtirildi.')

    activate_ingredients.short_description = "Tanlangan ingredientlarni faollashtirish"

    def deactivate_ingredients(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} ta ingredient o\'chirildi.')

    deactivate_ingredients.short_description = "Tanlangan ingredientlarni o'chirish"


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['ingredient', 'current_quantity', 'available_quantity_display', 'reserved_quantity',
                    'stock_status', 'expiry_status', 'last_updated']
    list_filter = ['last_restock_date', 'expiry_date', 'last_updated']
    search_fields = ['ingredient__name']
    readonly_fields = ['last_updated']

    fieldsets = (
        ('Ingredient', {
            'fields': ('ingredient',)
        }),
        ('Miqdorlar', {
            'fields': ('current_quantity', 'reserved_quantity')
        }),
        ('Sanalar', {
            'fields': ('last_restock_date', 'expiry_date')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('last_updated_by', 'last_updated')
        }),
    )

    def available_quantity_display(self, obj):
        available = obj.available_quantity()
        return f"{available} {obj.ingredient.unit}"

    available_quantity_display.short_description = 'Mavjud miqdor'

    def stock_status(self, obj):
        available = obj.available_quantity()
        if available <= 0:
            return format_html('<span style="color: red; font-weight: bold;">Tugagan</span>')
        elif available <= obj.ingredient.min_threshold:
            return format_html('<span style="color: orange; font-weight: bold;">Kam</span>')
        else:
            return format_html('<span style="color: green;">Yetarli</span>')

    stock_status.short_description = 'Holati'

    def expiry_status(self, obj):
        if not obj.expiry_date:
            return "-"

        days = obj.days_until_expiry()
        if days < 0:
            return format_html('<span style="color: red;">Muddati tugagan</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} kun qoldi</span>', days)
        else:
            return format_html('<span style="color: green;">{} kun qoldi</span>', days)

    expiry_status.short_description = 'Muddat holati'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ingredient', 'last_updated_by')


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['ingredient', 'transaction_type', 'quantity', 'unit_cost', 'total_cost',
                    'supplier', 'created_by', 'created_at']
    list_filter = ['transaction_type', 'created_at', 'supplier']
    search_fields = ['ingredient__name', 'supplier', 'invoice_number', 'notes']
    readonly_fields = ['total_cost', 'created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Tranzaksiya ma\'lumotlari', {
            'fields': ('ingredient', 'transaction_type', 'quantity')
        }),
        ('Moliyaviy ma\'lumotlar', {
            'fields': ('unit_cost', 'total_cost'),
            'classes': ('collapse',)
        }),
        ('Tashqi ma\'lumotlar', {
            'fields': ('reference_type', 'reference_id', 'supplier', 'invoice_number'),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha', {
            'fields': ('expiry_date', 'notes')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('ingredient', 'transaction_type', 'quantity', 'created_by')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ingredient', 'created_by')

    actions = ['export_transactions']

    def export_transactions(self, request, queryset):
        # CSV export funksiyasi (sodda versiya)
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="stock_transactions.csv"'

        writer = csv.writer(response)
        writer.writerow(['Ingredient', 'Tur', 'Miqdor', 'Birlik narx', 'Jami', 'Supplier', 'Sana'])

        for transaction in queryset:
            writer.writerow([
                transaction.ingredient.name,
                transaction.get_transaction_type_display(),
                transaction.quantity,
                transaction.unit_cost or '',
                transaction.total_cost or '',
                transaction.supplier or '',
                transaction.created_at.strftime('%d.%m.%Y %H:%M')
            ])

        return response

    export_transactions.short_description = "Tanlangan tranzaksiyalarni CSV ga eksport qilish"


# Admin site customization
admin.site.site_header = 'Bog\'cha Ombor Boshqaruvi'
admin.site.site_title = 'Ombor Admin'
admin.site.index_title = 'Ombor Boshqaruv Paneli'