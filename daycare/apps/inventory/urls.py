from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.inventory_dashboard, name='dashboard'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Ingredients
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredients/create/', views.ingredient_create, name='ingredient_create'),
    path('ingredients/<int:pk>/', views.ingredient_detail, name='ingredient_detail'),
    path('ingredients/<int:pk>/update/', views.ingredient_update, name='ingredient_update'),
    path('ingredients/<int:pk>/delete/', views.ingredient_delete, name='ingredient_delete'),

    # Stock
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/<int:pk>/update/', views.stock_update, name='stock_update'),
    path('stock/adjust/<int:ingredient_id>/', views.stock_adjustment, name='stock_adjustment'),

    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),

    # AJAX API endpoints
    path('api/ingredient/<int:ingredient_id>/', views.get_ingredient_info, name='get_ingredient_info'),
    path('api/stock/quick-update/', views.quick_stock_update, name='quick_stock_update'),

    # Reports
    path('reports/stock/', views.stock_report, name='stock_report'),
]