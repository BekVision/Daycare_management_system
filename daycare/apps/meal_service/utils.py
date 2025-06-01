from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import date, timedelta

from .models import MealService, ServiceLog
from apps.meals.models import Recipe
from apps.inventory.models import Ingredient


def calculate_possible_portions_for_meal(meal):
    """
    Mavjud ingredientlar asosida nechta porsiya tayyorlash mumkinligini hisoblash
    """
    recipe_items = Recipe.objects.filter(
        meal=meal,
        is_optional=False
    ).select_related('ingredient')

    if not recipe_items.exists():
        return 0

    possible_portions = float('inf')

    for recipe_item in recipe_items:
        available_quantity = recipe_item.ingredient.available_quantity()
        if recipe_item.quantity_per_portion > 0:
            max_portions = available_quantity / recipe_item.quantity_per_portion
            possible_portions = min(possible_portions, max_portions)

    # Infinity bo'lsa 0 qaytarish
    if possible_portions == float('inf'):
        return 0

    return int(possible_portions)


def check_ingredient_availability(meal, portions=1):
    """
    Ovqat uchun ingredientlar mavjudligini tekshirish
    """
    recipe_items = Recipe.objects.filter(meal=meal).select_related('ingredient')

    ingredients_status = []
    all_available = True

    for recipe_item in recipe_items:
        required_quantity = recipe_item.quantity_per_portion * portions
        available_quantity = recipe_item.ingredient.available_quantity()
        is_sufficient = available_quantity >= required_quantity

        if not is_sufficient and not recipe_item.is_optional:
            all_available = False

        ingredients_status.append({
            'ingredient': recipe_item.ingredient,
            'required': required_quantity,
            'available': available_quantity,
            'is_sufficient': is_sufficient,
            'is_optional': recipe_item.is_optional
        })

    return {
        'all_available': all_available,
        'ingredients': ingredients_status
    }


def get_daily_service_stats(service_date=None):
    """
    Berilgan sana uchun kunlik statistika
    """
    if service_date is None:
        service_date = date.today()

    services = MealService.objects.filter(service_date=service_date)

    stats = {
        'total_services': services.count(),
        'total_planned': services.aggregate(Sum('portions_planned'))['portions_planned__sum'] or 0,
        'total_served': services.aggregate(Sum('portions_served'))['portions_served__sum'] or 0,
        'total_cost': services.aggregate(Sum('total_cost'))['total_cost__sum'] or 0,
        'services_by_status': {},
        'services_by_meal_type': {},
    }

    # Efficiency hisoblash
    if stats['total_planned'] > 0:
        stats['efficiency'] = (stats['total_served'] / stats['total_planned']) * 100
    else:
        stats['efficiency'] = 0

    # Status bo'yicha guruhlash
    for status_choice in MealService.STATUS_CHOICES:
        status = status_choice[0]
        count = services.filter(status=status).count()
        stats['services_by_status'][status] = count

    # Meal type bo'yicha guruhlash
    for meal_type_choice in MealService.MEAL_TYPES:
        meal_type = meal_type_choice[0]
        count = services.filter(meal_type=meal_type).count()
        stats['services_by_meal_type'][meal_type] = count

    return stats


def get_weekly_service_stats(start_date=None):
    """
    Haftalik statistika
    """
    if start_date is None:
        start_date = date.today() - timedelta(days=7)

    end_date = start_date + timedelta(days=7)

    services = MealService.objects.filter(
        service_date__range=[start_date, end_date]
    )

    daily_stats = []
    current_date = start_date

    while current_date <= end_date:
        day_services = services.filter(service_date=current_date)
        planned = day_services.aggregate(Sum('portions_planned'))['portions_planned__sum'] or 0
        served = day_services.aggregate(Sum('portions_served'))['portions_served__sum'] or 0
        cost = day_services.aggregate(Sum('total_cost'))['total_cost__sum'] or 0

        efficiency = (served / planned * 100) if planned > 0 else 0

        daily_stats.append({
            'date': current_date,
            'planned': planned,
            'served': served,
            'cost': cost,
            'efficiency': efficiency,
            'services_count': day_services.count()
        })

        current_date += timedelta(days=1)

    return daily_stats


def get_ingredient_usage_for_service(meal_service):
    """
    Xizmat uchun ingredient iste'molini hisoblash
    """
    logs = ServiceLog.objects.filter(meal_service=meal_service).select_related('ingredient')

    usage_stats = {
        'total_cost': logs.aggregate(Sum('total_cost'))['total_cost__sum'] or 0,
        'total_waste': logs.aggregate(Sum('waste_quantity'))['waste_quantity__sum'] or 0,
        'ingredients_used': logs.count(),
        'efficiency': 0
    }

    # Efficiency hisoblash (planned vs used)
    total_planned = logs.aggregate(Sum('quantity_planned'))['quantity_planned__sum'] or 0
    total_used = logs.aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0

    if total_planned > 0:
        usage_stats['efficiency'] = (total_used / total_planned) * 100

    return usage_stats


def get_popular_meals(days=30, limit=10):
    """
    Eng mashhur ovqatlarni aniqlash
    """
    start_date = date.today() - timedelta(days=days)

    popular_meals = MealService.objects.filter(
        service_date__gte=start_date,
        status='SERVED'
    ).values(
        'meal__name',
        'meal__id'
    ).annotate(
        total_served=Sum('portions_served')
    ).order_by('-total_served')[:limit]

    return popular_meals


def get_chef_performance(days=30):
    """
    Oshpazlar samaradorligini hisoblash
    """
    start_date = date.today() - timedelta(days=days)

    chef_stats = MealService.objects.filter(
        service_date__gte=start_date
    ).values(
        'served_by__username',
        'served_by__first_name',
        'served_by__last_name'
    ).annotate(
        total_services=Count('id'),
        total_planned=Sum('portions_planned'),
        total_served=Sum('portions_served'),
        total_cost=Sum('total_cost')
    ).order_by('-total_served')

    # Efficiency qo'shish
    for chef in chef_stats:
        if chef['total_planned'] and chef['total_planned'] > 0:
            chef['efficiency'] = round((chef['total_served'] / chef['total_planned']) * 100, 1)
        else:
            chef['efficiency'] = 0

        # O'rtacha porsiya per service
        if chef['total_services'] > 0:
            chef['average_per_service'] = round(chef['total_served'] / chef['total_services'], 1)
        else:
            chef['average_per_service'] = 0

    return chef_stats


def generate_service_recommendations(meal_service):
    """
    Xizmat uchun tavsiyalar yaratish
    """
    recommendations = []

    # Efficiency tekshirish
    if meal_service.portions_planned > 0:
        efficiency = (meal_service.portions_served / meal_service.portions_planned) * 100

        if efficiency < 70:
            recommendations.append({
                'type': 'warning',
                'title': 'Past samaradorlik',
                'message': f'Samaradorlik {efficiency:.1f}% ga teng. Ovqat tayyorlashni optimallashtirishni ko\'rib chiqing.',
                'priority': 'medium'
            })
        elif efficiency > 95:
            recommendations.append({
                'type': 'success',
                'title': 'Yuqori samaradorlik',
                'message': f'Ajoyib natija! Samaradorlik {efficiency:.1f}%.',
                'priority': 'low'
            })

    # Chiqindi tekshirish
    if meal_service.waste_quantity > 0:
        logs = ServiceLog.objects.filter(meal_service=meal_service)
        total_used = logs.aggregate(Sum('quantity_used'))['quantity_used__sum'] or 0

        if total_used > 0:
            waste_percentage = (meal_service.waste_quantity / total_used) * 100
            if waste_percentage > 10:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Yuqori chiqindi',
                    'message': f'Chiqindi miqdori {waste_percentage:.1f}%. Chiqindilarni kamaytirishga e\'tibor bering.',
                    'priority': 'high'
                })

    # Xarajat tekshirish
    if meal_service.total_cost and meal_service.portions_served > 0:
        cost_per_portion = meal_service.total_cost / meal_service.portions_served

        # Ovqat kategoriyasi bo'yicha o'rtacha xarajat bilan solishtirish
        similar_services = MealService.objects.filter(
            meal__category=meal_service.meal.category,
            status='SERVED',
            total_cost__isnull=False
        ).exclude(id=meal_service.id)

        if similar_services.exists():
            avg_cost = similar_services.aggregate(
                avg_cost=Sum('total_cost') / Sum('portions_served')
            )['avg_cost']

            if avg_cost and cost_per_portion > avg_cost * 1.2:
                recommendations.append({
                    'type': 'info',
                    'title': 'Yuqori xarajat',
                    'message': f'Porsiya narxi ({cost_per_portion:.0f} so\'m) o\'rtachadan yuqori. Xarajatlarni tekshiring.',
                    'priority': 'medium'
                })

    return recommendations


def check_low_stock_after_service(meal_service):
    """
    Xizmatdan keyin zaxira holatini tekshirish
    """
    low_stock_ingredients = []

    logs = ServiceLog.objects.filter(meal_service=meal_service).select_related('ingredient')

    for log in logs:
        ingredient = log.ingredient
        if ingredient.is_low_stock():
            low_stock_ingredients.append({
                'ingredient': ingredient,
                'current_stock': ingredient.available_quantity(),
                'min_threshold': ingredient.min_threshold
            })

    return low_stock_ingredients


def calculate_meal_cost_estimate(meal, portions=1):
    """
    Ovqat xarajatini taxminiy hisoblash
    """
    recipe_items = Recipe.objects.filter(meal=meal).select_related('ingredient')

    total_cost = 0
    cost_breakdown = []

    for recipe_item in recipe_items:
        ingredient = recipe_item.ingredient
        required_quantity = recipe_item.quantity_per_portion * portions

        if ingredient.cost_per_unit:
            item_cost = float(ingredient.cost_per_unit) * required_quantity
            total_cost += item_cost

            cost_breakdown.append({
                'ingredient': ingredient.name,
                'quantity': required_quantity,
                'unit': ingredient.unit,
                'unit_cost': ingredient.cost_per_unit,
                'total_cost': item_cost
            })

    return {
        'total_cost': total_cost,
        'cost_per_portion': total_cost / portions if portions > 0 else 0,
        'breakdown': cost_breakdown
    }