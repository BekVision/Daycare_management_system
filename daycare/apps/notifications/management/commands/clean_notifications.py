# notifications/management/commands/clean_notifications.py
from django.core.management.base import BaseCommand
from apps.notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Muddati o\'tgan bildirishnomalarni tozalash'

    def handle(self, *args, **options):
        cleaned_count = NotificationService.clean_expired_notifications()
        self.stdout.write(
            self.style.SUCCESS(
                f'{cleaned_count} ta muddati o\'tgan bildirishnoma tozalandi.'
            )
        )