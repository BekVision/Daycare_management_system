# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', views.reports_dashboard, name='dashboard'),

    # Daily Reports
    path('daily/', views.daily_reports_list, name='daily_reports_list'),
    path('daily/<int:pk>/', views.daily_report_detail, name='daily_report_detail'),
    path('daily/generate/', views.daily_report_generate, name='daily_report_generate'),

    # Monthly Reports
    path('monthly/', views.monthly_reports_list, name='monthly_reports_list'),
    path('monthly/<int:pk>/', views.monthly_report_detail, name='monthly_report_detail'),
    path('monthly/generate/', views.monthly_report_generate, name='monthly_report_generate'),

    # Ingredient Usage Reports
    path('ingredient-usage/', views.ingredient_usage_reports, name='ingredient_usage_reports'),

    # Export
    path('export/', views.export_report, name='export_report'),

    # AJAX endpoints
    path('api/dashboard-analytics/', views.get_dashboard_analytics, name='get_dashboard_analytics'),
    path('api/daily/<int:pk>/regenerate/', views.regenerate_daily_report, name='regenerate_daily_report'),
    path('api/monthly/<int:pk>/regenerate/', views.regenerate_monthly_report, name='regenerate_monthly_report'),
]