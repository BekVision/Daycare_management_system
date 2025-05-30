from django.conf import settings
from django.utils import timezone
from .models import AppSettings, ActivityLog, SystemHealth
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client's IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(user, action, object_type=None, object_id=None, changes=None, request=None):
    """Log user activity"""
    try:
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
            changes=changes or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")


def get_setting(key, default=None):
    """Get application setting value"""
    try:
        setting = AppSettings.objects.get(key=key)
        return setting.get_typed_value()
    except AppSettings.DoesNotExist:
        return default


def set_setting(key, value, description=None, data_type='STRING'):
    """Set application setting"""
    setting, created = AppSettings.objects.get_or_create(
        key=key,
        defaults={
            'value': str(value),
            'description': description,
            'data_type': data_type
        }
    )
    if not created:
        setting.value = str(value)
        setting.save()
    return setting


def check_system_health():
    """Check system health for all components"""
    from django.db import connection
    from django.core.mail import send_mail
    import time
    import redis

    components_to_check = [
        'DATABASE',
        'REDIS',
        'EMAIL',
        'STORAGE'
    ]

    for component in components_to_check:
        try:
            start_time = time.time()
            status = 'HEALTHY'
            error_message = None
            details = {}

            if component == 'DATABASE':
                # Check database
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()

            elif component == 'REDIS':
                # Check Redis
                try:
                    r = redis.Redis(host='localhost', port=6379, db=0)
                    r.ping()
                except:
                    status = 'DOWN'
                    error_message = 'Redis is not accessible'

            elif component == 'EMAIL':
                # Check email (just validate settings)
                if not getattr(settings, 'EMAIL_HOST', None):
                    status = 'WARNING'
                    error_message = 'Email not configured'

            elif component == 'STORAGE':
                # Check storage
                import os
                if not os.path.exists(settings.MEDIA_ROOT):
                    status = 'WARNING'
                    error_message = 'Media directory not found'

            response_time = time.time() - start_time

        except Exception as e:
            status = 'ERROR'
            error_message = str(e)
            response_time = None

        SystemHealth.objects.create(
            component=component,
            status=status,
            response_time=response_time,
            error_message=error_message,
            details=details
        )


def create_default_settings():
    """Create default application settings"""
    defaults = [
        ('SITE_NAME', 'Daycare Management System', 'Website name', 'STRING'),
        ('ITEMS_PER_PAGE', '20', 'Items per page in lists', 'INTEGER'),
        ('LOW_STOCK_THRESHOLD', '100', 'Low stock warning threshold (grams)', 'INTEGER'),
        ('EMAIL_NOTIFICATIONS', 'true', 'Enable email notifications', 'BOOLEAN'),
        ('MAX_UPLOAD_SIZE', '5242880', 'Maximum file upload size (bytes)', 'INTEGER'),
        ('BACKUP_ENABLED', 'true', 'Enable automatic backups', 'BOOLEAN'),
        ('SESSION_TIMEOUT', '3600', 'Session timeout in seconds', 'INTEGER'),
        ('MAINTENANCE_MODE', 'false', 'Enable maintenance mode', 'BOOLEAN'),
    ]

    for key, value, description, data_type in defaults:
        AppSettings.objects.get_or_create(
            key=key,
            defaults={
                'value': value,
                'description': description,
                'data_type': data_type
            }
        )
