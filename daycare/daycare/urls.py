from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

def home_redirect(request):
    """Root URL dan dashboard ga yo'naltirish"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    else:
        return redirect('accounts:login')
urlpatterns = [
    # Root
    path('', home_redirect, name='home'),

    # Other
    path('accounts/', include('apps.accounts.urls')),
    path('common/', include('apps.common.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('meal_service/', include('apps.meal_service.urls')),
    path('meals/', include('apps.meals.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('reports/', include('apps.reports.urls')),
    # Admin
    path('admin/', admin.site.urls),

]
#
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)