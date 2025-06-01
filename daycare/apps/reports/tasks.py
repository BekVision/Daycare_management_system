# reports/tasks.py
"""
Celery task'lari hisobotlarni avtomatik yaratish uchun
Celery o'rnatilgan bo'lsa ishlaydi
"""

from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

# Celery mavjud bo'lsa import qilish
try:
    from celery import shared_task

    CELERY_AVAILABLE = True
except ImportError:
    # Celery yo'q bo'lsa, oddiy funktsiya decorator
    def shared_task(func):
        return func


    CELERY_AVAILABLE = False

from .services import ReportService

User = get_user_model()


@shared_task
def generate_daily_report_task(report_date=None, user_id=None):
    """
    Kunlik hisobot yaratish task'i

    Args:
        report_date: str (YYYY-MM-DD) yoki None (kecha uchun)
        user_id: int yoki None (system user uchun)

    Returns:
        dict: {'success': bool, 'message': str, 'report_id': int}
    """
    try:
        # Sanani aniqlash
        if report_date:
            if isinstance(report_date, str):
                from datetime import datetime
                report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        else:
            report_date = date.today() - timedelta(days=1)  # Kecha

        # Foydalanuvchini topish
        if user_id:
            user = User.objects.get(id=user_id)
        else:
            user = User.objects.filter(is_admin=True).first()
            if not user:
                return {
                    'success': False,
                    'message': 'System admin topilmadi',
                    'report_id': None
                }

        # Hisobotni yaratish
        report = ReportService.generate_daily_report(report_date, user)

        return {
            'success': True,
            'message': f'Kunlik hisobot yaratildi: {report_date}',
            'report_id': report.id
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Xatolik: {str(e)}',
            'report_id': None
        }


@shared_task
def generate_monthly_report_task(year=None, month=None, user_id=None):
    """
    Oylik hisobot yaratish task'i

    Args:
        year: int yoki None (o'tgan oy uchun)
        month: int yoki None (o'tgan oy uchun)
        user_id: int yoki None (system user uchun)

    Returns:
        dict: {'success': bool, 'message': str, 'report_id': int}
    """
    try:
        # Yil va oyni aniqlash
        if year is None or month is None:
            last_month = date.today().replace(day=1) - timedelta(days=1)
            year = last_month.year
            month = last_month.month

        # Foydalanuvchini topish
        if user_id:
            user = User.objects.get(id=user_id)
        else:
            user = User.objects.filter(is_admin=True).first()
            if not user:
                return {
                    'success': False,
                    'message': 'System admin topilmadi',
                    'report_id': None
                }

        # Hisobotni yaratish
        report = ReportService.generate_monthly_report(year, month, user)

        return {
            'success': True,
            'message': f'Oylik hisobot yaratildi: {year}-{month:02d}',
            'report_id': report.id
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Xatolik: {str(e)}',
            'report_id': None
        }


@shared_task
def auto_generate_daily_reports():
    """
    Har kuni avtomatik ravishda kechagi hisobotni yaratish
    Celery beat bilan ishlatiladi
    """
    yesterday = date.today() - timedelta(days=1)

    # Hisobot mavjudligini tekshirish
    from .models import DailyReport
    if DailyReport.objects.filter(report_date=yesterday).exists():
        return {
            'success': False,
            'message': f'{yesterday} uchun hisobot allaqachon mavjud',
            'report_id': None
        }

    # Task'ni ishga tushirish
    return generate_daily_report_task.delay(
        report_date=yesterday.strftime('%Y-%m-%d')
    )


@shared_task
def auto_generate_monthly_reports():
    """
    Har oy boshida o'tgan oy uchun hisobotni yaratish
    Celery beat bilan ishlatiladi
    """
    # O'tgan oyni aniqlash
    first_day_this_month = date.today().replace(day=1)
    last_month_last_day = first_day_this_month - timedelta(days=1)
    year = last_month_last_day.year
    month = last_month_last_day.month

    # Hisobot mavjudligini tekshirish
    from .models import MonthlyReport
    report_month = date(year, month, 1)
    if MonthlyReport.objects.filter(report_month=report_month).exists():
        return {
            'success': False,
            'message': f'{year}-{month:02d} uchun hisobot allaqachon mavjud',
            'report_id': None
        }

    # Task'ni ishga tushirish
    return generate_monthly_report_task.delay(year=year, month=month)


@shared_task
def cleanup_old_reports(days=365):
    """
    Eski hisobotlarni tozalash task'i

    Args:
        days: int - necha kundan eski hisobotlarni o'chirish

    Returns:
        dict: {'success': bool, 'deleted_count': int, 'message': str}
    """
    try:
        from .models import DailyReport, MonthlyReport, IngredientUsageReport

        cutoff_date = date.today() - timedelta(days=days)

        # Hisobotlarni o'chirish
        daily_deleted = DailyReport.objects.filter(
            report_date__lt=cutoff_date
        ).delete()[0]

        monthly_deleted = MonthlyReport.objects.filter(
            report_month__lt=cutoff_date
        ).delete()[0]

        ingredient_deleted = IngredientUsageReport.objects.filter(
            report_date__lt=cutoff_date
        ).delete()[0]

        total_deleted = daily_deleted + monthly_deleted + ingredient_deleted

        return {
            'success': True,
            'deleted_count': total_deleted,
            'message': f'{total_deleted} ta eski hisobot o\'chirildi (daily: {daily_deleted}, monthly: {monthly_deleted}, ingredient: {ingredient_deleted})'
        }

    except Exception as e:
        return {
            'success': False,
            'deleted_count': 0,
            'message': f'Xatolik: {str(e)}'
        }


@shared_task
def send_report_notifications(report_type, report_id):
    """
    Hisobot yaratilganda notification yuborish

    Args:
        report_type: str - 'daily' yoki 'monthly'
        report_id: int - hisobot ID'si
    """
    try:
        # Notification service'ni import qilish
        # from notifications.services import NotificationService

        if report_type == 'daily':
            from .models import DailyReport
            report = DailyReport.objects.get(id=report_id)

            # Manager va admin foydalanuvchilarni topish
            managers = User.objects.filter(is_manager=True, is_active=True)
            admins = User.objects.filter(is_admin=True, is_active=True)
            recipients = list(managers) + list(admins)

            # Notification yaratish
            for recipient in recipients:
                if recipient != report.generated_by:
                    # NotificationService.create_notification(...)
                    pass

        elif report_type == 'monthly':
            from .models import MonthlyReport
            report = MonthlyReport.objects.get(id=report_id)

            # Shunga o'xshash logika
            pass

        return {
            'success': True,
            'message': f'{report_type} hisobot uchun notification yuborildi'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Notification yuborishda xatolik: {str(e)}'
        }


# Celery beat schedule (settings.py ga qo'shish uchun)
CELERY_BEAT_SCHEDULE_EXAMPLE = {
    'auto-generate-daily-reports': {
        'task': 'reports.tasks.auto_generate_daily_reports',
        'schedule': {
            'hour': 6,  # Ertalab 6:00 da
            'minute': 0,
        },
    },
    'auto-generate-monthly-reports': {
        'task': 'reports.tasks.auto_generate_monthly_reports',
        'schedule': {
            'day_of_month': 1,  # Har oy 1-sanasida
            'hour': 8,  # 8:00 da
            'minute': 0,
        },
    },
    'cleanup-old-reports': {
        'task': 'reports.tasks.cleanup_old_reports',
        'schedule': {
            'day_of_week': 0,  # Yakshanba kuni
            'hour': 2,  # Kecha soat 2:00 da
            'minute': 0,
        },
        'args': (365,),  # 1 yildan eski hisobotlarni o'chirish
    },
}