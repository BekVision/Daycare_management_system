from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum, F, Count
from django.core.paginator import Paginator
from datetime import date, datetime, timedelta
import json

from .models import MealService, ServiceLog, ServiceFeedback
from .forms import MealServiceForm, MealServiceUpdateForm, ServiceFeedbackForm
from apps.meals.models import Meal, Recipe
from apps.inventory.models import Ingredient, Stock, StockTransaction
from apps.accounts.models import CustomUser
from apps.common.models import ActivityLog
from apps.notifications.models import Notification


@login_required
def meal_service_list(request):
    """Ovqat xizmatlari ro'yxati"""
    services = MealService.objects.select_related(
        'meal', 'served_by', 'created_by'
    ).order_by('-created_at')

    # Filtrlash
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    meal_type_filter = request.GET.get('meal_type')

    if date_filter:
        services = services.filter(service_date=date_filter)
    if status_filter:
        services = services.filter(status=status_filter)
    if meal_type_filter:
        services = services.filter(meal_type=meal_type_filter)

    # Har bir service uchun efficiency hisoblash
    for service in services:
        if service.portions_planned > 0:
            service.efficiency_percentage = round((service.portions_served / service.portions_planned) * 100, 1)
        else:
            service.efficiency_percentage = 0

    # Sahifalash
    paginator = Paginator(services, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'meal_types': MealService.MEAL_TYPES,
        'status_choices': MealService.STATUS_CHOICES,
        'date_filter': date_filter,
        'status_filter': status_filter,
        'meal_type_filter': meal_type_filter,
    }
    return render(request, 'meal_service/service_list.html', context)


@login_required
def meal_service_create(request):
    """Yangi ovqat xizmati yaratish"""
    if not request.user.is_chef() and not request.user.is_admin():
        messages.error(request, "Sizda ovqat xizmati yaratish huquqi yo'q!")
        return redirect('meal_service:service_list')

    if request.method == 'POST':
        form = MealServiceForm(request.POST)
        if form.is_valid():
            meal_service = form.save(commit=False)
            meal_service.created_by = request.user
            meal_service.served_by = request.user
            meal_service.save()

            # Faoliyatni qayd qilish
            ActivityLog.objects.create(
                user=request.user,
                action='MEAL_SERVICE_CREATED',
                object_type='MealService',
                object_id=meal_service.id,
                object_repr=str(meal_service)
            )

            messages.success(request, "Ovqat xizmati muvaffaqiyatli yaratildi!")
            return redirect('meal_service:service_detail', pk=meal_service.id)
    else:
        # URL parametridan meal ni olish
        meal_id = request.GET.get('meal')
        initial = {'service_date': date.today()}
        if meal_id:
            initial['meal'] = meal_id
        form = MealServiceForm(initial=initial)

    context = {
        'form': form,
        'title': 'Yangi ovqat xizmati'
    }
    return render(request, 'meal_service/service_form.html', context)


@login_required
def meal_service_detail(request, pk):
    """Ovqat xizmati tafsilotlari"""
    service = get_object_or_404(
        MealService.objects.select_related('meal', 'served_by', 'created_by'),
        pk=pk
    )

    # Service loglarini olish
    logs = ServiceLog.objects.filter(meal_service=service).select_related('ingredient')

    # Feedbacklarni olish
    feedbacks = ServiceFeedback.objects.filter(meal_service=service).select_related('feedback_by')

    # Retsept ma'lumotlarini olish
    recipe_items = Recipe.objects.filter(meal=service.meal).select_related('ingredient')

    # Xarajatlarni hisoblash
    total_ingredient_cost = logs.aggregate(
        total=Sum('total_cost')
    )['total'] or 0

    # Efficiency hisoblash
    if service.portions_planned > 0:
        service.efficiency_percentage = round((service.portions_served / service.portions_planned) * 100, 1)
    else:
        service.efficiency_percentage = 0

    # Cost per portion hisoblash
    if service.total_cost and service.portions_served > 0:
        service.cost_per_portion = round(float(service.total_cost) / service.portions_served, 0)
    else:
        service.cost_per_portion = 0

    # Recipe items uchun jami miqdorlarni hisoblash
    for recipe in recipe_items:
        recipe.total_quantity_needed = recipe.quantity_per_portion * service.portions_planned

    context = {
        'service': service,
        'logs': logs,
        'feedbacks': feedbacks,
        'recipe_items': recipe_items,
        'total_ingredient_cost': total_ingredient_cost,
    }
    return render(request, 'meal_service/service_detail.html', context)


@login_required
def meal_service_update(request, pk):
    """Ovqat xizmatini yangilash"""
    service = get_object_or_404(MealService, pk=pk)

    if not request.user.is_admin() and service.created_by != request.user:
        messages.error(request, "Sizda bu xizmatni o'zgartirish huquqi yo'q!")
        return redirect('meal_service:service_detail', pk=pk)

    if request.method == 'POST':
        form = MealServiceUpdateForm(request.POST, instance=service)
        if form.is_valid():
            form.save()

            # Faoliyatni qayd qilish
            ActivityLog.objects.create(
                user=request.user,
                action='MEAL_SERVICE_UPDATED',
                object_type='MealService',
                object_id=service.id,
                object_repr=str(service)
            )

            messages.success(request, "Ovqat xizmati yangilandi!")
            return redirect('meal_service:service_detail', pk=pk)
    else:
        form = MealServiceUpdateForm(instance=service)

    context = {
        'form': form,
        'service': service,
        'title': 'Ovqat xizmatini yangilash'
    }
    return render(request, 'meal_service/service_form.html', context)


@login_required
@require_http_methods(["POST"])
def serve_meal(request, pk):
    """Ovqat berish funksiyasi"""
    service = get_object_or_404(MealService, pk=pk)

    if not request.user.is_chef() and not request.user.is_admin():
        return JsonResponse({'success': False, 'error': 'Ruxsat berilmadi!'})

    if service.status == 'SERVED':
        return JsonResponse({'success': False, 'error': 'Bu ovqat allaqachon berilgan!'})

    try:
        with transaction.atomic():
            # Retsept ma'lumotlarini olish
            recipe_items = Recipe.objects.filter(meal=service.meal).select_related('ingredient__stock')

            # Ingredientlar yetarlimi tekshirish
            insufficient_ingredients = []
            for recipe_item in recipe_items:
                required_quantity = recipe_item.quantity_per_portion * service.portions_planned
                available_quantity = recipe_item.ingredient.available_quantity()

                if available_quantity < required_quantity:
                    insufficient_ingredients.append({
                        'name': recipe_item.ingredient.name,
                        'required': required_quantity,
                        'available': available_quantity,
                        'unit': recipe_item.ingredient.unit
                    })

            if insufficient_ingredients:
                return JsonResponse({
                    'success': False,
                    'error': 'Yetarli ingredient yo\'q!',
                    'insufficient_ingredients': insufficient_ingredients
                })

            # Ingredientlarni ombordan ayirish va logga yozish
            total_cost = 0
            for recipe_item in recipe_items:
                ingredient = recipe_item.ingredient
                required_quantity = recipe_item.quantity_per_portion * service.portions_planned

                # Stock dan olish
                stock = ingredient.stock
                stock_before = stock.current_quantity
                stock.current_quantity -= required_quantity
                stock.last_updated_by = request.user
                stock.save()

                # Tranzaksiya yaratish
                unit_cost = ingredient.cost_per_unit or 0
                total_ingredient_cost = float(unit_cost) * required_quantity
                total_cost += total_ingredient_cost

                StockTransaction.objects.create(
                    ingredient=ingredient,
                    transaction_type='OUT',
                    quantity=required_quantity,
                    unit_cost=unit_cost,
                    total_cost=total_ingredient_cost,
                    reference_type='meal_service',
                    reference_id=str(service.id),
                    notes=f"Ovqat berish: {service.meal.name}",
                    created_by=request.user
                )

                # Service log yaratish
                ServiceLog.objects.create(
                    meal_service=service,
                    ingredient=ingredient,
                    quantity_planned=required_quantity,
                    quantity_used=required_quantity,
                    stock_before=stock_before,
                    stock_after=stock.current_quantity,
                    unit_cost=unit_cost,
                    total_cost=total_ingredient_cost
                )

            # Service ni yangilash
            service.status = 'SERVED'
            service.served_at = timezone.now()
            service.served_by = request.user
            service.portions_served = service.portions_planned
            service.total_cost = total_cost
            service.save()

            # Faoliyatni qayd qilish
            ActivityLog.objects.create(
                user=request.user,
                action='MEAL_SERVED',
                object_type='MealService',
                object_id=service.id,
                object_repr=str(service),
                changes={'portions_served': service.portions_served}
            )

            # Bildirishnoma yuborish
            if request.user.role.name != 'admin':
                admin_users = CustomUser.objects.filter(role__name='admin')
                for admin in admin_users:
                    Notification.objects.create(
                        type='MEAL_READY',
                        title='Ovqat berildi',
                        message=f"{service.meal.name} ovqati {request.user.get_full_name()} tomonidan berildi",
                        recipient=admin,
                        sender=request.user,
                        related_object_type='meal_service',
                        related_object_id=service.id
                    )

            return JsonResponse({
                'success': True,
                'message': 'Ovqat muvaffaqiyatli berildi!',
                'service_id': service.id,
                'portions_served': service.portions_served
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def check_ingredients(request, meal_id):
    """Ovqat uchun ingredientlar mavjudligini tekshirish"""
    meal = get_object_or_404(Meal, pk=meal_id)
    portions = int(request.GET.get('portions', 1))

    recipe_items = Recipe.objects.filter(meal=meal).select_related('ingredient')

    ingredients_status = []
    all_available = True

    for recipe_item in recipe_items:
        required_quantity = recipe_item.quantity_per_portion * portions
        available_quantity = recipe_item.ingredient.available_quantity()
        is_sufficient = available_quantity >= required_quantity

        if not is_sufficient:
            all_available = False

        ingredients_status.append({
            'name': recipe_item.ingredient.name,
            'required': required_quantity,
            'available': available_quantity,
            'unit': recipe_item.ingredient.unit,
            'is_sufficient': is_sufficient,
            'is_optional': recipe_item.is_optional
        })

    return JsonResponse({
        'all_available': all_available,
        'ingredients': ingredients_status
    })


@login_required
def calculate_possible_portions(request, meal_id):
    """Mavjud ingredientlar asosida nechta porsiya tayyorlash mumkinligini hisoblash"""
    meal = get_object_or_404(Meal, pk=meal_id)
    recipe_items = Recipe.objects.filter(
        meal=meal,
        is_optional=False
    ).select_related('ingredient')

    if not recipe_items.exists():
        return JsonResponse({'possible_portions': 0})

    possible_portions = float('inf')

    for recipe_item in recipe_items:
        available_quantity = recipe_item.ingredient.available_quantity()
        if recipe_item.quantity_per_portion > 0:
            max_portions = available_quantity / recipe_item.quantity_per_portion
            possible_portions = min(possible_portions, max_portions)

    # Infinity bo'lsa 0 qaytarish
    if possible_portions == float('inf'):
        possible_portions = 0
    else:
        possible_portions = int(possible_portions)

    return JsonResponse({'possible_portions': possible_portions})


@login_required
def add_feedback(request, pk):
    """Ovqat xizmatiga baholash qo'shish"""
    service = get_object_or_404(MealService, pk=pk)

    if request.method == 'POST':
        form = ServiceFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.meal_service = service
            feedback.feedback_by = request.user
            feedback.save()

            messages.success(request, "Bahoyingiz qo'shildi!")
            return redirect('meal_service:service_detail', pk=pk)
    else:
        form = ServiceFeedbackForm()

    context = {
        'form': form,
        'service': service,
        'title': 'Baholash qo\'shish'
    }
    return render(request, 'meal_service/feedback_form.html', context)


@login_required
def daily_services(request):
    """Bugungi xizmatlar"""
    today = date.today()
    services = MealService.objects.filter(
        service_date=today
    ).select_related('meal', 'served_by').order_by('service_time')

    # Statistika
    total_planned = services.aggregate(Sum('portions_planned'))['portions_planned__sum'] or 0
    total_served = services.aggregate(Sum('portions_served'))['portions_served__sum'] or 0

    # Har bir service uchun efficiency hisoblash
    for service in services:
        if service.portions_planned > 0:
            service.efficiency_percentage = round((service.portions_served / service.portions_planned) * 100, 1)
        else:
            service.efficiency_percentage = 0

    context = {
        'services': services,
        'today': today,
        'total_planned': total_planned,
        'total_served': total_served,
        'efficiency': round((total_served / total_planned * 100), 1) if total_planned > 0 else 0
    }
    return render(request, 'meal_service/daily_services.html', context)


@login_required
def service_analytics(request):
    """Xizmat tahlillari (faqat admin va manager uchun)"""
    if not request.user.is_admin() and not request.user.is_manager():
        messages.error(request, "Sizda bu sahifaga kirish huquqi yo'q!")
        return redirect('meal_service:service_list')

    # Oxirgi 30 kunlik ma'lumotlar
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    services = MealService.objects.filter(
        service_date__range=[start_date, end_date]
    ).select_related('meal')

    # Kunlik statistika
    daily_stats = services.values('service_date').annotate(
        total_planned=Sum('portions_planned'),
        total_served=Sum('portions_served'),
        total_cost=Sum('total_cost')
    ).order_by('service_date')

    # Har bir kun uchun efficiency hisoblash
    for day in daily_stats:
        if day['total_planned'] > 0:
            day['efficiency_percentage'] = round((day['total_served'] / day['total_planned']) * 100, 1)
        else:
            day['efficiency_percentage'] = 0

    # Umumiy statistika
    total_stats = services.aggregate(
        grand_total_planned=Sum('portions_planned'),
        grand_total_served=Sum('portions_served'),
        grand_total_cost=Sum('total_cost')
    )

    # Umumiy efficiency
    if total_stats['grand_total_planned'] and total_stats['grand_total_planned'] > 0:
        overall_efficiency = round((total_stats['grand_total_served'] / total_stats['grand_total_planned']) * 100, 1)
    else:
        overall_efficiency = 0

    # Eng ko'p berilgan ovqatlar
    popular_meals = services.values('meal__name').annotate(
        total_served=Sum('portions_served')
    ).order_by('-total_served')[:10]

    # Percentage hisoblash
    if popular_meals:
        top_meal_count = popular_meals[0]['total_served']
        for meal in popular_meals:
            if top_meal_count > 0:
                meal['percentage'] = round((meal['total_served'] / top_meal_count) * 100, 1)
            else:
                meal['percentage'] = 0

    # Oshpazlar bo'yicha statistika
    chef_stats = services.values('served_by__username', 'served_by__first_name', 'served_by__last_name').annotate(
        total_served=Sum('portions_served'),
        total_services=Count('id')
    ).order_by('-total_served')

    # O'rtacha qiymatlarni hisoblash
    for chef in chef_stats:
        if chef['total_services'] > 0:
            chef['average_per_service'] = round(chef['total_served'] / chef['total_services'], 1)
        else:
            chef['average_per_service'] = 0

    context = {
        'daily_stats': daily_stats,
        'popular_meals': popular_meals,
        'chef_stats': chef_stats,
        'start_date': start_date,
        'end_date': end_date,
        'total_stats': total_stats,
        'overall_efficiency': overall_efficiency,
        'active_days': len(daily_stats),
    }
    return render(request, 'meal_service/analytics.html', context)