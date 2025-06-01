from django.core.management.base import BaseCommand
from apps.common.utils import cleanup_old_logs


class Command(BaseCommand):
    help = 'Eski loglarni tozalash'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Necha kundan eski loglarni o\'chirish (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Haqiqiy o\'chirmasdan faqat ko\'rsatish',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.WARNING(f'{days} kundan eski loglarni tozalash...')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN rejimi - hech narsa o\'chirilmaydi')
            )

            # Dry run uchun count qilish
            from django.utils import timezone
            from datetime import timedelta
            from apps.common.models import ActivityLog, SystemHealth

            cutoff_date = timezone.now() - timedelta(days=days)

            activity_count = ActivityLog.objects.filter(
                timestamp__lt=cutoff_date
            ).count()

            health_count = SystemHealth.objects.filter(
                checked_at__lt=cutoff_date
            ).count()

            self.stdout.write(f'O\'chiriladigan activity loglar: {activity_count}')
            self.stdout.write(f'O\'chiriladigan health checklar: {health_count}')

        else:
            # Haqiqiy tozalash
            result = cleanup_old_logs(days)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Muvaffaqiyatli tozalandi:\n'
                    f'  - Activity loglar: {result["deleted_logs"]}\n'
                    f'  - System health checklar: {result["deleted_health"]}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS('Tozalash jarayoni tugadi!')
        )