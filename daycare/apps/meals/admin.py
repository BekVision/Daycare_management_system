# meals/admin.py
from django.contrib import admin
from .models import MealCategory, Meal, Recipe, MealNutrition


@admin.register(MealCategory)
class MealCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']


class RecipeInline(admin.TabularInline):
    model = Recipe
    extra = 0
    fields = ['ingredient', 'quantity_per_portion', 'is_optional', 'display_order']
    ordering = ['display_order']


class MealNutritionInline(admin.StackedInline):
    model = MealNutrition
    extra = 0


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'difficulty_level', 'portions_per_recipe', 'is_active', 'created_by',
                    'created_at']
    list_filter = ['category', 'difficulty_level', 'is_active', 'created_at', 'created_by']
    search_fields = ['name', 'description', 'instructions']
    ordering = ['-created_at']
    inlines = [RecipeInline, MealNutritionInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['meal', 'ingredient', 'quantity_per_portion', 'is_optional', 'display_order']
    list_filter = ['is_optional', 'meal__category', 'ingredient__category']
    search_fields = ['meal__name', 'ingredient__name']
    ordering = ['meal__name', 'display_order']


@admin.register(MealNutrition)
class MealNutritionAdmin(admin.ModelAdmin):
    list_display = ['meal', 'calories_per_100g', 'protein_per_100g', 'fat_per_100g', 'carbs_per_100g']
    search_fields = ['meal__name']
    ordering = ['meal__name']