from django.urls import path
from . import views

app_name = 'common'

urlpatterns = [
    # Settings URLs
    path('settings/', views.settings_list, name='settings_list'),
    path('settings/<int:setting_id>/edit/', views.settings_edit, name='settings_edit'),

    # Activity Logs URLs
    path('logs/', views.activity_logs, name='activity_logs'),
    path('logs/<int:log_id>/', views.activity_log_detail, name='activity_log_detail'),

    # System Health URLs
    path('health/', views.system_health, name='system_health'),
    path('health/check/', views.run_health_check, name='run_health_check'),

    # API URLs
    path('api/settings/', views.SettingsAPIView.as_view(), name='settings_api'),
]