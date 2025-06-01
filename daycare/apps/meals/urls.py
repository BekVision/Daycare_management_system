# meals/urls.py
from django.urls import path
from . import views

app_name = 'meals'

urlpatterns = [
    # Main meals URLs
    path('', views.meal_list, name='meal_list'),
    path('create/', views.meal_create, name='meal_create'),
    path('<int:pk>/', views.meal_detail, name='meal_detail'),
    path('<int:pk>/edit/', views.meal_edit, name='meal_edit'),
    path('<int:pk>/delete/', views.meal_delete, name='meal_delete'),

    # Categories URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Recipes URLs
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/create/', views.recipe_create, name='recipe_create'),
    path('recipes/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/<int:pk>/edit/', views.recipe_edit, name='recipe_edit'),
    path('recipes/<int:pk>/delete/', views.recipe_delete, name='recipe_delete'),

    # AJAX endpoints
    path('ajax/meal-recipes/<int:meal_id>/', views.ajax_meal_recipes, name='ajax_meal_recipes'),
    path('ajax/calculate-nutrition/<int:meal_id>/', views.ajax_calculate_nutrition, name='ajax_calculate_nutrition'),
]