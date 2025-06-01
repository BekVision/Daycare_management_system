import time
import json
from datetime import datetime
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import ActivityLog, SystemHealth, AppSettings


def log_activity(user, action, object_type='Unknown', object_id=None,
                 object_repr=None, changes=None, request=None):
    """Activity log yaratish"""
    ip_address = None
    user_agent = None

    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    ActivityLog.objects.create(
        user=user,
        action=action,
        object_type=object_type,
        object_id=object_id,
        object_repr=object_repr or str(object_id) if object_id else '',
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent
    )


def get_client_ip(request):
    """Client IP addressini olish"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def check_system_health():
    """Tizim salomatligini tekshirish"""
    results = []

    # Database check
    db_status = check_database_health()
    results.append(db_status)

    # Redis check (agar mavjud bo'lsa)
    redis_status = check_redis_health()
    if redis_status:
        results.append(redis_status)

    # Email check
    email_status = check_email_health()
    results.append(email_status)

    # Storage check
    storage_status = check_storage_health()
    results.append(storage_status)

    return results


def check_database_health():
    """Ma'lumotlar bazasi salomatligini tekshirish"""
    start_time = time.time()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        response_time = time.time() - start_time
        status = SystemHealth.StatusChoices.HEALTHY

        if response_time > 1.0:
            status = SystemHealth.StatusChoices.WARNING

        SystemHealth.objects.create(
            component='DATABASE',
            status=status,
            response_time=response_time
        )

        return {
            'component': 'DATABASE',
            'status': status,
            'response_time': response_time,
            'healthy': True
        }

    except Exception as e:
        SystemHealth.objects.create(
            component='DATABASE',
            status=SystemHealth.StatusChoices.ERROR,
            error_message=str(e)
        )

        return {
            'component': 'DATABASE',
            'status': SystemHealth.StatusChoices.ERROR,
            'error': str(e),
            'healthy': False
        }


def check_redis_health():
    """Redis salomatligini tekshirish"""
    try:
        start_time = time.time()

        # Redis connection test
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')

        if result != 'ok':
            raise Exception('Redis test failed')

        response_time = time.time() - start_time
        status = SystemHealth.StatusChoices.HEALTHY

        SystemHealth.objects.create(
            component='REDIS',
            status=status,
            response_time=response_time
        )

        return {
            'component': 'REDIS',
            'status': status,
            'response_time': response_time,
            'healthy': True
        }

    except Exception as e:
        SystemHealth.objects.create(
            component='REDIS',
            status=SystemHealth.StatusChoices.ERROR,
            error_message=str(e)
        )

        return {
            'component': 'REDIS',
            'status': SystemHealth.StatusChoices.ERROR,
            'error': str(e),
            'healthy': False
        }


def check_email_health():
    """Email tizimi salomatligini tekshirish"""
    start_time = time.time()

    try:
        # Email backend test
        from django.core.mail import get_connection

        connection = get_connection()
        connection.open()
        connection.close()

        response_time = time.time() - start_time
        status = SystemHealth.StatusChoices.HEALTHY

        SystemHealth.objects.create(
            component='EMAIL',
            status=status,
            response_time=response_time
        )

        return {
            'component': 'EMAIL',
            'status': status,
            'response_time': response_time,
            'healthy': True
        }

    except Exception as e:
        SystemHealth.objects.create(
            component='EMAIL',
            status=SystemHealth.StatusChoices.ERROR,
            error_message=str(e)
        )

        return {
            'component': 'EMAIL',
            'status': SystemHealth.StatusChoices.ERROR,
            'error': str(e),
            'healthy': False
        }


def check_storage_health():
    """Fayl saqlash tizimi salomatligini tekshirish"""
    start_time = time.time()

    try:
        import os
        from django.conf import settings

        # MEDIA_ROOT mavjudligini tekshirish
        if hasattr(settings, 'MEDIA_ROOT'):
            media_path = settings.MEDIA_ROOT
            if not os.path.exists(media_path):
                os.makedirs(media_path, exist_ok=True)

            # Test file yaratish
            test_file = os.path.join(media_path, 'health_check.txt')
            with open(test_file, 'w') as f:
                f.write('health check')

            # Test file o'qish
            with open(test_file, 'r') as f:
                content = f.read()

            # Test file o'chirish
            os.remove(test_file)

            if content != 'health check':
                raise Exception('Storage test failed')

        response_time = time.time() - start_time
        status = SystemHealth.StatusChoices.HEALTHY

        SystemHealth.objects.create(
            component='STORAGE',
            status=status,
            response_time=response_time
        )

        return {
            'component': 'STORAGE',
            'status': status,
            'response_time': response_time,
            'healthy': True
        }

    except Exception as e:
        SystemHealth.objects.create(
            component='STORAGE',
            status=SystemHealth.StatusChoices.ERROR,
            error_message=str(e)
        )

        return {
            'component': 'STORAGE',
            'status': SystemHealth.StatusChoices.ERROR,
            'error': str(e),
            'healthy': False
        }


def get_setting(key, default=None):
    """Setting qiymatini olish"""
    try:
        setting = AppSettings.objects.get(key=key)
        return setting.get_typed_value()
    except AppSettings.DoesNotExist:
        return default


def set_setting(key, value, data_type='STRING', description=None, is_editable=True):
    """Setting qiymatini o'rnatish"""
    setting, created = AppSettings.objects.get_or_create(
        key=key,
        defaults={
            'value': str(value),
            'data_type': data_type,
            'description': description,
            'is_editable': is_editable
        }
    )

    if not created:
        setting.value = str(value)
        setting.save()

    return setting


def send_system_alert(title, message, level='warning'):
    """Tizim ogohlantirishini yuborish"""
    try:
        # Email yuborish
        admin_emails = get_setting('ADMIN_EMAILS', '').split(',')
        admin_emails = [email.strip() for email in admin_emails if email.strip()]

        if admin_emails:
            context = {
                'title': title,
                'message': message,
                'level': level,
                'timestamp': datetime.now(),
                'site_name': get_setting('SITE_NAME', 'Bog\'cha Tizimi')
            }

            html_message = render_to_string('common/emails/system_alert.html', context)

            send_mail(
                subject=f'Tizim ogohlantirishi: {title}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                html_message=html_message,
                fail_silently=True
            )

    except Exception as e:
        print(f'System alert yuborishda xato: {e}')


def get_activity_stats(days=30):
    """Activity statistikasi"""
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    stats = {
        'total_activities': ActivityLog.objects.filter(
            timestamp__range=[start_date, end_date]
        ).count(),

        'top_users': ActivityLog.objects.filter(
            timestamp__range=[start_date, end_date]
        ).values('user__username').annotate(
            count=Count('user')
        ).order_by('-count')[:10],

        'top_actions': ActivityLog.objects.filter(
            timestamp__range=[start_date, end_date]
        ).values('action').annotate(
            count=Count('action')
        ).order_by('-count')[:10],

        'activities_by_day': []
    }

    # Kunlik statistika
    for i in range(days):
        date = (start_date + timedelta(days=i)).date()
        count = ActivityLog.objects.filter(
            timestamp__date=date
        ).count()

        stats['activities_by_day'].append({
            'date': date.isoformat(),
            'count': count
        })

    return stats


def cleanup_old_logs(days=90):
    """Eski loglarni tozalash"""
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    # ActivityLog tozalash
    deleted_logs = ActivityLog.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()

    # SystemHealth tozalash
    deleted_health = SystemHealth.objects.filter(
        checked_at__lt=cutoff_date
    ).delete()

    return {
        'deleted_logs': deleted_logs[0] if deleted_logs[0] else 0,
        'deleted_health': deleted_health[0] if deleted_health[0] else 0
    }