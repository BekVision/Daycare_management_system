from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
import secrets
import string
from typing import Optional, Dict, Any
from .models import Role

User = get_user_model()


def generate_secure_password(length: int = 12) -> str:
    """
    Xavfsiz parol yaratish
    """
    # Parol uchun belgilar to'plami
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*"

    # Har bir turdan kamida bitta belgi
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]

    # Qolgan belgilarni tasodifiy tanlash
    all_chars = lowercase + uppercase + digits + special_chars
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    # Parolni aralashtirish
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def create_user_with_role(username: str, email: str, role_name: str,
                          password: Optional[str] = None, **extra_fields) -> User:
    """
    Rol bilan foydalanuvchi yaratish
    """
    try:
        role = Role.objects.get(name=role_name)
    except Role.DoesNotExist:
        raise ValueError(f"Role '{role_name}' does not exist")

    if not password:
        password = generate_secure_password()

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        **extra_fields
    )

    return user


def send_welcome_email(user: User, password: str = None) -> bool:
    """
    Yangi foydalanuvchiga xush kelibsiz emaili yuborish
    """
    try:
        context = {
            'user': user,
            'password': password,
            'login_url': f"{settings.SITE_URL}/accounts/login/",
            'site_name': getattr(settings, 'SITE_NAME', 'Bog\'cha Tizimi')
        }

        html_message = render_to_string('accounts/emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f"Xush kelibsiz - {context['site_name']}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Email yuborishda xato: {e}")
        return False


def send_password_reset_email(user: User) -> bool:
    """
    Parol tiklash emaili yuborish
    """
    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        context = {
            'user': user,
            'token': token,
            'uid': uid,
            'reset_url': f"{settings.SITE_URL}/accounts/password-reset/{uid}/{token}/",
            'site_name': getattr(settings, 'SITE_NAME', 'Bog\'cha Tizimi')
        }

        html_message = render_to_string('accounts/emails/password_reset_email.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=f"Parolni tiklash - {context['site_name']}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Parol tiklash emaili yuborishda xato: {e}")
        return False


def get_user_permissions(user: User) -> list:
    """
    Foydalanuvchi ruxsatlarini olish
    """
    if not user.is_authenticated or not user.role:
        return []

    return user.role.permissions or []


def has_permission(user: User, permission: str) -> bool:
    """
    Foydalanuvchining ma'lum ruxsatga ega ekanligini tekshirish
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    user_permissions = get_user_permissions(user)
    return permission in user_permissions


def get_users_by_role(role_name: str) -> list:
    """
    Ma'lum roldagi foydalanuvchilarni olish
    """
    try:
        role = Role.objects.get(name=role_name)
        return User.objects.filter(role=role, is_active=True)
    except Role.DoesNotExist:
        return []


def validate_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Foydalanuvchi ma'lumotlarini validatsiya qilish
    """
    errors = {}

    # Username validatsiyasi
    username = data.get('username', '').strip()
    if not username:
        errors['username'] = 'Foydalanuvchi nomi kiritilishi kerak'
    elif len(username) < 3:
        errors['username'] = 'Foydalanuvchi nomi kamida 3 ta belgidan iborat bo\'lishi kerak'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Bu foydalanuvchi nomi allaqachon mavjud'

    # Email validatsiyasi
    email = data.get('email', '').strip()
    if not email:
        errors['email'] = 'Email manzil kiritilishi kerak'
    elif User.objects.filter(email=email).exists():
        errors['email'] = 'Bu email manzil allaqachon mavjud'

    # Role validatsiyasi
    role_id = data.get('role')
    if not role_id:
        errors['role'] = 'Rol tanlanishi kerak'
    elif not Role.objects.filter(id=role_id).exists():
        errors['role'] = 'Noto\'g\'ri rol tanlandi'

    return errors


def get_user_stats() -> Dict[str, Any]:
    """
    Foydalanuvchilar statistikasi
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    role_stats = {}
    for role in Role.objects.all():
        role_stats[role.name] = User.objects.filter(role=role, is_active=True).count()

    recent_users = User.objects.filter(is_active=True).order_by('-date_joined')[:5]

    return {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'role_stats': role_stats,
        'recent_users': recent_users
    }


def log_user_activity(user: User, action: str, object_type: str = None,
                      object_id: int = None, object_repr: str = None,
                      changes: Dict = None, request=None):
    """
    Foydalanuvchi faoliyatini loglash
    """
    from core.models import ActivityLog

    ip_address = None
    user_agent = None

    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')

    ActivityLog.objects.create(
        user=user,
        action=action,
        object_type=object_type or 'Unknown',
        object_id=object_id,
        object_repr=object_repr,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent
    )


def bulk_create_users(users_data: list) -> Dict[str, Any]:
    """
    Ko'p sonli foydalanuvchilarni yaratish
    """
    created_users = []
    errors = []

    for i, user_data in enumerate(users_data):
        try:
            # Validatsiya
            validation_errors = validate_user_data(user_data)
            if validation_errors:
                errors.append({
                    'row': i + 1,
                    'data': user_data,
                    'errors': validation_errors
                })
                continue

            # Foydalanuvchi yaratish
            role = Role.objects.get(id=user_data['role'])
            password = user_data.get('password') or generate_secure_password()

            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=password,
                role=role,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', '')
            )

            created_users.append({
                'user': user,
                'password': password
            })

        except Exception as e:
            errors.append({
                'row': i + 1,
                'data': user_data,
                'errors': {'general': str(e)}
            })

    return {
        'created_users': created_users,
        'errors': errors,
        'success_count': len(created_users),
        'error_count': len(errors)
    }


def deactivate_inactive_users(days: int = 90):
    """
    Ma'lum vaqt davomida faol bo'lmagan foydalanuvchilarni o'chirish
    """
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    inactive_users = User.objects.filter(
        last_login__lt=cutoff_date,
        is_active=True
    ).exclude(is_superuser=True)

    count = inactive_users.count()
    inactive_users.update(is_active=False)

    return count


def export_users_data(format_type: str = 'csv') -> str:
    """
    Foydalanuvchilar ma'lumotlarini eksport qilish
    """
    import csv
    import io
    from django.http import HttpResponse

    users = User.objects.select_related('role', 'profile').all()

    if format_type.lower() == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'ID', 'Username', 'Email', 'First Name', 'Last Name',
            'Role', 'Is Active', 'Date Joined', 'Last Login',
            'Phone', 'Address'
        ])

        # Data
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.role.get_name_display() if user.role else '',
                'Ha' if user.is_active else 'Yo\'q',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                user.profile.phone_number if hasattr(user, 'profile') else '',
                user.profile.address if hasattr(user, 'profile') else ''
            ])

        return output.getvalue()

    return ""