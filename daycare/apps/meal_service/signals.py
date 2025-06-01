from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import MealService, ServiceLog
from apps.common.models import ActivityLog
from apps.notifications.models import Notification
from apps.accounts.models import CustomUser


@receiver(post_save, sender=MealService)
def meal_service_created(sender, instance, created, **kwargs):
    """Yangi ovqat xizmati yaratilganda"""
    if created:
        # Admin va managerlarni xabardor qilish
        admin_manager_users = CustomUser.objects.filter(
            role__name__in=['admin', 'manager']
        ).exclude(id=instance.created_by.id)

        for user in admin_manager_users:
            Notification.objects.create(
                type='MEAL_READY',
                title='Yangi ovqat xizmati',
                message=f"{instance.meal.name} ovqati {instance.created_by.get_full_name()} "
                        f"tomonidan {instance.service_date} sanasiga rejalashtirildi",
                recipient=user,
                sender=instance.created_by,
                related_object_type='meal_service',
                related_object_id=instance.id,
                action_url=f'/meal_service/{instance.id}/'
            )


@receiver(pre_save, sender=MealService)
def meal_service_status_changed(sender, instance, **kwargs):
    """Ovqat xizmati holati o'zgarganda"""
    if instance.pk:
        try:
            old_instance = MealService.objects.get(pk=instance.pk)

            # Holat o'zgargan bo'lsa
            if old_instance.status != instance.status:
                # SERVED holatiga o'tganda
                if instance.status == 'SERVED' and old_instance.status != 'SERVED':
                    if not instance.served_at:
                        instance.served_at = timezone.now()

                    # Admin va managerlarni xabardor qilish
                    admin_manager_users = CustomUser.objects.filter(
                        role__name__in=['admin', 'manager']
                    ).exclude(id=instance.served_by.id if instance.served_by else None)

                    for user in admin_manager_users:
                        Notification.objects.create(
                            type='MEAL_READY',
                            title='Ovqat berildi',
                            message=f"{instance.meal.name} ovqati {instance.portions_served} "
                                    f"porsiya miqdorida berildi",
                            recipient=user,
                            sender=instance.served_by,
                            related_object_type='meal_service',
                            related_object_id=instance.id,
                            action_url=f'/meal_service/{instance.id}/'
                        )

                # CANCELLED holatiga o'tganda
                elif instance.status == 'CANCELLED':
                    # Admin va managerlarni xabardor qilish
                    admin_manager_users = CustomUser.objects.filter(
                        role__name__in=['admin', 'manager']
                    )

                    for user in admin_manager_users:
                        Notification.objects.create(
                            type='SYSTEM_ALERT',
                            title='Ovqat xizmati bekor qilindi',
                            message=f"{instance.meal.name} ovqati {instance.service_date} "
                                    f"sanasiga bekor qilindi",
                            recipient=user,
                            related_object_type='meal_service',
                            related_object_id=instance.id,
                            priority='HIGH',
                            action_url=f'/meal_service/{instance.id}/'
                        )

        except MealService.DoesNotExist:
            pass


@receiver(post_save, sender=ServiceLog)
def service_log_created(sender, instance, created, **kwargs):
    """Xizmat logi yaratilganda"""
    if created:
        # Agar ingredient kam bo'lib qolgan bo'lsa ogohlantirish
        ingredient = instance.ingredient

        if ingredient.is_low_stock():
            # Admin va managerlarni xabardor qilish
            admin_manager_users = CustomUser.objects.filter(
                role__name__in=['admin', 'manager']
            )

            for user in admin_manager_users:
                # Avval bunday ogohlantirish yuborilganmi tekshirish
                recent_notification = Notification.objects.filter(
                    type='LOW_STOCK',
                    recipient=user,
                    related_object_type='ingredient',
                    related_object_id=ingredient.id,
                    created_at__gte=timezone.now() - timezone.timedelta(hours=1)
                ).exists()

                if not recent_notification:
                    Notification.objects.create(
                        type='LOW_STOCK',
                        title='Ingredient kam qoldi',
                        message=f"{ingredient.name} ingredienti kam qoldi. "
                                f"Joriy miqdor: {ingredient.available_quantity()} {ingredient.unit}",
                        recipient=user,
                        related_object_type='ingredient',
                        related_object_id=ingredient.id,
                        priority='HIGH',
                        action_url=f'/inventory/stock/'
                    )

        # Agar ingredient tugab qolgan bo'lsa
        if ingredient.is_out_of_stock():
            admin_manager_users = CustomUser.objects.filter(
                role__name__in=['admin', 'manager']
            )

            for user in admin_manager_users:
                Notification.objects.create(
                    type='LOW_STOCK',
                    title='Ingredient tugadi!',
                    message=f"{ingredient.name} ingredienti tugab qoldi!",
                    recipient=user,
                    related_object_type='ingredient',
                    related_object_id=ingredient.id,
                    priority='URGENT',
                    action_url=f'/inventory/stock/'
                )


def create_efficiency_alert(meal_service):
    """Samaradorlik bo'yicha ogohlantirish yaratish"""
    if meal_service.portions_planned > 0:
        efficiency = (meal_service.portions_served / meal_service.portions_planned) * 100

        # Agar samaradorlik 70% dan past bo'lsa
        if efficiency < 70:
            admin_users = CustomUser.objects.filter(role__name='admin')

            for admin in admin_users:
                Notification.objects.create(
                    type='SYSTEM_ALERT',
                    title='Past samaradorlik',
                    message=f"{meal_service.meal.name} ovqati uchun samaradorlik past: "
                            f"{efficiency:.1f}% ({meal_service.portions_served}/"
                            f"{meal_service.portions_planned})",
                    recipient=admin,
                    related_object_type='meal_service',
                    related_object_id=meal_service.id,
                    priority='MEDIUM',
                    action_url=f'/meal_service/{meal_service.id}/'
                )


@receiver(post_save, sender=MealService)
def check_efficiency(sender, instance, **kwargs):
    """Ovqat xizmati samaradorligini tekshirish"""
    if instance.status == 'SERVED':
        create_efficiency_alert(instance)