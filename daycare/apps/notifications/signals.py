# notifications/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import NotificationPreference
from .services import NotificationService

User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_preference(sender, instance, created, **kwargs):
    """Yangi foydalanuvchi uchun notification preference yaratish"""
    if created:
        NotificationPreference.objects.create(user=instance)

# Inventory app bilan bog'liq signallar (agar kerak bo'lsa)
# Bu yerda ingredient zaxirasi kam bo'lganda avtomatik notification yaratish mumkin

# Misol:
# @receiver(post_save, sender='inventory.Ingredient')
# def check_low_stock(sender, instance, **kwargs):
#     """Ingredient zaxirasi kam bo'lganda notification yaratish"""
#     if instance.current_stock <= instance.min_threshold:
#         # Manager va admin foydalanuvchilarni topish
#         managers = User.objects.filter(is_manager=True, is_active=True)
#         admins = User.objects.filter(is_admin=True, is_active=True)
#         recipients = list(managers) + list(admins)

#         for recipient in recipients:
#             # Foydalanuvchi sozlamalarini tekshirish
#             try:
#                 preference = recipient.notification_preferences
#                 if preference.low_stock_alerts:
#                     NotificationService.create_low_stock_alert(instance, recipient)
#             except NotificationPreference.DoesNotExist:
#                 # Default sozlamalar bo'yicha notification yaratish
#                 NotificationService.create_low_stock_alert(instance, recipient)