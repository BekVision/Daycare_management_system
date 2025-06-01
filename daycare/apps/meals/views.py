# meals/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import Meal, MealCategory, Recipe, MealNutrition
from .forms import MealForm, MealCategoryForm, RecipeForm, MealNutritionForm
from apps.inventory.models import Ingredient


# =============================================
# MEAL VIEWS
# =============================================

@login_required
def meal_list(request):
    """Ovqatlar ro'yxati"""
    meals = Meal.objects.select_related('category', 'created_by').prefetch_related('recipe_items')

    # Filtrlash
    category_filter = request.GET.get('category')
    difficulty_filter = request.GET.get('difficulty')
    active_filter = request.GET.get('active')

    if category_filter:
        meals = meals.filter(category_id=category_filter)
    if difficulty_filter:
        meals = meals.filter(difficulty_level=difficulty_filter)
    if active_filter == '1':
        meals = meals.filter(is_active=True)
    elif active_filter == '0':
        meals = meals.filter(is_active=False)

    # Qidiruv
    search = request.GET.get('search')
    if search:
        meals = meals.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(instructions__icontains=search)
        )

    meals = meals.order_by('-created_at')

    # Sahifalash
    paginator = Paginator(meals, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter options
    categories = MealCategory.objects.filter(is_active=True).order_by('display_order', 'name')
    difficulty_choices = [(i, f'Daraja {i}') for i in range(1, 6)]

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'difficulty_choices': difficulty_choices,
        'search': search,
        'category_filter': category_filter,
        'difficulty_filter': difficulty_filter,
        'active_filter': active_filter,
        'total_meals': meals.count(),
    }
    return render(request, 'meals/meal_list.html', context)


@login_required
def meal_detail(request, pk):
    """Ovqat tafsilotlari"""
    meal = get_object_or_404(
        Meal.objects.select_related('category', 'created_by'),
        pk=pk
    )

    # Retsept ingredientlari
    recipe_items = Recipe.objects.filter(meal=meal).select_related('ingredient').order_by('display_order')

    # Ozuqa qiymati
    nutrition = getattr(meal, 'nutrition', None)

    # Umumiy xarajat hisoblash
    total_cost = 0
    for item in recipe_items:
        if item.ingredient.cost_per_unit:
            cost = float(item.quantity_per_portion) * float(item.ingredient.cost_per_unit) * meal.portions_per_recipe
            total_cost += cost

    context = {
        'meal': meal,
        'recipe_items': recipe_items,
        'nutrition': nutrition,
        'total_cost': total_cost,
        'cost_per_portion': total_cost / meal.portions_per_recipe if meal.portions_per_recipe > 0 else 0,
    }
    return render(request, 'meals/meal_detail.html', context)


@login_required
def meal_create(request):
    """Yangi ovqat yaratish"""
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda bu amalni bajarish huquqi yo\'q.')
        return redirect('meals:meal_list')

    if request.method == 'POST':
        form = MealForm(request.POST, request.FILES)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.created_by = request.user
            meal.save()
            messages.success(request, f'{meal.name} ovqati muvaffaqiyatli yaratildi.')
            return redirect('meals:meal_detail', pk=meal.pk)
    else:
        form = MealForm()

    context = {
        'form': form,
        'title': 'Yangi ovqat yaratish'
    }
    return render(request, 'meals/meal_form.html', context)


@login_required
def meal_edit(request, pk):
    """Ovqatni tahrirlash"""
    meal = get_object_or_404(Meal, pk=pk)

    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda bu amalni bajarish huquqi yo\'q.')
        return redirect('meals:meal_detail', pk=meal.pk)

    if request.method == 'POST':
        form = MealForm(request.POST, request.FILES, instance=meal)
        if form.is_valid():
            form.save()
            messages.success(request, f'{meal.name} ovqati yangilandi.')
            return redirect('meals:meal_detail', pk=meal.pk)
    else:
        form = MealForm(instance=meal)

    context = {
        'form': form,
        'meal': meal,
        'title': f'{meal.name} ovqatini tahrirlash'
    }
    return render(request, 'meals/meal_form.html', context)


@require_POST
@login_required
def meal_delete(request, pk):
    """Ovqatni o'chirish"""
    meal = get_object_or_404(Meal, pk=pk)

    if not (request.user.is_manager or request.user.is_admin):
        return JsonResponse({'success': False, 'error': 'Huquq yo\'q'})

    # Ovqat xizmatlarida ishlatilganligini tekshirish
    if hasattr(meal, 'meal_services') and meal.meal_services.exists():
        return JsonResponse({
            'success': False,
            'error': 'Bu ovqat xizmatlarida ishlatilgan. O\'chirib bo\'lmaydi.'
        })

    meal_name = meal.name
    meal.delete()

    return JsonResponse({
        'success': True,
        'message': f'{meal_name} ovqati o\'chirildi.'
    })


# =============================================
# CATEGORY VIEWS
# =============================================

@login_required
def category_list(request):
    """Kategoriyalar ro'yxati"""
    categories = MealCategory.objects.annotate(
        meal_count=Count('meals')
    ).order_by('display_order', 'name')

    # Qidiruv
    search = request.GET.get('search')
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    context = {
        'categories': categories,
        'search': search,
        'total_categories': categories.count(),
    }
    return render(request, 'meals/category_list.html', context)


@login_required
def category_create(request):
    """Yangi kategoriya yaratish"""
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda bu amalni bajarish huquqi yo\'q.')
        return redirect('meals:category_list')

    if request.method == 'POST':
        form = MealCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'{category.name} kategoriyasi yaratildi.')
            return redirect('meals:category_list')
    else:
        form = MealCategoryForm()

    context = {
        'form': form,
        'title': 'Yangi kategoriya yaratish'
    }
    return render(request, 'meals/category_form.html', context)


@login_required
def category_edit(request, pk):
    """Kategoriyani tahrirlash"""
    category = get_object_or_404(MealCategory, pk=pk)

    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda bu amalni bajarish huquqi yo\'q.')
        return redirect('meals:category_list')

    if request.method == 'POST':
        form = MealCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'{category.name} kategoriyasi yangilandi.')
            return redirect('meals:category_list')
    else:
        form = MealCategoryForm(instance=category)

    context = {
        'form': form,
        'category': category,
        'title': f'{category.name} kategoriyasini tahrirlash'
    }
    return render(request, 'meals/category_form.html', context)


@require_POST
@login_required
def category_delete(request, pk):
    """Kategoriyani o'chirish"""
    category = get_object_or_404(MealCategory, pk=pk)

    if not (request.user.is_manager or request.user.is_admin):
        return JsonResponse({'success': False, 'error': 'Huquq yo\'q'})

    if category.meals.exists():
        return JsonResponse({
            'success': False,
            'error': 'Bu kategoriyada ovqatlar mavjud. Avval ovqatlarni boshqa kategoriyaga o\'tkazing.'
        })

    category_name = category.name
    category.delete()

    return JsonResponse({
        'success': True,
        'message': f'{category_name} kategoriyasi o\'chirildi.'
    })


# =============================================
# RECIPE VIEWS
# =============================================

@login_required
def recipe_list(request):
    """Retseptlar ro'yxati"""
    recipes = Recipe.objects.select_related(
        'meal__category', 'ingredient__category'
    ).order_by('meal__name', 'display_order')

    # Filtrlash
    meal_filter = request.GET.get('meal')
    ingredient_filter = request.GET.get('ingredient')

    if meal_filter:
        recipes = recipes.filter(meal_id=meal_filter)
    if ingredient_filter:
        recipes = recipes.filter(ingredient_id=ingredient_filter)

    # Qidiruv
    search = request.GET.get('search')
    if search:
        recipes = recipes.filter(
            Q(meal__name__icontains=search) |
            Q(ingredient__name__icontains=search) |
            Q(notes__icontains=search)
        )

    # Sahifalash
    paginator = Paginator(recipes, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Filter options
    meals = Meal.objects.filter(is_active=True).order_by('name')
    ingredients = Ingredient.objects.filter(is_active=True).order_by('name')

    context = {
        'page_obj': page_obj,
        'meals': meals,
        'ingredients': ingredients,
        'search': search,
        'meal_filter': meal_filter,
        'ingredient_filter': ingredient_filter,
        'total_recipes': recipes.count(),
    }
    return render(request, 'meals/reciep_list.html', context)


@login_required
def recipe_detail(request, pk):
    """Retsept tafsilotlari"""
    recipe = get_object_or_404(
        Recipe.objects.select_related('meal', 'ingredient'),
        pk=pk
    )

    # O'sha ovqat uchun boshqa ingredientlar
    related_recipes = Recipe.objects.filter(
        meal=recipe.meal
    ).exclude(pk=pk).select_related('ingredient').order_by('display_order')

    context = {
        'recipe': recipe,
        'related_recipes': related_recipes,
    }
    return render(request, 'meals/reciep_detail.html', context)


@login_required
def recipe_create(request):
    """Yangi retsept yaratish"""
    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda bu amalni bajarish huquqi yo\'q.')
        return redirect('meals:recipe_list')

    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save()
            messages.success(request, 'Retsept muvaffaqiyatli yaratildi.')
            return redirect('meals:recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()
        # Agar meal parametri berilgan bo'lsa
        meal_id = request.GET.get('meal')
        if meal_id:
            form.fields['meal'].initial = meal_id

    context = {
        'form': form,
        'title': 'Yangi retsept yaratish'
    }
    return render(request, 'meals/reciep_form.html', context)


@login_required
def recipe_edit(request, pk):
    """Retseptni tahrirlash"""
    recipe = get_object_or_404(Recipe, pk=pk)

    if not (request.user.is_manager or request.user.is_admin):
        messages.error(request, 'Sizda bu amalni bajarish huquqi yo\'q.')
        return redirect('meals:recipe_detail', pk=recipe.pk)

    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            form.save()
            messages.success(request, 'Retsept yangilandi.')
            return redirect('meals:recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)

    context = {
        'form': form,
        'recipe': recipe,
        'title': f'{recipe.meal.name} retseptini tahrirlash'
    }
    return render(request, 'meals/reciep_form.html', context)


@require_POST
@login_required
def recipe_delete(request, pk):
    """Retseptni o'chirish"""
    recipe = get_object_or_404(Recipe, pk=pk)

    if not (request.user.is_manager or request.user.is_admin):
        return JsonResponse({'success': False, 'error': 'Huquq yo\'q'})

    meal_name = recipe.meal.name
    ingredient_name = recipe.ingredient.name
    recipe.delete()

    return JsonResponse({
        'success': True,
        'message': f'{meal_name} uchun {ingredient_name} retsepti o\'chirildi.'
    })


# =============================================
# AJAX VIEWS
# =============================================

@login_required
def ajax_meal_recipes(request, meal_id):
    """Ovqat uchun retsept ingredientlari"""
    try:
        meal = get_object_or_404(Meal, pk=meal_id)
        recipes = Recipe.objects.filter(meal=meal).select_related('ingredient').order_by('display_order')

        data = {
            'recipes': [
                {
                    'id': recipe.id,
                    'ingredient_name': recipe.ingredient.name,
                    'quantity': float(recipe.quantity_per_portion),
                    'unit': recipe.ingredient.unit,
                    'is_optional': recipe.is_optional,
                    'notes': recipe.notes or '',
                    'cost_per_unit': float(recipe.ingredient.cost_per_unit) if recipe.ingredient.cost_per_unit else 0,
                }
                for recipe in recipes
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def ajax_calculate_nutrition(request, meal_id):
    """Ovqat uchun ozuqa qiymatini hisoblash"""
    try:
        meal = get_object_or_404(Meal, pk=meal_id)
        recipes = Recipe.objects.filter(meal=meal).select_related('ingredient')

        # Bu yerda ozuqa qiymatlarini hisoblash logikasi bo'lishi kerak
        # Hozircha oddiy hisobot qaytaramiz

        total_calories = sum(
            recipe.quantity_per_portion * 2  # 2 kcal per gram as example
            for recipe in recipes
        )

        data = {
            'total_calories': total_calories,
            'calories_per_portion': total_calories / meal.portions_per_recipe if meal.portions_per_recipe > 0 else 0,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


