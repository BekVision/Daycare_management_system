from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'common'

# API Router
router = DefaultRouter()
router.register(r'settings', views.AppSettingsViewSet)
router.register(r'activity-logs', views.ActivityLogViewSet)
router.register(r'system-health', views.SystemHealthViewSet)

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Settings
    path('appsettings/', views.AppSettingsListView.as_view(), name='settings_list'),
    path('settings/add/', views.AppSettingsCreateView.as_view(), name='settings_add'),
    path('settings/<int:pk>/edit/', views.AppSettingsUpdateView.as_view(), name='settings_edit'),
    path('settings/<int:pk>/delete/', views.settings_delete, name='settings_delete'),

    # Activity Logs
    path('activitylog/', views.activity_log_list, name='activity_log_list'),
    path('activity-logs/<int:pk>/', views.activity_log_detail, name='activity_log_detail'),

    # System Health
    path('systemhealth/', views.system_health_dashboard, name='system_health_dashboard'),
    path('system-health/check/', views.system_health_check, name='system_health_check'),

    # API
    path('api/', include(router.urls)),
]