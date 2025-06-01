from django.urls import path
from . import views

app_name = 'meal_service'

urlpatterns = [
    # Asosiy sahifalar
    path('', views.meal_service_list, name='service_list'),
    path('create/', views.meal_service_create, name='service_create'),
    path('<int:pk>/', views.meal_service_detail, name='service_detail'),
    path('<int:pk>/update/', views.meal_service_update, name='service_update'),

    # Ovqat berish
    path('<int:pk>/serve/', views.serve_meal, name='serve_meal'),

    # AJAX endpoints
    path('check-ingredients/<int:meal_id>/', views.check_ingredients, name='check_ingredients'),
    path('calculate-portions/<int:meal_id>/', views.calculate_possible_portions, name='calculate_portions'),

    # Baholash
    path('<int:pk>/feedback/', views.add_feedback, name='add_feedback'),

    # Hisobotlar va tahlillar
    path('daily/', views.daily_services, name='daily_services'),
    path('analytics/', views.service_analytics, name='analytics'),
]