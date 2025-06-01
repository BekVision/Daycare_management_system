# reports/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date, timedelta

from .models import DailyReport, MonthlyReport


# from notifications.services import NotificationService  # Import qilinganda


# @receiver(post_save, sender=DailyReport)
# def daily_report_created(sender, instance, created, **kwargs):
#     """Kunlik hisobot yaratilganda notification yuborish"""
#     if created:
#         # Manager va admin foydalanuvchilarni topish
#         from django.contrib.auth import get_user_model
#         User = get_user_model()
#
#         managers = User.objects.filter(is_manager=True, is_active=True)
#         admins = User.objects.filter(is_admin=True, is_active=True)
#         recipients = list(managers) + list(admins)
#
#         # Notification yaratish
#         for recipient in recipients:
#             if recipient != instance.generated_by:  # O'ziga notification yubormaslik
#                 NotificationService.create_notification(
#                     type='MONTHLY_REPORT',
#                     title=f"Kunlik hisobot yaratildi: {instance.report_date}",
#                     message=f"{instance.report_date} sanasi uchun kunlik hisobot yaratildi. Samaradorlik: {instance.efficiency_percentage or 0:.1f}%",
#                     recipient=recipient,
#                     sender=instance.generated_by,
#                     priority='LOW',
#                     related_object_type='daily_report',
#                     related_object_id=instance.id,
#                     action_url=f'/reports/daily/{instance.id}/',
#                     data={
#                         'report_date': instance.report_date.strftime('%d.%m.%Y'),
#                         'efficiency': str(instance.efficiency_percentage or 0),
#                         'waste': str(instance.waste_percentage or 0)
#                     }
#                 )


# @receiver(post_save, sender=MonthlyReport)
# def monthly_report_created(sender, instance, created, **kwargs):
#     """Oylik hisobot yaratilganda notification yuborish"""
#     if created:
#         # Manager va admin foydalanuvchilarni topish
#         from django.contrib.auth import get_user_model
#         User = get_user_model()
#
#         managers = User.objects.filter(is_manager=True, is_active=True)
#         admins = User.objects.filter(is_admin=True, is_active=True)
#         recipients = list(managers) + list(admins)
#
#         # Notification yaratish
#         for recipient in recipients:
#             if recipient != instance.generated_by:  # O'ziga notification yubormaslik
#                 NotificationService.create_notification(
#                     type='MONTHLY_REPORT',
#                     title=f"Oylik hisobot yaratildi: {instance.report_month.strftime('%B %Y')}",
#                     message=f"{instance.report_month.strftime('%B %Y')} oy uchun oylik hisobot yaratildi. Jami {instance.total_portions_served} porsiya xizmat qilindi.",
#                     recipient=recipient,
#                     sender=instance.generated_by,
#                     priority='MEDIUM',
#                     related_object_type='monthly_report',
#                     related_object_id=instance.id,
#                     action_url=f'/reports/monthly/{instance.id}/',
#                     data={
#                         'report_month': instance.report_month.strftime('%Y-%m'),
#                         'total_meals': str(instance.total_meals_served),
#                         'total_portions': str(instance.total_portions_served),
#                         'efficiency': str(instance.efficiency_percentage or 0)
#                     }
#                 )


# Avtomatik hisobot yaratish uchun task'lar (Celery bilan ishlaydi)
def create_daily_report_task(report_date=None):
    """Kunlik hisobot yaratish task'i"""
    if report_date is None:
        report_date = date.today() - timedelta(days=1)  # Kecha uchun

    from .services import ReportService
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        # System user yoki admin topish
        system_user = User.objects.filter(is_admin=True).first()
        if system_user:
            report = ReportService.generate_daily_report(report_date, system_user)
            return f"Kunlik hisobot yaratildi: {report.pk}"
    except Exception as e:
        return f"Xatolik: {str(e)}"


def create_monthly_report_task(year=None, month=None):
    """Oylik hisobot yaratish task'i"""
    if year is None or month is None:
        last_month = date.today().replace(day=1) - timedelta(days=1)
        year = last_month.year
        month = last_month.month

    from .services import ReportService
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        # System user yoki admin topish
        system_user = User.objects.filter(is_admin=True).first()
        if system_user:
            report = ReportService.generate_monthly_report(year, month, system_user)
            return f"Oylik hisobot yaratildi: {report.pk}"
    except Exception as e:
        return f"Xatolik: {str(e)}"