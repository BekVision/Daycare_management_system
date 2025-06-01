# notifications/services.py
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from typing import List, Optional, Dict, Any
from .models import Notification, NotificationPreference, NotificationTemplate

User = get_user_model()


class NotificationService:
    """Bildirishnoma xizmati"""

    @staticmethod
    def create_notification(
            type: str,
            title: str,
            message: str,
            recipient: User,
            sender: User = None,
            priority: str = 'MEDIUM',
            related_object_type: str = None,
            related_object_id: int = None,
            action_url: str = None,
            data: Dict[str, Any] = None,
            expires_at=None
    ) -> Notification:
        """Yangi bildirishnoma yaratish"""

        notification = Notification.objects.create(
            type=type,
            title=title,
            message=message,
            recipient=recipient,
            sender=sender,
            priority=priority,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            action_url=action_url,
            data=data,
            expires_at=expires_at,
            sent_at=timezone.now()
        )

        # Foydalanuvchi sozlamalarini tekshirish va email yuborish
        NotificationService._send_email_if_enabled(notification)

        return notification

    @staticmethod
    def create_bulk_notifications(
            type: str,
            title: str,
            message: str,
            recipients: List[User],
            sender: User = None,
            priority: str = 'MEDIUM',
            related_object_type: str = None,
            related_object_id: int = None,
            action_url: str = None,
            data: Dict[str, Any] = None
    ) -> List[Notification]:
        """Ko'p foydalanuvchi uchun bildirishnoma yaratish"""

        notifications = []
        for recipient in recipients:
            notification = NotificationService.create_notification(
                type=type,
                title=title,
                message=message,
                recipient=recipient,
                sender=sender,
                priority=priority,
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                action_url=action_url,
                data=data
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def create_low_stock_alert(ingredient, recipient: User):
        """Kam zaxira ogohlantirishi"""
        title = f"Kam zaxira: {ingredient.name}"
        message = f"{ingredient.name} ingredientining zaxirasi kam ({ingredient.current_stock} {ingredient.unit}). Yangi ta'minot kerak."

        return NotificationService.create_notification(
            type='LOW_STOCK',
            title=title,
            message=message,
            recipient=recipient,
            priority='HIGH',
            related_object_type='ingredient',
            related_object_id=ingredient.id,
            action_url=f'/inventory/ingredients/{ingredient.id}/',
            data={
                'ingredient_name': ingredient.name,
                'current_stock': str(ingredient.current_stock),
                'unit': ingredient.unit,
                'threshold': str(ingredient.min_threshold)
            }
        )

    @staticmethod
    def create_expiry_warning(ingredient, recipient: User):
        """Muddat ogohlantirishi"""
        title = f"Muddat tugash: {ingredient.name}"
        message = f"{ingredient.name} ingredientining muddati yaqinda tugaydi. Tekshirib ko'ring."

        return NotificationService.create_notification(
            type='EXPIRY_WARNING',
            title=title,
            message=message,
            recipient=recipient,
            priority='MEDIUM',
            related_object_type='ingredient',
            related_object_id=ingredient.id,
            action_url=f'/inventory/ingredients/{ingredient.id}/',
            data={
                'ingredient_name': ingredient.name,
                'expiry_date': ingredient.expiry_date.strftime('%d.%m.%Y') if ingredient.expiry_date else None
            }
        )

    @staticmethod
    def create_meal_ready_notification(meal, recipient: User):
        """Ovqat tayyor bildirishnomasi"""
        title = f"Ovqat tayyor: {meal.name}"
        message = f"{meal.name} ovqati tayyorlandi va xizmat qilishga tayyor."

        return NotificationService.create_notification(
            type='MEAL_READY',
            title=title,
            message=message,
            recipient=recipient,
            priority='LOW',
            related_object_type='meal',
            related_object_id=meal.id,
            action_url=f'/meals/{meal.id}/',
            data={
                'meal_name': meal.name,
                'category': meal.category.name if meal.category else None
            }
        )

    @staticmethod
    def create_system_alert(title: str, message: str, recipients: List[User], priority: str = 'MEDIUM'):
        """Tizim ogohlantirishi"""
        return NotificationService.create_bulk_notifications(
            type='SYSTEM_ALERT',
            title=title,
            message=message,
            recipients=recipients,
            priority=priority
        )

    @staticmethod
    def _send_email_if_enabled(notification: Notification):
        """Email yuborish (agar yoqilgan bo'lsa)"""
        try:
            preference = notification.recipient.notification_preferences
            if preference.email_notifications:
                NotificationService._send_email_notification(notification)
        except NotificationPreference.DoesNotExist:
            # Default sozlamalar bo'yicha email yuborish
            NotificationService._send_email_notification(notification)

    @staticmethod
    def _send_email_notification(notification: Notification):
        """Email bildirishnoma yuborish"""
        try:
            subject = f"[Daycare] {notification.title}"
            message = notification.message
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [notification.recipient.email]

            # HTML template ishlatish (ixtiyoriy)
            html_message = render_to_string('notifications/email_notification.html', {
                'notification': notification,
                'user': notification.recipient
            })

            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            # Log qilish (production da)
            print(f"Email yuborishda xatolik: {e}")

    @staticmethod
    def get_user_unread_count(user: User) -> int:
        """Foydalanuvchining o'qilmagan bildirishnomalar soni"""
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @staticmethod
    def mark_user_notifications_as_seen(user: User):
        """Foydalanuvchining barcha bildirishnomalarini ko'rilgan deb belgilash"""
        Notification.objects.filter(recipient=user, is_seen=False).update(is_seen=True)

    @staticmethod
    def clean_expired_notifications():
        """Muddati o'tgan bildirishnomalarni tozalash"""
        expired_count = Notification.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()[0]
        return expired_count