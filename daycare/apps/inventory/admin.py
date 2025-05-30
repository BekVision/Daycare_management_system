from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, F
from django.utils import timezone
from datetime import date

from .models import IngredientCategory, Ingredient, Stock, StockTransaction


@admin.register(IngredientCategory)
class IngredientCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'ingredient_count', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']
    list_editable = ['display_order', 'is_active']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'description')
        }),
        ('Sozlamalar', {
            'fields': ('display_order', 'is_active')
        }),
    )

    def ingredient_count(self, obj):
        """Kategoriya ichidagi ingredientlar soni"""
        count = obj.ingredients.filter(is_active=True).count()
        if count > 0:
            url = reverse('admin:inventory_ingredient_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} ta</a>', url, count)
        return '0 ta'

    ingredient_count.short_description = 'Ingredientlar soni'
    ingredient_count.admin_order_field = 'ingredients__count'


class StockInline(admin.StackedInline):
    model = Stock
    extra = 0
    readonly_fields = ['last_updated']
    fields = [
        'current_quantity', 'reserved_quantity',
        'last_restock_date', 'expiry_date',
        'last_updated_by', 'last_updated'
    ]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'unit', 'category', 'current_stock', 'stock_status',
        'cost_per_unit', 'is_active', 'created_at'
    ]
    list_filter = [
        'category', 'is_active', 'created_at',
        ('stock__current_quantity', admin.EmptyFieldListFilter)
    ]
    search_fields = ['name', 'description', 'barcode']
    ordering = ['name']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [StockInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'unit', 'category', 'description')
        }),
        ('Zaxira sozlamalari', {
            'fields': ('min_threshold', 'max_threshold')
        }),
        ('Moliyaviy ma\'lumotlar', {
            'fields': ('cost_per_unit', 'barcode')
        }),
        ('Sozlamalar', {
            'fields': ('is_active', 'created_by')
        }),
        ('Vaqt ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def current_stock(self, obj):
        """Joriy zaxira miqdori"""
        try:
            stock = obj.stock
            quantity = stock.current_quantity
            if quantity <= obj.min_threshold:
                return format_html(
                    '<span style="color: red; font-weight: bold;">{} {}</span>',
                    quantity, obj.unit
                )
            return f'{quantity} {obj.unit}'
        except Stock.DoesNotExist:
            return format_html('<span style="color: gray;">Zaxira yo\'q</span>')

    current_stock.short_description = 'Joriy zaxira'
    current_stock.admin_order_field = 'stock__current_quantity'

    def stock_status(self, obj):
        """Zaxira holati"""
        try:
            stock = obj.stock
            if stock.current_quantity <= 0:
                return format_html('<span style="color: red;">❌ Tugagan</span>')
            elif stock.current_quantity <= obj.min_threshold:
                return format_html('<span style="color: orange;">⚠️ Kam</span>')
            elif obj.max_threshold and stock.current_quantity >= obj.max_threshold:
                return format_html('<span style="color: blue;">📦 Ko\'p</span>')
            else:
                return format_html('<span style="color: green;">✅ Yaxshi</span>')
        except Stock.DoesNotExist:
            return format_html('<span style="color: gray;">❓ Noma\'lum</span>')

    stock_status.short_description = 'Holat'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'stock', 'created_by')

    def save_model(self, request, obj, form, change):
        if not change:  # Yangi yaratilganda
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

        # Agar Stock mavjud bo'lmasa, yaratish
        if not hasattr(obj, 'stock'):
            Stock.objects.create(
                ingredient=obj,
                current_quantity=0,
                reserved_quantity=0,
                last_updated_by=request.user
            )


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = [
        'ingredient', 'current_quantity_display', 'reserved_quantity',
        'stock_status', 'expiry_status', 'last_restock_date', 'last_updated'
    ]
    list_filter = [
        'last_restock_date', 'expiry_date', 'last_updated',
        ('expiry_date', admin.DateFieldListFilter)
    ]
    search_fields = ['ingredient__name', 'ingredient__category__name']
    ordering = ['ingredient__name']
    readonly_fields = ['last_updated']

    fieldsets = (
        ('Ingredient ma\'lumotlari', {
            'fields': ('ingredient',)
        }),
        ('Zaxira ma\'lumotlari', {
            'fields': ('current_quantity', 'reserved_quantity')
        }),
        ('Sanalar', {
            'fields': ('last_restock_date', 'expiry_date')
        }),
        ('Oxirgi yangilanish', {
            'fields': ('last_updated_by', 'last_updated'),
            'classes': ('collapse',)
        }),
    )

    def current_quantity_display(self, obj):
        """Joriy miqdorni rangli ko'rsatish"""
        quantity = obj.current_quantity
        unit = obj.ingredient.unit
        threshold = obj.ingredient.min_threshold

        if quantity <= 0:
            color = 'red'
            icon = '❌'
        elif quantity <= threshold:
            color = 'orange'
            icon = '⚠️'
        else:
            color = 'green'
            icon = '✅'

        return format_html(
            '<span style="color: {};">{} {} {}</span>',
            color, icon, quantity, unit
        )

    current_quantity_display.short_description = 'Joriy miqdor'
    current_quantity_display.admin_order_field = 'current_quantity'

    def stock_status(self, obj):
        """Zaxira holati"""
        if obj.current_quantity <= 0:
            return format_html('<span style="color: red; font-weight: bold;">TUGAGAN</span>')
        elif obj.current_quantity <= obj.ingredient.min_threshold:
            return format_html('<span style="color: orange; font-weight: bold;">KAM</span>')
        else:
            return format_html('<span style="color: green;">YAXSHI</span>')

    stock_status.short_description = 'Holat'

    def expiry_status(self, obj):
        """Muddat holati"""
        if not obj.expiry_date:
            return format_html('<span style="color: gray;">Belgilanmagan</span>')

        today = date.today()
        days_left = (obj.expiry_date - today).days

        if days_left < 0:
            return format_html('<span style="color: red; font-weight: bold;">❌ MUDDATI O\'TGAN</span>')
        elif days_left <= 7:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ {} kun qoldi</span>', days_left)
        elif days_left <= 30:
            return format_html('<span style="color: blue;">📅 {} kun qoldi</span>', days_left)
        else:
            return format_html('<span style="color: green;">✅ {} kun qoldi</span>', days_left)

    expiry_status.short_description = 'Muddat holati'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ingredient', 'ingredient__category', 'last_updated_by')


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'ingredient', 'transaction_type_display', 'quantity_display',
        'total_cost', 'supplier', 'created_by', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'created_at', 'supplier',
        ('expiry_date', admin.DateFieldListFilter)
    ]
    search_fields = [
        'ingredient__name', 'supplier', 'invoice_number',
        'reference_id', 'notes'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('ingredient', 'transaction_type', 'quantity')
        }),
        ('Moliyaviy ma\'lumotlar', {
            'fields': ('unit_cost', 'total_cost')
        }),
        ('Tashqi ma\'lumotlar', {
            'fields': ('supplier', 'invoice_number', 'expiry_date')
        }),
        ('Reference ma\'lumotlar', {
            'fields': ('reference_type', 'reference_id'),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha', {
            'fields': ('notes',)
        }),
        ('Yaratuvchi', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def transaction_type_display(self, obj):
        """Tranzaksiya turini rangli ko'rsatish"""
        colors = {
            'IN': 'green',
            'OUT': 'orange',
            'ADJUSTMENT': 'blue',
            'WASTE': 'red',
            'TRANSFER': 'purple'
        }
        icons = {
            'IN': '📥',
            'OUT': '📤',
            'ADJUSTMENT': '⚖️',
            'WASTE': '🗑️',
            'TRANSFER': '🔄'
        }

        color = colors.get(obj.transaction_type, 'black')
        icon = icons.get(obj.transaction_type, '❓')

        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, obj.get_transaction_type_display()
        )

    transaction_type_display.short_description = 'Tranzaksiya turi'
    transaction_type_display.admin_order_field = 'transaction_type'

    def quantity_display(self, obj):
        """Miqdorni birlik bilan ko'rsatish"""
        return f'{obj.quantity} {obj.ingredient.unit}'

    quantity_display.short_description = 'Miqdor'
    quantity_display.admin_order_field = 'quantity'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ingredient', 'created_by')

    def save_model(self, request, obj, form, change):
        if not change:  # Yangi yaratilganda
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Custom admin actions
@admin.action(description='Tanlangan ingredientlarni faollashtirish')
def activate_ingredients(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f'{updated} ta ingredient faollashtirildi.')


@admin.action(description='Tanlangan ingredientlarni o\'chirish')
def deactivate_ingredients(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f'{updated} ta ingredient o\'chirildi.')


# Admin action larni qo'shish
IngredientAdmin.actions = [activate_ingredients, deactivate_ingredients]

# Admin site customization
admin.site.site_header = "Bog'cha Tizimi - Inventory Admin"
admin.site.site_title = "Inventory Admin"
admin.site.index_title = "Inventory boshqaruvi"