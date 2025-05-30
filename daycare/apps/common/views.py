from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AppSettings, ActivityLog, SystemHealth
from .forms import AppSettingsForm, ActivityLogFilterForm, SystemHealthForm
from .serializers import AppSettingsSerializer, ActivityLogSerializer, SystemHealthSerializer
from .utils import log_activity, check_system_health, get_setting
import json


def is_admin(user):
    """Check if user is admin"""
    if not user.is_authenticated:
        return False
    # Superuser always has admin rights
    if user.is_superuser:
        return True
    # Check role if exists
    try:
        return hasattr(user, 'role') and user.role and user.role.name == 'Admin'
    except AttributeError:
        # If no role system, fall back to superuser
        return user.is_superuser


def is_manager_or_admin(user):
    """Check if user is manager or admin"""
    if not user.is_authenticated:
        return False
    # Superuser always has admin rights
    if user.is_superuser:
        return True
    # Check role if exists
    try:
        return hasattr(user, 'role') and user.role and user.role.name in ['Admin', 'Manager']
    except AttributeError:
        # If no role system, fall back to staff status
        return user.is_staff or user.is_superuser


# ===== Dashboard Views =====

@login_required
def dashboard_view(request):
    """Umumiy dashboard"""
    context = {
        'total_users': get_setting('TOTAL_USERS', 0),
        'active_sessions': get_setting('ACTIVE_SESSIONS', 0),
        'recent_activities': ActivityLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )[:10],
        'system_status': SystemHealth.objects.filter(
            checked_at__gte=timezone.now() - timedelta(minutes=30)
        ).order_by('-checked_at')[:5]
    }
    return render(request, 'common/dashboard.html', context)


# ===== Settings Views =====

class AppSettingsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = AppSettings
    template_name = 'common/settings/list.html'
    context_object_name = 'settings'
    paginate_by = 20

    def test_func(self):
        return is_admin(self.request.user)

    def get_queryset(self):
        queryset = AppSettings.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(key__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset.order_by('key')


class AppSettingsCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AppSettings
    form_class = AppSettingsForm
    template_name = 'common/settings/form.html'
    success_url = reverse_lazy('common:settings_list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            self.request.user,
            'SETTING_CREATED',
            'AppSettings',
            self.object.id,
            {'key': self.object.key}
        )
        messages.success(self.request, 'Sozlama muvaffaqiyatli qo\'shildi!')
        return response


class AppSettingsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AppSettings
    form_class = AppSettingsForm
    template_name = 'common/settings/form.html'
    success_url = reverse_lazy('common:settings_list')

    def test_func(self):
        return is_admin(self.request.user)

    def form_valid(self, form):
        old_value = self.get_object().value
        response = super().form_valid(form)
        log_activity(
            self.request.user,
            'SETTING_UPDATED',
            'AppSettings',
            self.object.id,
            {'key': self.object.key, 'old_value': old_value, 'new_value': self.object.value}
        )
        messages.success(self.request, 'Sozlama muvaffaqiyatli yangilandi!')
        return response


@login_required
@user_passes_test(is_admin)
def settings_delete(request, pk):
    setting = get_object_or_404(AppSettings, pk=pk)
    if not setting.is_editable:
        messages.error(request, 'Bu sozlamani o\'chirib bo\'lmaydi!')
        return redirect('common:settings_list')

    if request.method == 'POST':
        log_activity(
            request.user,
            'SETTING_DELETED',
            'AppSettings',
            setting.id,
            {'key': setting.key}
        )
        setting.delete()
        messages.success(request, 'Sozlama muvaffaqiyatli o\'chirildi!')
    return redirect('common:settings_list')


# ===== Activity Log Views =====

@login_required
@user_passes_test(is_manager_or_admin)
def activity_log_list(request):
    """Faoliyat loglarini ko'rish"""
    form = ActivityLogFilterForm(request.GET)
    logs = ActivityLog.objects.all()

    if form.is_valid():
        if form.cleaned_data['user']:
            logs = logs.filter(user=form.cleaned_data['user'])
        if form.cleaned_data['action']:
            logs = logs.filter(action=form.cleaned_data['action'])
        if form.cleaned_data['object_type']:
            logs = logs.filter(object_type__icontains=form.cleaned_data['object_type'])
        if form.cleaned_data['date_from']:
            logs = logs.filter(timestamp__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data['date_to']:
            logs = logs.filter(timestamp__date__lte=form.cleaned_data['date_to'])

    logs = logs.order_by('-timestamp')
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'logs': page_obj
    }
    return render(request, 'common/activity_log/list.html', context)


@login_required
@user_passes_test(is_manager_or_admin)
def activity_log_detail(request, pk):
    """Faoliyat log tafsilotlari"""
    log = get_object_or_404(ActivityLog, pk=pk)
    return render(request, 'common/activity_log/detail.html', {'log': log})


# ===== System Health Views =====

@login_required
@user_passes_test(is_admin)
def system_health_dashboard(request):
    """Tizim salomatligi dashboard"""
    # Last 24 hours health checks
    recent_checks = SystemHealth.objects.filter(
        checked_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-checked_at')

    # Current status for each component
    current_status = {}
    for component, _ in SystemHealth.COMPONENT_CHOICES:
        latest = SystemHealth.objects.filter(component=component).first()
        current_status[component] = latest

    # Stats
    stats = {
        'healthy': recent_checks.filter(status='HEALTHY').count(),
        'warning': recent_checks.filter(status='WARNING').count(),
        'error': recent_checks.filter(status='ERROR').count(),
        'down': recent_checks.filter(status='DOWN').count(),
    }

    context = {
        'current_status': current_status,
        'recent_checks': recent_checks[:20],
        'stats': stats
    }
    return render(request, 'common/system_health/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def system_health_check(request):
    """Tizim salomatligini tekshirish"""
    if request.method == 'POST':
        check_system_health()
        messages.success(request, 'Tizim salomatligi tekshirildi!')
    return redirect('common:system_health_dashboard')


# ===== API Views =====

class AppSettingsViewSet(viewsets.ModelViewSet):
    queryset = AppSettings.objects.all()
    serializer_class = AppSettingsSerializer

    @action(detail=False, methods=['get'])
    def by_key(self, request):
        key = request.query_params.get('key')
        if not key:
            return Response({'error': 'Key parameter required'}, status=400)

        try:
            setting = AppSettings.objects.get(key=key)
            return Response({
                'key': setting.key,
                'value': setting.get_typed_value(),
                'data_type': setting.data_type
            })
        except AppSettings.DoesNotExist:
            return Response({'error': 'Setting not found'}, status=404)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer

    def get_queryset(self):
        queryset = ActivityLog.objects.all()
        user_id = self.request.query_params.get('user_id')
        action = self.request.query_params.get('action')

        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)

        return queryset.order_by('-timestamp')


class SystemHealthViewSet(viewsets.ModelViewSet):
    queryset = SystemHealth.objects.all()
    serializer_class = SystemHealthSerializer

    @action(detail=False, methods=['get'])
    def current_status(self, request):
        """Get current status of all components"""
        status_data = {}
        for component, name in SystemHealth.COMPONENT_CHOICES:
            latest = SystemHealth.objects.filter(component=component).first()
            status_data[component] = {
                'name': name,
                'status': latest.status if latest else 'UNKNOWN',
                'checked_at': latest.checked_at if latest else None,
                'response_time': latest.response_time if latest else None
            }
        return Response(status_data)
