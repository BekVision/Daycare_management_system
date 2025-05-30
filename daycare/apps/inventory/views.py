from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, F
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import date, timedelta

from .models import IngredientCategory, Ingredient, Stock, StockTransaction
from .forms import (
    IngredientCategoryForm, IngredientForm, StockForm,
    StockTransactionForm, StockAdjustmentForm, StockSearchForm
)


# ================== DASHBOARD ==================
@login_required
def inventory_dashboard(request):
    """Inventory asosiy sahifa"""
    # Asosiy statistikalar
    total_ingredients = Ingredient.objects.filter(is_active=True).count()
    total_categories = IngredientCategory.objects.filter(is_active=True).count()

    # Kam zaxira (low stock)
    low_stock_items = Stock.objects.filter(
        current_quantity__lte=F('ingredient__min_threshold'),
        ingredient__is_active=True
    ).count()

    # Muddati tugagan mahsulotlar
    expired_items = Stock.objects.filter(
        expiry_date__lt=date.today(),
        ingredient__is_active=True
    ).count()

    # Oxirgi tranzaksiyalar
    recent_transactions = StockTransaction.objects.select_related(
        'ingredient', 'created_by'
    ).order_by('-created_at')[:10]

    # Eng ko'p ishlatiladigan ingredientlar
    most_used = StockTransaction.objects.filter(
        transaction_type='OUT',
        created_at__gte=timezone.now() - timedelta(days=30)
    ).values('ingredient__name').annotate(
        total_used=Sum('quantity')
    ).order_by('-total_used')[:5]

    context = {
        'total_ingredients': total_ingredients,
        'total_categories': total_categories,
        'low_stock_items': low_stock_items,
        'expired_items': expired_items,
        'recent_transactions': recent_transactions,
        'most_used': most_used,
    }

    return render(request, 'inventory/dashboard.html', context)


# ================== KATEGORY VIEWS ==================
@login_required
def category_list(request):
    """Kategoriyalar ro'yxati"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q.")
        return redirect('accounts:dashboard')

    search_query = request.GET.get('search', '')
    categories = IngredientCategory.objects.all()

    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    categories = categories.order_by('display_order', 'name')

    # Pagination
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }

    return render(request, 'inventory/category_list.html', context)


@login_required
def category_create(request):
    """Yangi kategoriya yaratish"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:category_list')

    if request.method == 'POST':
        form = IngredientCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Kategoriya muvaffaqiyatli yaratildi.")
            return redirect('inventory:category_list')
    else:
        form = IngredientCategoryForm()

    context = {'form': form, 'title': 'Yangi kategoriya yaratish'}
    return render(request, 'inventory/category_form.html', context)


@login_required
def category_update(request, pk):
    """Kategoriyani tahrirlash"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:category_list')

    category = get_object_or_404(IngredientCategory, pk=pk)

    if request.method == 'POST':
        form = IngredientCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Kategoriya muvaffaqiyatli yangilandi.")
            return redirect('inventory:category_list')
    else:
        form = IngredientCategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'title': f'"{category.name}" kategoriyasini tahrirlash'
    }
    return render(request, 'inventory/category_form.html', context)


@login_required
def category_delete(request, pk):
    """Kategoriyani o'chirish"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:category_list')

    category = get_object_or_404(IngredientCategory, pk=pk)

    if request.method == 'POST':
        if category.ingredients.exists():
            messages.error(request,
                           "Bu kategoriyada ingredientlar mavjud. Avval ularni o'chiring yoki boshqa kategoriyaga ko'chiring.")
        else:
            category_name = category.name
            category.delete()
            messages.success(request, f'"{category_name}" kategoriyasi o\'chirildi.')
        return redirect('inventory:category_list')

    context = {'category': category}
    return render(request, 'inventory/category_confirm_delete.html', context)


# ================== INGREDIENT VIEWS ==================
@login_required
def ingredient_list(request):
    """Ingredientlar ro'yxati"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q.")
        return redirect('accounts:dashboard')

    search_form = StockSearchForm(request.GET)
    ingredients = Ingredient.objects.select_related('category').prefetch_related('stock')

    # Qidirish va filtrlash
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        low_stock_only = search_form.cleaned_data.get('low_stock_only')
        expired_only = search_form.cleaned_data.get('expired_only')

        if search:
            ingredients = ingredients.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(barcode__icontains=search)
            )

        if category:
            ingredients = ingredients.filter(category=category)

        if low_stock_only:
            ingredients = ingredients.filter(
                stock__current_quantity__lte=F('min_threshold')
            )

        if expired_only:
            ingredients = ingredients.filter(
                stock__expiry_date__lt=date.today()
            )

    ingredients = ingredients.filter(is_active=True).order_by('name')

    # Pagination
    paginator = Paginator(ingredients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }

    return render(request, 'inventory/ingredient_list.html', context)


@login_required
def ingredient_create(request):
    """Yangi ingredient yaratish"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:ingredient_list')

    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.created_by = request.user
            ingredient.save()

            # Ingredient uchun bo'sh Stock yaratish
            Stock.objects.create(
                ingredient=ingredient,
                current_quantity=0,
                reserved_quantity=0,
                last_updated_by=request.user
            )

            messages.success(request, "Ingredient muvaffaqiyatli yaratildi.")
            return redirect('inventory:ingredient_list')
    else:
        form = IngredientForm()

    context = {'form': form, 'title': 'Yangi ingredient yaratish'}
    return render(request, 'inventory/ingredient_form.html', context)


@login_required
def ingredient_detail(request, pk):
    """Ingredient tafsilotlari"""
    ingredient = get_object_or_404(Ingredient, pk=pk)

    # Oxirgi tranzaksiyalar
    transactions = StockTransaction.objects.filter(
        ingredient=ingredient
    ).select_related('created_by').order_by('-created_at')[:20]

    context = {
        'ingredient': ingredient,
        'transactions': transactions,
    }

    return render(request, 'inventory/ingredient_detail.html', context)


@login_required
def ingredient_update(request, pk):
    """Ingredientni tahrirlash"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:ingredient_list')

    ingredient = get_object_or_404(Ingredient, pk=pk)

    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            messages.success(request, "Ingredient muvaffaqiyatli yangilandi.")
            return redirect('inventory:ingredient_detail', pk=ingredient.pk)
    else:
        form = IngredientForm(instance=ingredient)

    context = {
        'form': form,
        'ingredient': ingredient,
        'title': f'"{ingredient.name}" ni tahrirlash'
    }
    return render(request, 'inventory/ingredient_form.html', context)


@login_required
def ingredient_delete(request, pk):
    """Ingredientni o'chirish"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:ingredient_list')

    ingredient = get_object_or_404(Ingredient, pk=pk)

    if request.method == 'POST':
        ingredient_name = ingredient.name
        ingredient.is_active = False  # Soft delete
        ingredient.save()
        messages.success(request, f'"{ingredient_name}" ingredienti o\'chirildi.')
        return redirect('inventory:ingredient_list')

    context = {'ingredient': ingredient}
    return render(request, 'inventory/ingredient_confirm_delete.html', context)


# ================== STOCK VIEWS ==================

@login_required
def stock_list(request):
    """Zaxira ro'yxati"""
    search_form = StockSearchForm(request.GET)
    stocks = Stock.objects.select_related('ingredient', 'ingredient__category')

    # Qidirish va filtrlash
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        low_stock_only = search_form.cleaned_data.get('low_stock_only')
        expired_only = search_form.cleaned_data.get('expired_only')

        if search:
            stocks = stocks.filter(
                Q(ingredient__name__icontains=search) |
                Q(ingredient__description__icontains=search)
            )

        if category:
            stocks = stocks.filter(ingredient__category=category)

        if low_stock_only:
            stocks = stocks.filter(
                current_quantity__lte=F('ingredient__min_threshold')
            )

        if expired_only:
            stocks = stocks.filter(expiry_date__lt=date.today())

    stocks = stocks.filter(ingredient__is_active=True).order_by('ingredient__name')

    # Har bir stock uchun total_value hisoblash
    for stock in stocks:
        if stock.ingredient.cost_per_unit and stock.current_quantity:
            stock.total_value = stock.current_quantity * stock.ingredient.cost_per_unit
        else:
            stock.total_value = 0

    # Pagination
    paginator = Paginator(stocks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
    }

    return render(request, 'inventory/stock_list.html', context)


@login_required
def stock_update(request, pk):
    """Zaxira ma'lumotlarini yangilash"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:stock_list')

    stock = get_object_or_404(Stock, pk=pk)

    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            updated_stock = form.save(commit=False)
            updated_stock.last_updated_by = request.user
            updated_stock.save()
            messages.success(request, "Zaxira ma'lumotlari yangilandi.")
            return redirect('inventory:stock_list')
    else:
        form = StockForm(instance=stock)

    context = {
        'form': form,
        'stock': stock,
        'title': f'"{stock.ingredient.name}" zaxirasini yangilash'
    }
    return render(request, 'inventory/stock_form.html', context)


# ================== TRANSACTION VIEWS ==================
@login_required
def transaction_list(request):
    """Tranzaksiyalar ro'yxati"""
    search_query = request.GET.get('search', '')
    transaction_type = request.GET.get('type', '')

    transactions = StockTransaction.objects.select_related(
        'ingredient', 'created_by'
    ).order_by('-created_at')

    if search_query:
        transactions = transactions.filter(
            Q(ingredient__name__icontains=search_query) |
            Q(supplier__icontains=search_query) |
            Q(invoice_number__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # Pagination
    paginator = Paginator(transactions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'transaction_type': transaction_type,
        'transaction_types': StockTransaction.TRANSACTION_TYPES,
    }

    return render(request, 'inventory/transaction_list.html', context)


@login_required
def transaction_create(request):
    """Yangi tranzaksiya yaratish"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:transaction_list')

    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()

            # Stock ni yangilash
            update_stock_from_transaction(transaction)

            messages.success(request, "Tranzaksiya muvaffaqiyatli yaratildi.")
            return redirect('inventory:transaction_list')
    else:
        form = StockTransactionForm()

    context = {'form': form, 'title': 'Yangi tranzaksiya yaratish'}
    return render(request, 'inventory/transaction_form.html', context)


@login_required
def stock_adjustment(request, ingredient_id):
    """Zaxira miqdorini sozlash"""
    if not request.user.role.permissions.can_manage_inventory:
        messages.error(request, "Sizda bu amalni bajarish huquqi yo'q.")
        return redirect('inventory:stock_list')

    ingredient = get_object_or_404(Ingredient, pk=ingredient_id)
    stock = get_object_or_404(Stock, ingredient=ingredient)

    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            new_quantity = form.cleaned_data['quantity']
            current_quantity = stock.current_quantity
            adjustment_quantity = new_quantity - current_quantity

            # Tranzaksiya yaratish
            transaction = form.save(commit=False)
            transaction.ingredient = ingredient
            transaction.quantity = abs(adjustment_quantity)
            transaction.transaction_type = 'ADJUSTMENT'
            transaction.created_by = request.user
            transaction.notes = f"Miqdor {current_quantity} dan {new_quantity} ga o'zgartirildi. Sabab: {form.cleaned_data.get('adjustment_reason', '')}"
            transaction.save()

            # Stock ni yangilash
            stock.current_quantity = new_quantity
            stock.last_updated_by = request.user
            stock.save()

            messages.success(request, f"Zaxira miqdori muvaffaqiyatli o'zgartirildi.")
            return redirect('inventory:stock_list')
    else:
        form = StockAdjustmentForm(initial={'quantity': stock.current_quantity})

    context = {
        'form': form,
        'ingredient': ingredient,
        'stock': stock,
        'title': f'"{ingredient.name}" zaxirasini sozlash'
    }
    return render(request, 'inventory/stock_adjustment.html', context)


# ================== AJAX VIEWS ==================
@login_required
@require_http_methods(["GET"])
def get_ingredient_info(request, ingredient_id):
    """AJAX: Ingredient ma'lumotlarini olish"""
    try:
        ingredient = Ingredient.objects.select_related('stock').get(pk=ingredient_id)
        data = {
            'name': ingredient.name,
            'unit': ingredient.unit,
            'current_stock': ingredient.stock.current_quantity if hasattr(ingredient, 'stock') else 0,
            'min_threshold': ingredient.min_threshold,
            'cost_per_unit': float(ingredient.cost_per_unit) if ingredient.cost_per_unit else 0,
        }
        return JsonResponse(data)
    except Ingredient.DoesNotExist:
        return JsonResponse({'error': 'Ingredient topilmadi'}, status=404)


@login_required
@require_http_methods(["POST"])
def quick_stock_update(request):
    """AJAX: Tez zaxira yangilash"""
    if not request.user.role.permissions.can_manage_inventory:
        return JsonResponse({'error': 'Ruxsat berilmagan'}, status=403)

    try:
        data = json.loads(request.body)
        stock_id = data.get('stock_id')
        new_quantity = float(data.get('quantity', 0))

        stock = Stock.objects.get(pk=stock_id)
        old_quantity = stock.current_quantity

        # Stock yangilash
        stock.current_quantity = new_quantity
        stock.last_updated_by = request.user
        stock.save()

        # Tranzaksiya yaratish
        quantity_diff = new_quantity - old_quantity
        StockTransaction.objects.create(
            ingredient=stock.ingredient,
            transaction_type='ADJUSTMENT',
            quantity=abs(quantity_diff),
            notes=f'Tez yangilash: {old_quantity} dan {new_quantity} ga',
            created_by=request.user
        )

        return JsonResponse({'success': True, 'message': 'Zaxira yangilandi'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ================== HELPER FUNCTIONS ==================
def update_stock_from_transaction(transaction):
    """Tranzaksiya asosida zaxirani yangilash"""
    try:
        stock = Stock.objects.get(ingredient=transaction.ingredient)
    except Stock.DoesNotExist:
        # Agar Stock mavjud bo'lmasa, yangi yaratish
        stock = Stock.objects.create(
            ingredient=transaction.ingredient,
            current_quantity=0,
            reserved_quantity=0,
            last_updated_by=transaction.created_by
        )

    if transaction.transaction_type == 'IN':
        stock.current_quantity += transaction.quantity
    elif transaction.transaction_type in ['OUT', 'WASTE']:
        stock.current_quantity = max(0, stock.current_quantity - transaction.quantity)
    elif transaction.transaction_type == 'ADJUSTMENT':
        # Adjustment da quantity yangi qiymat
        stock.current_quantity = transaction.quantity

    # Oxirgi yangilanish ma'lumotlarini saqlash
    stock.last_updated_by = transaction.created_by
    if transaction.expiry_date:
        stock.expiry_date = transaction.expiry_date
    if transaction.transaction_type == 'IN':
        stock.last_restock_date = transaction.created_at.date()

    stock.save()


# ================== REPORTS ==================
@login_required
def stock_report(request):
    """Zaxira hisoboti"""
    if not request.user.role.permissions.can_view_reports:
        messages.error(request, "Sizda hisobot ko'rish huquqi yo'q.")
        return redirect('accounts:dashboard')

    # Umumiy statistikalar
    total_value = Stock.objects.aggregate(
        total=Sum(F('current_quantity') * F('ingredient__cost_per_unit'))
    )['total'] or 0

    low_stock_count = Stock.objects.filter(
        current_quantity__lte=F('ingredient__min_threshold')
    ).count()

    expired_count = Stock.objects.filter(
        expiry_date__lt=date.today()
    ).count()

    # Kategoriya bo'yicha taqsimot
    category_stats = IngredientCategory.objects.annotate(
        ingredient_count=Sum('ingredients__stock__current_quantity'),
        category_value=Sum(
            F('ingredients__stock__current_quantity') *
            F('ingredients__cost_per_unit')
        )
    ).filter(is_active=True)

    context = {
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'expired_count': expired_count,
        'category_stats': category_stats,
    }

    return render(request, 'inventory/stock_report.html', context)