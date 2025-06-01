# reports/management/commands/cleanup_reports.py
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from datetime import date, timedelta
from reports.models import DailyReport, MonthlyReport, IngredientUsageReport


class Command(BaseCommand):
    help = 'Eski hisobotlarni tozalash va saqlash'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Necha kundan eski hisobotlarni o\'chirish (default: 365)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Haqiqatan o\'chirmasdan, faqat hisobni ko\'rsatish',
        )
        parser.add_argument(
            '--archive',
            action='store_true',
            help='O\'chirish o\'rniga arxivlash (kelajakda ishlatiladi)',
        )
        parser.add_argument(
            '--report-type',
            type=str,
            choices=['daily', 'monthly', 'ingredient', 'all'],
            default='all',
            help='Qaysi turdagi hisobotlarni tozalash',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        archive = options['archive']
        report_type = options['report_type']

        cutoff_date = date.today() - timedelta(days=days)

        self.stdout.write(
            self.style.SUCCESS(f'Hisobotlarni tozalash jarayoni boshlandi...')
        )
        self.stdout.write(f'Chegara sanasi: {cutoff_date}')
        self.stdout.write(f'Hisobot turi: {report_type}')
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN rejimi: hech narsa o\'chirilmaydi')
            )
        if archive:
            self.stdout.write(
                self.style.WARNING('ARXIV rejimi: hisobotlar arxivlanadi')
            )

        total_deleted = 0

        # Kunlik hisobotlar
        if report_type in ['daily', 'all']:
            daily_reports = DailyReport.objects.filter(
                report_date__lt=cutoff_date
            )
            daily_count = daily_reports.count()

            if daily_count > 0:
                self.stdout.write(f'\n📅 Kunlik hisobotlar: {daily_count} ta topildi')

                if not dry_run:
                    if archive:
                        # Arxivlash logikasi (kelajakda)
                        self.stdout.write(
                            self.style.WARNING('Arxivlash funksiyasi hozircha ishlab chiqilmoqda')
                        )
                    else:
                        daily_reports.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {daily_count} ta kunlik hisobot o\'chirildi')
                        )
                        total_deleted += daily_count
                else:
                    self.stdout.write(f'  - O\'chiriladigan: {daily_count} ta')
            else:
                self.stdout.write(f'📅 Kunlik hisobotlar: tozalash uchun hech narsa yo\'q')

        # Oylik hisobotlar
        if report_type in ['monthly', 'all']:
            monthly_reports = MonthlyReport.objects.filter(
                report_month__lt=cutoff_date
            )
            monthly_count = monthly_reports.count()

            if monthly_count > 0:
                self.stdout.write(f'\n📊 Oylik hisobotlar: {monthly_count} ta topildi')

                if not dry_run:
                    if archive:
                        # Arxivlash logikasi (kelajakda)
                        self.stdout.write(
                            self.style.WARNING('Arxivlash funksiyasi hozircha ishlab chiqilmoqda')
                        )
                    else:
                        monthly_reports.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {monthly_count} ta oylik hisobot o\'chirildi')
                        )
                        total_deleted += monthly_count
                else:
                    self.stdout.write(f'  - O\'chiriladigan: {monthly_count} ta')
            else:
                self.stdout.write(f'📊 Oylik hisobotlar: tozalash uchun hech narsa yo\'q')

        # Ingredient hisobotlari
        if report_type in ['ingredient', 'all']:
            ingredient_reports = IngredientUsageReport.objects.filter(
                report_date__lt=cutoff_date
            )
            ingredient_count = ingredient_reports.count()

            if ingredient_count > 0:
                self.stdout.write(f'\n🧪 Ingredient hisobotlari: {ingredient_count} ta topildi')

                if not dry_run:
                    if archive:
                        # Arxivlash logikasi (kelajakda)
                        self.stdout.write(
                            self.style.WARNING('Arxivlash funksiyasi hozircha ishlab chiqilmoqda')
                        )
                    else:
                        ingredient_reports.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ {ingredient_count} ta ingredient hisoboti o\'chirildi')
                        )
                        total_deleted += ingredient_count
                else:
                    self.stdout.write(f'  - O\'chiriladigan: {ingredient_count} ta')
            else:
                self.stdout.write(f'🧪 Ingredient hisobotlari: tozalash uchun hech narsa yo\'q')

        # Statistika ko'rsatish
        self.show_statistics()

        # Xulosa
        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN tugadi! Hech narsa o\'chirilmadi.')
            )
            self.stdout.write(f'O\'chiriladigan jami: {total_deleted} ta hisobot')
            self.stdout.write('Haqiqiy tozalash uchun --dry-run flagini olib tashlang.')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Tozalash tugadi! Jami o\'chirildi: {total_deleted} ta hisobot')
            )

    def show_statistics(self):
        """Joriy hisobotlar statistikasi"""
        self.stdout.write('\n📈 Joriy hisobotlar statistikasi:')

        # Kunlik hisobotlar
        daily_count = DailyReport.objects.count()
        daily_latest = DailyReport.objects.order_by('-report_date').first()
        daily_oldest = DailyReport.objects.order_by('report_date').first()

        self.stdout.write(f'  📅 Kunlik: {daily_count} ta')
        if daily_latest and daily_oldest:
            self.stdout.write(f'     - Eng yangi: {daily_latest.report_date}')
            self.stdout.write(f'     - Eng eski: {daily_oldest.report_date}')

        # Oylik hisobotlar
        monthly_count = MonthlyReport.objects.count()
        monthly_latest = MonthlyReport.objects.order_by('-report_month').first()
        monthly_oldest = MonthlyReport.objects.order_by('report_month').first()

        self.stdout.write(f'  📊 Oylik: {monthly_count} ta')
        if monthly_latest and monthly_oldest:
            self.stdout.write(f'     - Eng yangi: {monthly_latest.report_month.strftime("%Y-%m")}')
            self.stdout.write(f'     - Eng eski: {monthly_oldest.report_month.strftime("%Y-%m")}')

        # Ingredient hisobotlari
        ingredient_count = IngredientUsageReport.objects.count()
        self.stdout.write(f'  🧪 Ingredient: {ingredient_count} ta')

        # Jami
        total_count = daily_count + monthly_count + ingredient_count
        self.stdout.write(f'  📝 Jami: {total_count} ta hisobot')