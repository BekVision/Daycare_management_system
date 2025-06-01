from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.inventory_dashboard, name='dashboard'),

    # Ingredients
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredients/create/', views.ingredient_create, name='ingredient_create'),
    path('ingredients/<int:ingredient_id>/', views.ingredient_detail, name='ingredient_detail'),
    path('ingredients/<int:ingredient_id>/edit/', views.ingredient_edit, name='ingredient_edit'),
    path('ingredients/<int:ingredient_id>/delete/', views.ingredient_delete, name='ingredient_delete'),

    # Stock Management
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/detail/', views.stock_detail, name='stock_detail'),
    path('ingredients/<int:ingredient_id>/stock/', views.stock_update, name='stock_update'),
    path('stock/adjustment/', views.stock_adjustment, name='stock_adjustment'),

    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),

    # Reports
    path('reports/low-stock/', views.low_stock_report, name='low_stock_report'),
    path('reports/expiry/', views.expiry_report, name='expiry_report'),

    # API Endpoints
    path('api/ingredients/', views.ingredient_api, name='ingredient_api'),
    path('api/ingredients/<int:ingredient_id>/stock/', views.stock_status_api, name='stock_status_api'),
]