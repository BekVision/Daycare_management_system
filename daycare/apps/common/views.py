from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from apps.accounts.decorators import admin_required
from .models import AppSettings, ActivityLog, SystemHealth
from .forms import AppSettingsForm, SystemHealthForm
from .utils import log_activity, check_system_health


@admin_required
def settings_list(request):
    """Tizim sozlamalari ro'yxati"""
    settings = AppSettings.objects.all().order_by('key')

    # Qidiruv
    search = request.GET.get('search')
    if search:
        settings = settings.filter(
            Q(key__icontains=search) | Q(description__icontains=search)
        )

    # Filter by data type
    data_type = request.GET.get('data_type')
    if data_type:
        settings = settings.filter(data_type=data_type)

    context = {
        'settings': settings,
        'search': search,
        'data_type': data_type,
        'data_types': AppSettings.DATA_TYPE_CHOICES,
    }
    return render(request, 'common/settings_list.html', context)


@admin_required
def settings_edit(request, setting_id):
    """Sozlamani tahrirlash"""
    setting = get_object_or_404(AppSettings, id=setting_id)

    if not setting.is_editable:
        messages.error(request, 'Bu sozlama tahrirlash uchun ruxsat etilmagan')
        return redirect('common:settings_list')

    if request.method == 'POST':
        form = AppSettingsForm(request.POST, instance=setting)
        if form.is_valid():
            old_value = setting.value
            form.save()

            # Activity log
            log_activity(
                user=request.user,
                action='SETTING_UPDATED',
                object_type='AppSettings',
                object_id=setting.id,
                object_repr=str(setting),
                changes={'old_value': old_value, 'new_value': setting.value},
                request=request
            )

            messages.success(request, 'Sozlama muvaffaqiyatli yangilandi')
            return redirect('common:settings_list')
    else:
        form = AppSettingsForm(instance=setting)

    context = {
        'form': form,
        'setting': setting,
    }
    return render(request, 'common/settings_edit.html', context)


@admin_required
def activity_logs(request):
    """Faoliyat loglari"""
    logs = ActivityLog.objects.select_related('user').order_by('-timestamp')

    # Filters
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)

    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)

    object_type = request.GET.get('object_type')
    if object_type:
        logs = logs.filter(object_type=object_type)

    # Date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    stats = {
        'total_today': ActivityLog.objects.filter(
            timestamp__date=datetime.today().date()
        ).count(),
        'total_week': ActivityLog.objects.filter(
            timestamp__gte=datetime.now() - timedelta(days=7)
        ).count(),
        'top_actions': ActivityLog.objects.values('action').annotate(
            count=Count('action')
        ).order_by('-count')[:5],
    }

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'actions': ActivityLog.ACTION_CHOICES,
        'filters': {
            'user': user_id,
            'action': action,
            'object_type': object_type,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'common/activity_logs.html', context)


@admin_required
def system_health(request):
    """Tizim salomatligi"""
    health_checks = SystemHealth.objects.order_by('component', '-checked_at')

    # Get latest status for each component
    latest_checks = {}
    for check in health_checks:
        if check.component not in latest_checks:
            latest_checks[check.component] = check

    # Overall system status
    overall_status = 'HEALTHY'
    for check in latest_checks.values():
        if check.status == 'DOWN':
            overall_status = 'DOWN'
            break
        elif check.status == 'ERROR':
            overall_status = 'ERROR'
        elif check.status == 'WARNING' and overall_status == 'HEALTHY':
            overall_status = 'WARNING'

    context = {
        'latest_checks': latest_checks,
        'overall_status': overall_status,
        'all_checks': health_checks[:20],
    }
    return render(request, 'common/system_health.html', context)


@admin_required
def run_health_check(request):
    """Manual tizim salomatligi tekshiruvi"""
    if request.method == 'POST':
        results = check_system_health()

        # Log activity
        log_activity(
            user=request.user,
            action='SYSTEM_HEALTH_CHECK',
            object_type='SystemHealth',
            object_repr='Manual health check',
            request=request
        )

        messages.success(request, 'Tizim salomatligi tekshirildi')

        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'status': 'success', 'results': results})

    return redirect('common:system_health')


class SettingsAPIView(LoginRequiredMixin, ListView):
    """API endpoint for settings"""
    model = AppSettings

    def get(self, request, *args, **kwargs):
        key = request.GET.get('key')

        if key:
            try:
                setting = AppSettings.objects.get(key=key)
                return JsonResponse({
                    'key': setting.key,
                    'value': setting.get_typed_value(),
                    'data_type': setting.data_type
                })
            except AppSettings.DoesNotExist:
                return JsonResponse({'error': 'Setting not found'}, status=404)

        # Return all settings
        settings = AppSettings.objects.all()
        data = {}
        for setting in settings:
            data[setting.key] = setting.get_typed_value()

        return JsonResponse(data)


@login_required
def activity_log_detail(request, log_id):
    """Activity log detali"""
    log = get_object_or_404(ActivityLog, id=log_id)

    # Faqat admin yoki log egasi ko'ra oladi
    if not request.user.is_admin() and log.user != request.user:
        messages.error(request, 'Bu logni ko\'rish uchun ruxsat yo\'q')
        return redirect('common:activity_logs')

    context = {
        'log': log,
    }
    return render(request, 'common/activity_log_detail.html', context)