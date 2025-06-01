from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F, Sum, Count, Avg, When, Value, Case, IntegerField, CharField, DecimalField
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from apps.accounts.decorators import chef_required, admin_or_manager_required
from .models import IngredientCategory, Ingredient, Stock, StockTransaction
from .forms import (IngredientCategoryForm, IngredientForm, StockForm,
                    StockTransactionForm, StockAdjustmentForm,
                    InventorySearchForm, TransactionFilterForm)
from .utils import log_inventory_activity, check_low_stock, send_stock_alert
from .forms import StockUpdateForm


@chef_required
def inventory_dashboard(request):
    """Ombor bosh sahifasi"""

    # Asosiy statistika
    stats = {
        'total_ingredients': Ingredient.objects.filter(is_active=True).count(),
        'total_categories': IngredientCategory.objects.filter(is_active=True).count(),
        'low_stock_count': 0,
        'out_of_stock_count': 0,
        'expiring_soon_count': 0,
        'total_value': 0,
    }

    # Kam zaxira va tugagan mahsulotlar
    for ingredient in Ingredient.objects.filter(is_active=True):
        if ingredient.is_out_of_stock():
            stats['out_of_stock_count'] += 1
        elif ingredient.is_low_stock():
            stats['low_stock_count'] += 1

    # Muddati tugayotgan mahsulotlar (7 kun ichida)
    expiring_stocks = Stock.objects.filter(
        expiry_date__lte=timezone.now().date() + timedelta(days=7),
        expiry_date__gte=timezone.now().date()
    )
    stats['expiring_soon_count'] = expiring_stocks.count()

    # Jami qiymat (taxminiy)
    total_value = Decimal('0')
    for ingredient in Ingredient.objects.filter(is_active=True, cost_per_unit__isnull=False):
        try:
            stock_quantity = ingredient.stock.current_quantity
            # Both values converted to Decimal for safe multiplication
            quantity_decimal = Decimal(str(stock_quantity)) if not isinstance(stock_quantity,
                                                                              Decimal) else stock_quantity
            cost_decimal = Decimal(str(ingredient.cost_per_unit)) if not isinstance(ingredient.cost_per_unit,
                                                                                    Decimal) else ingredient.cost_per_unit

            total_value += quantity_decimal * cost_decimal
        except Stock.DoesNotExist:
            pass
    stats['total_value'] = total_value
    # total_value = 0
    # for ingredient in Ingredient.objects.filter(is_active=True, cost_per_unit__isnull=False):
    #     try:
    #         stock_quantity = ingredient.stock.current_quantity
    #         total_value += stock_quantity * ingredient.cost_per_unit
    #     except Stock.DoesNotExist:
    #         pass
    # stats['total_value'] = total_value

    # So'nggi tranzaksiyalar
    recent_transactions = StockTransaction.objects.select_related(
        'ingredient', 'created_by'
    ).order_by('-created_at')[:10]

    # Kategoriya bo'yicha statistika
    category_stats = []
    for category in IngredientCategory.objects.filter(is_active=True):
        cat_ingredients = category.ingredients.filter(is_active=True)
        category_stats.append({
            'category': category,
            'ingredient_count': cat_ingredients.count(),
            'low_stock_count': sum(1 for ing in cat_ingredients if ing.is_low_stock()),
        })

    context = {
        'stats': stats,
        'recent_transactions': recent_transactions,
        'category_stats': category_stats,
        'expiring_stocks': expiring_stocks[:5],
    }

    return render(request, 'inventory/dashboard.html', context)


@chef_required
def ingredient_list(request):
    """Ingredientlar ro'yxati"""
    form = InventorySearchForm(request.GET)
    ingredients = Ingredient.objects.select_related('category').prefetch_related('stock')

    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            ingredients = ingredients.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        category = form.cleaned_data.get('category')
        if category:
            ingredients = ingredients.filter(category=category)

        stock_status = form.cleaned_data.get('stock_status')
        if stock_status == 'available':
            ingredients = [ing for ing in ingredients if not ing.is_low_stock() and not ing.is_out_of_stock()]
        elif stock_status == 'low':
            ingredients = [ing for ing in ingredients if ing.is_low_stock()]
        elif stock_status == 'out':
            ingredients = [ing for ing in ingredients if ing.is_out_of_stock()]

        unit = form.cleaned_data.get('unit')
        if unit:
            ingredients = ingredients.filter(unit__icontains=unit)

    # Pagination
    paginator = Paginator(ingredients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'total_count': len(ingredients) if isinstance(ingredients, list) else ingredients.count(),
    }

    return render(request, 'inventory/ingredient_list.html', context)


@chef_required
def ingredient_detail(request, ingredient_id):
    """Ingredient detali"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    # So'nggi tranzaksiyalar
    transactions = ingredient.transactions.select_related('created_by').order_by('-created_at')[:20]

    # Statistika
    last_30_days = timezone.now().date() - timedelta(days=30)
    stats = {
        'total_in': ingredient.transactions.filter(
            transaction_type='IN',
            created_at__date__gte=last_30_days
        ).aggregate(total=Sum('quantity'))['total'] or 0,

        'total_out': ingredient.transactions.filter(
            transaction_type='OUT',
            created_at__date__gte=last_30_days
        ).aggregate(total=Sum('quantity'))['total'] or 0,

        'avg_cost': ingredient.transactions.filter(
            unit_cost__isnull=False
        ).aggregate(avg=Avg('unit_cost'))['avg'] or 0,
    }

    context = {
        'ingredient': ingredient,
        'transactions': transactions,
        'stats': stats,
    }

    return render(request, 'inventory/ingredient_detail.html', context)


@chef_required
def ingredient_create(request):
    """Yangi ingredient yaratish"""
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.created_by = request.user
            ingredient.save()

            # Stock yaratish
            stock, created = Stock.objects.get_or_create(
                ingredient=ingredient,
                defaults={
                    'current_quantity': 0,
                    'last_updated': timezone.now()
                }
            )
            # Stock.objects.create(
            #     ingredient=ingredient,
            #     last_updated_by=request.user
            # )

            # Activity log
            log_inventory_activity(
                user=request.user,
                action='INGREDIENT_CREATED',
                ingredient=ingredient,
                request=request
            )

            messages.success(request, f'{ingredient.name} muvaffaqiyatli yaratildi')
            return redirect('inventory:ingredient_detail', ingredient_id=ingredient.id)
    else:
        form = IngredientForm()

    context = {
        'form': form,
        'title': 'Yangi ingredient qo\'shish'
    }
    return render(request, 'inventory/ingredient_form.html', context)


@chef_required
def ingredient_edit(request, ingredient_id):
    """Ingredient tahrirlash"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()

            # Activity log
            log_inventory_activity(
                user=request.user,
                action='INGREDIENT_UPDATED',
                ingredient=ingredient,
                request=request
            )

            messages.success(request, f'{ingredient.name} muvaffaqiyatli yangilandi')
            return redirect('inventory:ingredient_detail', ingredient_id=ingredient.id)
    else:
        form = IngredientForm(instance=ingredient)

    context = {
        'form': form,
        'ingredient': ingredient,
        'title': f'{ingredient.name} ni tahrirlash'
    }
    return render(request, 'inventory/ingredient_form.html', context)


@admin_or_manager_required
def ingredient_delete(request, ingredient_id):
    """Ingredient o'chirish"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    if request.method == 'POST':
        ingredient_name = ingredient.name
        ingredient.is_active = False
        ingredient.save()

        # Activity log
        log_inventory_activity(
            user=request.user,
            action='INGREDIENT_DELETED',
            ingredient=ingredient,
            request=request
        )

        messages.success(request, f'{ingredient_name} o\'chirildi')
        return redirect('inventory:ingredient_list')

    context = {
        'ingredient': ingredient,
    }
    return render(request, 'inventory/ingredient_confirm_delete.html', context)


@chef_required
def stock_update(request, ingredient_id):
    """Stock yangilash"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    stock, created = Stock.objects.get_or_create(
        ingredient=ingredient,
        defaults={'last_updated_by': request.user}
    )

    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.last_updated_by = request.user
            stock.save()

            # Activity log
            log_inventory_activity(
                user=request.user,
                action='STOCK_UPDATED',
                ingredient=ingredient,
                request=request
            )

            messages.success(request, f'{ingredient.name} zaxirasi yangilandi')
            return redirect('inventory:ingredient_detail', ingredient_id=ingredient.id)
    else:
        form = StockForm(instance=stock)

    context = {
        'form': form,
        'ingredient': ingredient,
        'stock': stock,
    }
    return render(request, 'inventory/stock_form.html', context)


@chef_required
def transaction_create(request):
    """Yangi tranzaksiya yaratish"""
    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()  # save() metodi avtomatik stock ni yangilaydi

            # Activity log
            log_inventory_activity(
                user=request.user,
                action='TRANSACTION_CREATED',
                ingredient=transaction.ingredient,
                request=request,
                extra_data={
                    'transaction_type': transaction.transaction_type,
                    'quantity': transaction.quantity
                }
            )

            # Kam zaxira ogohlantirishi
            if transaction.ingredient.is_low_stock():
                send_stock_alert(transaction.ingredient, 'low_stock')

            messages.success(request, 'Tranzaksiya muvaffaqiyatli yaratildi')
            return redirect('inventory:transaction_list')
    else:
        form = StockTransactionForm()

    context = {
        'form': form,
        'title': 'Yangi tranzaksiya'
    }
    return render(request, 'inventory/transaction_form.html', context)


@chef_required
def transaction_list(request):
    """Tranzaksiyalar ro'yxati"""
    form = TransactionFilterForm(request.GET)
    transactions = StockTransaction.objects.select_related('ingredient', 'created_by')

    # Filtrlash
    if form.is_valid():
        ingredient = form.cleaned_data.get('ingredient')
        if ingredient:
            transactions = transactions.filter(ingredient=ingredient)

        transaction_type = form.cleaned_data.get('transaction_type')
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)

        supplier = form.cleaned_data.get('supplier')
        if supplier:
            transactions = transactions.filter(supplier__icontains=supplier)

        date_from = form.cleaned_data.get('date_from')
        if date_from:
            transactions = transactions.filter(created_at__date__gte=date_from)

        date_to = form.cleaned_data.get('date_to')
        if date_to:
            transactions = transactions.filter(created_at__date__lte=date_to)

    transactions = transactions.order_by('-created_at')

    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
    }

    return render(request, 'inventory/transaction_list.html', context)


@chef_required
def category_list(request):
    """Kategoriyalar ro'yxati"""
    categories = IngredientCategory.objects.annotate(
        ingredient_count=Count('ingredients')
    ).order_by('display_order', 'name')

    context = {
        'categories': categories,
    }
    return render(request, 'inventory/category_list.html', context)


@admin_or_manager_required
def category_create(request):
    """Yangi kategoriya yaratish"""
    if request.method == 'POST':
        form = IngredientCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()

            # Activity log
            log_inventory_activity(
                user=request.user,
                action='CATEGORY_CREATED',
                request=request,
                extra_data={'category_name': category.name}
            )

            messages.success(request, f'{category.name} kategoriyasi yaratildi')
            return redirect('inventory:category_list')
    else:
        form = IngredientCategoryForm()

    context = {
        'form': form,
        'title': 'Yangi kategoriya'
    }
    return render(request, 'inventory/category_form.html', context)


@admin_or_manager_required
def category_edit(request, category_id):
    """Kategoriya tahrirlash"""
    category = get_object_or_404(IngredientCategory, id=category_id)

    if request.method == 'POST':
        form = IngredientCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()

            # Activity log
            log_inventory_activity(
                user=request.user,
                action='CATEGORY_UPDATED',
                request=request,
                extra_data={'category_name': category.name}
            )

            messages.success(request, f'{category.name} kategoriyasi yangilandi')
            return redirect('inventory:category_list')
    else:
        form = IngredientCategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'title': f'{category.name} ni tahrirlash'
    }
    return render(request, 'inventory/category_form.html', context)


@chef_required
def stock_adjustment(request):
    """Stock tuzatish"""
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            ingredient = form.cleaned_data['ingredient']
            new_quantity = form.cleaned_data['new_quantity']
            reason = form.cleaned_data['reason']

            # Tranzaksiya yaratish
            transaction = StockTransaction.objects.create(
                ingredient=ingredient,
                transaction_type='ADJUSTMENT',
                quantity=new_quantity,
                notes=reason,
                created_by=request.user
            )

            messages.success(request, f'{ingredient.name} zaxirasi tuzatildi')
            return redirect('inventory:ingredient_detail', ingredient_id=ingredient.id)
    else:
        form = StockAdjustmentForm()

    context = {
        'form': form,
        'title': 'Zaxira tuzatish'
    }
    return render(request, 'inventory/stock_adjustment.html', context)


@chef_required
def low_stock_report(request):
    """Kam zaxira hisoboti"""
    low_stock_ingredients = []

    for ingredient in Ingredient.objects.filter(is_active=True):
        if ingredient.is_low_stock():
            low_stock_ingredients.append({
                'ingredient': ingredient,
                'current_stock': ingredient.available_quantity(),
                'min_threshold': ingredient.min_threshold,
                'shortage': ingredient.min_threshold - ingredient.available_quantity(),
            })

    # Sortlash - eng kam zaxira birinchi
    low_stock_ingredients.sort(key=lambda x: x['shortage'], reverse=True)

    context = {
        'low_stock_ingredients': low_stock_ingredients,
    }
    return render(request, 'inventory/low_stock_report.html', context)


@chef_required
def expiry_report(request):
    """Muddati tugayotgan mahsulotlar hisoboti"""
    today = timezone.now().date()

    # Muddati tugagan
    expired_stocks = Stock.objects.filter(
        expiry_date__lt=today,
        current_quantity__gt=0
    ).select_related('ingredient')

    # 7 kun ichida tugayotgan
    expiring_soon = Stock.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=7),
        current_quantity__gt=0
    ).select_related('ingredient')

    # 30 kun ichida tugayotgan
    expiring_month = Stock.objects.filter(
        expiry_date__gt=today + timedelta(days=7),
        expiry_date__lte=today + timedelta(days=30),
        current_quantity__gt=0
    ).select_related('ingredient')

    context = {
        'expired_stocks': expired_stocks,
        'expiring_soon': expiring_soon,
        'expiring_month': expiring_month,
    }
    return render(request, 'inventory/expiry_report.html', context)


# API Views
@chef_required
def ingredient_api(request):
    """Ingredient API (AJAX uchun)"""
    search = request.GET.get('q', '')
    ingredients = Ingredient.objects.filter(
        is_active=True,
        name__icontains=search
    )[:10]

    data = [
        {
            'id': ing.id,
            'name': ing.name,
            'unit': ing.unit,
            'current_stock': ing.available_quantity(),
            'min_threshold': ing.min_threshold,
        }
        for ing in ingredients
    ]

    return JsonResponse({'ingredients': data})


@chef_required
def stock_status_api(request, ingredient_id):
    """Ingredient stock holati API"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)

    data = {
        'ingredient_id': ingredient.id,
        'name': ingredient.name,
        'unit': ingredient.unit,
        'current_stock': ingredient.available_quantity(),
        'min_threshold': ingredient.min_threshold,
        'max_threshold': ingredient.max_threshold,
        'is_low_stock': ingredient.is_low_stock(),
        'is_out_of_stock': ingredient.is_out_of_stock(),
    }

    try:
        stock = ingredient.stock
        data.update({
            'reserved_quantity': stock.reserved_quantity,
            'expiry_date': stock.expiry_date.isoformat() if stock.expiry_date else None,
            'last_updated': stock.last_updated.isoformat(),
        })
    except Stock.DoesNotExist:
        pass

    return JsonResponse(data)


@admin_or_manager_required
def stock_list(request):
    """Barcha stock ma'lumotlarini ko'rsatish"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')

    # Base queryset
    stocks = Stock.objects.select_related('ingredient', 'ingredient__category').filter(
        ingredient__is_active=True
    )

    # Search filter
    if search_query:
        stocks = stocks.filter(
            Q(ingredient__name__icontains=search_query) |
            Q(ingredient__barcode__icontains=search_query)
        )

    # Category filter
    if category_filter:
        stocks = stocks.filter(ingredient__category_id=category_filter)

    # Status filter
    if status_filter == 'low':
        stocks = stocks.filter(current_quantity__lte=F('ingredient__min_threshold'))
    elif status_filter == 'out':
        stocks = stocks.filter(current_quantity=0)
    elif status_filter == 'normal':
        stocks = stocks.filter(current_quantity__gt=F('ingredient__min_threshold'))

    # Annotate with calculated fields
    stocks = stocks.annotate(
        status=Case(
            When(current_quantity=0, then=Value('out_of_stock')),
            When(current_quantity__lte=F('ingredient__min_threshold'), then=Value('low_stock')),
            default=Value('normal'),
            output_field=CharField()
        ),
        total_value=Case(
            When(ingredient__cost_per_unit__isnull=False,
                 then=F('current_quantity') * F('ingredient__cost_per_unit')),
            default=Value(0),
            output_field=DecimalField()
        )
    ).order_by('ingredient__name')

    # Pagination
    paginator = Paginator(stocks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    total_items = stocks.count()
    low_stock_count = stocks.filter(current_quantity__lte=F('ingredient__min_threshold')).count()
    out_of_stock_count = stocks.filter(current_quantity=0).count()
    total_value = stocks.aggregate(
        total=Sum('total_value', default=0)
    )['total']

    # Categories for filter
    from .models import IngredientCategory
    categories = IngredientCategory.objects.filter(is_active=True).order_by('name')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': categories,
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_value': total_value,
        'title': 'Stock Ma\'lumotlari'
    }

    return render(request, 'inventory/stock_list.html', context)


@admin_or_manager_required
def stock_detail(request, ingredient_id):
    """Ingredient stock detallari"""
    ingredient = get_object_or_404(Ingredient, id=ingredient_id, is_active=True)
    stock = get_object_or_404(Stock, ingredient=ingredient)

    # Recent transactions
    recent_transactions = StockTransaction.objects.filter(
        ingredient=ingredient
    ).select_related('created_by').order_by('-created_at')[:10]

    context = {
        'ingredient': ingredient,
        'stock': stock,
        'recent_transactions': recent_transactions,
        'title': f'{ingredient.name} - Stock Ma\'lumotlari'
    }

    return render(request, 'inventory/stock_detail.html', context)


# @admin_or_manager_required
# def stock_update(request, ingredient_id):
#     """Stock yangilash"""
#     ingredient = get_object_or_404(Ingredient, id=ingredient_id, is_active=True)
#     stock, created = Stock.objects.get_or_create(ingredient=ingredient)
#
#     if request.method == 'POST':
#         form = StockUpdateForm(request.POST, instance=stock)
#         if form.is_valid():
#             old_quantity = stock.current_quantity
#             stock = form.save()
#
#             quantity_change = stock.current_quantity - old_quantity
#             transaction_type = 'STOCK_IN' if quantity_change > 0 else 'STOCK_OUT'
#
#             StockTransaction.objects.create(
#                 ingredient=ingredient,
#                 transaction_type=transaction_type,
#                 quantity=abs(quantity_change),
#                 notes=f"Stock yangilandi: {old_quantity} → {stock.current_quantity}",
#                 created_by=request.user
#             )
#
#             # Activity log
#             log_inventory_activity(
#                 user=request.user,
#                 action='STOCK_UPDATED',
#                 ingredient=ingredient,
#                 details={
#                     'old_quantity': old_quantity,
#                     'new_quantity': stock.current_quantity,
#                     'change': quantity_change
#                 },
#                 request=request
#             )
#
#             messages.success(request, f'{ingredient.name} stock muvaffaqiyatli yangilandi')
#             return redirect('inventory:stock_detail', ingredient_id=ingredient.id)
#     else:
#         form = StockUpdateForm(instance=stock)
#
#     context = {
#         'form': form,
#         'ingredient': ingredient,
#         'stock': stock,
#         'title': f'{ingredient.name} - Stock Yangilash'
#     }
#
#     return render(request, 'inventory/stock_update.html', context)