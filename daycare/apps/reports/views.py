# reports/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import date, datetime, timedelta
import json

from .models import DailyReport, MonthlyReport, IngredientUsageReport
from .forms import (
    ReportFilterForm, DailyReportGenerateForm, MonthlyReportGenerateForm,
    IngredientUsageFilterForm, ReportExportForm
)
from .services import ReportService, ReportAnalyticsService


def is_manager_or_admin(user):
    """Manager yoki admin tekshirish"""
    return user.is_authenticated and (user.is_manager or user.is_admin)


@login_required
@user_passes_test(is_manager_or_admin)
def reports_dashboard(request):
    """Hisobotlar dashboard"""

    # Dashboard ma'lumotlari
    dashboard_data = ReportAnalyticsService.get_dashboard_data(days=30)

    # So'nggi hisobotlar
    recent_daily = DailyReport.objects.order_by('-report_date')[:5]
    recent_monthly = MonthlyReport.objects.order_by('-report_month')[:3]

    context = {
        'dashboard_data': dashboard_data,
        'recent_daily': recent_daily,
        'recent_monthly': recent_monthly,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
@user_passes_test(is_manager_or_admin)
def daily_reports_list(request):
    """Kunlik hisobotlar ro'yxati"""

    reports = DailyReport.objects.all()

    # Filtrlash
    form = ReportFilterForm(request.GET)
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

        if start_date:
            reports = reports.filter(report_date__gte=start_date)
        if end_date:
            reports = reports.filter(report_date__lte=end_date)

    reports = reports.order_by('-report_date')

    # Sahifalash
    paginator = Paginator(reports, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'form': form,
        'total_reports': reports.count(),
    }
    return render(request, 'reports/daily_reports_list.html', context)


@login_required
@user_passes_test(is_manager_or_admin)
def daily_report_detail(request, pk):
    """Kunlik hisobot tafsilotlari"""

    report = get_object_or_404(DailyReport, pk=pk)

    context = {
        'report': report,
    }
    return render(request, 'reports/daily_report_detail.html', context)


@login_required
@user_passes_test(is_manager_or_admin)
def daily_report_generate(request):
    """Kunlik hisobot yaratish"""

    if request.method == 'POST':
        form = DailyReportGenerateForm(request.POST)
        if form.is_valid():
            report_date = form.cleaned_data['report_date']

            # Hisobotni yaratish
            try:
                report = ReportService.generate_daily_report(report_date, request.user)
                messages.success(request, f'{report_date} sanasi uchun hisobot yaratildi.')
                return redirect('reports:daily_report_detail', pk=report.pk)
            except Exception as e:
                messages.error(request, f'Hisobot yaratishda xatolik: {str(e)}')
    else:
        form = DailyReportGenerateForm(initial={'report_date': date.today() - timedelta(days=1)})

    context = {
        'form': form,
    }
    return render(request, 'reports/daily_report_generate.html', context)


@login_required
@user_passes_test(is_manager_or_admin)
def monthly_reports_list(request):
    """Oylik hisobotlar ro'yxati"""

    reports = MonthlyReport.objects.order_by('-report_month')

    # Sahifalash
    paginator = Paginator(reports, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_reports': reports.count(),
    }
    return render(request, 'reports/monthly_reports_list.html', context)


@login_required
@user_passes_test(is_manager_or_admin)
def monthly_report_detail(request, pk):
    """Oylik hisobot tafsilotlari"""

    report = get_object_or_404(MonthlyReport, pk=pk)

    context = {
        'report': report,
    }
    return render(request, 'reports/monthly_report_detail.html', context)


@login_required
@user_passes_test(is_manager_or_admin)
def monthly_report_generate(request):
    """Oylik hisobot yaratish"""

    if request.method == 'POST':
        form = MonthlyReportGenerateForm(request.POST)
        if form.is_valid():
            year = form.cleaned_data['year']
            month = int(form.cleaned_data['month'])

            # Hisobotni yaratish
            try:
                report = ReportService.generate_monthly_report(year, month, request.user)
                messages.success(request, f'{year}-{month:02d} oy uchun hisobot yaratildi.')
                return redirect('reports:monthly_report_detail', pk=report.pk)
            except Exception as e:
                messages.error(request, f'Hisobot yaratishda xatolik: {str(e)}')
    else:
        today = date.today()
        # O'tgan oy uchun default
        if today.month == 1:
            default_year = today.year - 1
            default_month = 12
        else:
            default_year = today.year
            default_month = today.month - 1

        form = MonthlyReportGenerateForm(initial={
            'year': default_year,
            'month': default_month
        })

    context = {
        'form': form,
    }
    return render(request, 'reports/monthly_report_generate.html', context)


@login_required
@user_passes_test(is_manager_or_admin)
def ingredient_usage_reports(request):
    """Ingredient ishlatish hisobotlari"""

    reports = IngredientUsageReport.objects.select_related('ingredient')

    # Filtrlash
    form = IngredientUsageFilterForm(request.GET)
    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        ingredient = form.cleaned_data.get('ingredient')
        category = form.cleaned_data.get('category')

        if start_date:
            reports = reports.filter(report_date__gte=start_date)
        if end_date:
            reports = reports.filter(report_date__lte=end_date)
        if ingredient:
            reports = reports.filter(ingredient=ingredient)
        if category:
            reports = reports.filter(ingredient__category=category)

    reports = reports.order_by('-report_date', 'ingredient__name')

    # Sahifalash
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Form uchun queryset'lar
    # Bu yerda inventory app'dan import qilish kerak
    # form.fields['ingredient'].queryset = Ingredient.objects.all()
    # form.fields['category'].queryset = IngredientCategory.objects.all()

    context = {
        'page_obj': page_obj,
        'form': form,
        'total_reports': reports.count(),
    }
    return render(request, 'reports/ingredient_usage_reports.html', context)


# =============================================
# AJAX VIEWS
# =============================================

@login_required
@user_passes_test(is_manager_or_admin)
def get_dashboard_analytics(request):
    """Dashboard analytics ma'lumotlari"""

    days = int(request.GET.get('days', 30))
    data = ReportAnalyticsService.get_dashboard_data(days=days)

    return JsonResponse(data)


@require_POST
@login_required
@user_passes_test(is_manager_or_admin)
def regenerate_daily_report(request, pk):
    """Kunlik hisobotni qayta yaratish"""

    report = get_object_or_404(DailyReport, pk=pk)

    try:
        updated_report = ReportService.generate_daily_report(report.report_date, request.user)
        return JsonResponse({
            'success': True,
            'message': 'Hisobot qayta yaratildi.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_POST
@login_required
@user_passes_test(is_manager_or_admin)
def regenerate_monthly_report(request, pk):
    """Oylik hisobotni qayta yaratish"""

    report = get_object_or_404(MonthlyReport, pk=pk)

    try:
        year = report.report_month.year
        month = report.report_month.month
        updated_report = ReportService.generate_monthly_report(year, month, request.user)
        return JsonResponse({
            'success': True,
            'message': 'Hisobot qayta yaratildi.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@user_passes_test(is_manager_or_admin)
def export_report(request):
    """Hisobot eksport qilish"""

    if request.method == 'POST':
        form = ReportExportForm(request.POST)
        if form.is_valid():
            export_format = form.cleaned_data['export_format']
            include_charts = form.cleaned_data['include_charts']
            include_details = form.cleaned_data['include_details']

            # Eksport logikasi bu yerda bo'ladi
            # PDF, Excel, CSV generatsiya

            if export_format == 'pdf':
                # PDF yaratish
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="hisobot.pdf"'
                # PDF generatsiya logikasi
                return response

            elif export_format == 'excel':
                # Excel yaratish
                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="hisobot.xlsx"'
                # Excel generatsiya logikasi
                return response

            elif export_format == 'csv':
                # CSV yaratish
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="hisobot.csv"'
                # CSV generatsiya logikasi
                return response
    else:
        form = ReportExportForm()

    context = {
        'form': form,
    }
    return render(request, 'reports/export_report.html', context)