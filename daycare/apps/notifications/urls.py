# notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Main notification URLs
    path('', views.notification_list, name='notification_list'),
    path('<int:pk>/', views.notification_detail, name='notification_detail'),
    path('preferences/', views.notification_preferences, name='preferences'),

    # AJAX endpoints
    path('<int:pk>/mark-read/', views.mark_as_read, name='mark_as_read'),
    path('<int:pk>/mark-unread/', views.mark_as_unread, name='mark_as_unread'),
    path('<int:pk>/delete/', views.delete_notification, name='delete_notification'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_as_read'),

    # API endpoints
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
    path('api/recent/', views.get_recent_notifications, name='get_recent_notifications'),
]