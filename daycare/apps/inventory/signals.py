from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import Ingredient, Stock, StockTransaction

User = get_user_model()


@receiver(post_save, sender=Ingredient)
def create_stock_for_ingredient(sender, instance, created, **kwargs):
    """Yangi ingredient yaratilganda avtomatik Stock yaratish"""
    if created:
        # Agar Stock mavjud bo'lmasa, yangi yaratish
        if not hasattr(instance, 'stock'):
            Stock.objects.create(
                ingredient=instance,
                current_quantity=0,
                reserved_quantity=0,
                last_updated_by=instance.created_by
            )


@receiver(post_save, sender=StockTransaction)
def update_stock_from_transaction(sender, instance, created, **kwargs):
    """Tranzaksiya yaratilganda Stock ni avtomatik yangilash"""
    if created:
        try:
            stock = instance.ingredient.stock
        except Stock.DoesNotExist:
            # Agar Stock mavjud bo'lmasa, yaratish
            stock = Stock.objects.create(
                ingredient=instance.ingredient,
                current_quantity=0,
                reserved_quantity=0,
                last_updated_by=instance.created_by
            )

        # Transaction turiga qarab stock ni yangilash
        if instance.transaction_type == 'IN':
            stock.current_quantity += instance.quantity
            stock.last_restock_date = instance.created_at.date()
        elif instance.transaction_type in ['OUT', 'WASTE']:
            stock.current_quantity = max(0, stock.current_quantity - instance.quantity)
        elif instance.transaction_type == 'ADJUSTMENT':
            # Adjustment da quantity yangi qiymat
            stock.current_quantity = instance.quantity

        # Expiry date ni yangilash
        if instance.expiry_date:
            stock.expiry_date = instance.expiry_date

        stock.last_updated_by = instance.created_by
        stock.save()


@receiver(post_save, sender=Stock)
def check_low_stock_alert(sender, instance, **kwargs):
    """Kam zaxira bo'lganda ogohlantirish"""
    if instance.current_quantity <= instance.ingredient.min_threshold:
        # Admin foydalanuvchilarni topish
        admin_users = User.objects.filter(
            role__permissions__can_manage_inventory=True,
            is_active=True
        )

        # Email yuborish (agar sozlangan bo'lsa)
        if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
            for admin_user in admin_users:
                if admin_user.email:
                    try:
                        send_mail(
                            subject=f'Kam zaxira ogohlantirishi - {instance.ingredient.name}',
                            message=f'''
Hurmatli {admin_user.get_full_name()},

{instance.ingredient.name} ingredient zaxirasi kam qoldi:
- Joriy miqdor: {instance.current_quantity} {instance.ingredient.unit}
- Minimal chegara: {instance.ingredient.min_threshold} {instance.ingredient.unit}

Iltimos, zaxirani to'ldiring.

Bog'cha Tizimi
                            '''.strip(),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[admin_user.email],
                            fail_silently=True,
                        )
                    except Exception:
                        pass  # Email yuborishda xatolik bo'lsa, e'tibor bermaslik


@receiver(post_save, sender=Stock)
def check_expiry_alert(sender, instance, **kwargs):
    """Muddat tugashidan oldin ogohlantirish"""
    if instance.expiry_date:
        days_until_expiry = (instance.expiry_date - date.today()).days

        # 7 kun qolganda ogohlantirish
        if 0 <= days_until_expiry <= 7:
            admin_users = User.objects.filter(
                role__permissions__can_manage_inventory=True,
                is_active=True
            )

            if hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST:
                for admin_user in admin_users:
                    if admin_user.email:
                        try:
                            if days_until_expiry == 0:
                                subject = f'DIQQAT: Muddat tugadi - {instance.ingredient.name}'
                                message_text = 'Bugun muddat tugaydi!'
                            else:
                                subject = f'Muddat tugashi ogohlantirishi - {instance.ingredient.name}'
                                message_text = f'{days_until_expiry} kun qoldi'

                            send_mail(
                                subject=subject,
                                message=f'''
Hurmatli {admin_user.get_full_name()},

{instance.ingredient.name} ingredient muddat tugashi haqida ogohlantirish:
- Joriy miqdor: {instance.current_quantity} {instance.ingredient.unit}
- Muddat tugash sanasi: {instance.expiry_date.strftime('%d.%m.%Y')}
- {message_text}

Iltimos, kerakli choralarni ko'ring.

Bog'cha Tizimi
                                '''.strip(),
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[admin_user.email],
                                fail_silently=True,
                            )
                        except Exception:
                            pass


@receiver(pre_save, sender=StockTransaction)
def validate_stock_transaction(sender, instance, **kwargs):
    """Tranzaksiya saqlashdan oldin tekshirish"""
    # OUT va WASTE tranzaksiyalari uchun zaxira yetarliligini tekshirish
    if instance.transaction_type in ['OUT', 'WASTE']:
        try:
            current_stock = instance.ingredient.stock.current_quantity
            if instance.quantity > current_stock:
                # Bu yerda ValidationError raise qilish mumkin
                # Ammo signal ichida exception qilish tavsiya etilmaydi
                # Shuning uchun log yozish yoki warning berish mumkin
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f'Insufficient stock for {instance.ingredient.name}: '
                    f'requested {instance.quantity}, available {current_stock}'
                )
        except Stock.DoesNotExist:
            pass


@receiver(post_delete, sender=Ingredient)
def cleanup_ingredient_stock(sender, instance, **kwargs):
    """Ingredient o'chirilganda Stock ni ham o'chirish"""
    try:
        if hasattr(instance, 'stock'):
            instance.stock.delete()
    except:
        pass


# Custom signal for inventory operations
from django.dispatch import Signal

# Maxsus signallar
inventory_low_stock = Signal()
inventory_expired = Signal()
inventory_restocked = Signal()


# Custom signal handlers
@receiver(inventory_restocked)
def handle_restock_notification(sender, ingredient, quantity, user, **kwargs):
    """Zaxira to'ldirilganda xabar"""
    # Bu yerda custom logika qo'shish mumkin
    # Masalan, dashboard ga real-time notification yuborish
    pass


@receiver(inventory_low_stock)
def handle_low_stock_notification(sender, ingredient, current_quantity, **kwargs):
    """Kam zaxira signali"""
    # Dashboard yoki real-time notification
    pass


@receiver(inventory_expired)
def handle_expired_notification(sender, ingredient, expiry_date, **kwargs):
    """Muddat tugagan signali"""
    # Expired items tracking uchun
    pass