# reports/management/commands/generate_monthly_reports.py
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from datetime import date, datetime
import calendar
from reports.services import ReportService

User = get_user_model()


class Command(BaseCommand):
    help = 'Oylik hisobotlarni yaratish'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Hisobot yili',
        )
        parser.add_argument(
            '--month',
            type=int,
            help='Hisobot oyi (1-12)',
        )
        parser.add_argument(
            '--months',
            type=int,
            default=1,
            help='Necha oylik hisobot yaratish (default: 1)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Hisobot yaratuvchi foydalanuvchi username',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Mavjud hisobotlarni qayta yaratish',
        )

    def handle(self, *args, **options):
        # Foydalanuvchini topish
        user = None
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
            except User.DoesNotExist:
                raise CommandError(f'Foydalanuvchi topilmadi: {options["user"]}')
        else:
            # Default admin foydalanuvchini topish
            user = User.objects.filter(is_admin=True).first()
            if not user:
                raise CommandError('Admin foydalanuvchi topilmadi.')

        # Yil va oyni aniqlash
        if options['year'] and options['month']:
            year = options['year']
            month = options['month']

            if month < 1 or month > 12:
                raise CommandError('Oy 1-12 orasida bo\'lishi kerak.')
        else:
            # O'tgan oy uchun default
            today = date.today()
            if today.month == 1:
                year = today.year - 1
                month = 12
            else:
                year = today.year
                month = today.month - 1

        months_count = options['months']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS(f'Oylik hisobot yaratish boshlandi...')
        )
        self.stdout.write(f'Foydalanuvchi: {user.get_full_name()}')
        self.stdout.write(f'Boshlanish: {year}-{month:02d}')
        self.stdout.write(f'Oylar soni: {months_count}')

        created_count = 0
        updated_count = 0
        error_count = 0

        for i in range(months_count):
            current_month = month - i
            current_year = year

            # Yilni to'g'rilash
            while current_month < 1:
                current_month += 12
                current_year -= 1

            try:
                # Mavjud hisobotni tekshirish
                from apps.reports.models import MonthlyReport
                report_date = date(current_year, current_month, 1)
                existing_report = MonthlyReport.objects.filter(report_month=report_date).first()

                if existing_report and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'{current_year}-{current_month:02d} uchun hisobot mavjud. --force flagini ishlating.')
                    )
                    continue

                # Hisobotni yaratish
                report = ReportService.generate_monthly_report(current_year, current_month, user)

                if existing_report:
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {current_year}-{current_month:02d} uchun hisobot yangilandi (ID: {report.pk})')
                    )
                else:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {current_year}-{current_month:02d} uchun hisobot yaratildi (ID: {report.pk})')
                    )

                # Hisobot statistikalarini ko'rsatish
                self.stdout.write(f'   - Jami ovqatlar: {report.total_meals_served}')
                self.stdout.write(f'   - Jami porsiyalar: {report.total_portions_served}')
                if report.efficiency_percentage:
                    self.stdout.write(f'   - Samaradorlik: {report.efficiency_percentage:.1f}%')
                if report.waste_percentage:
                    self.stdout.write(f'   - Chiqindi: {report.waste_percentage:.1f}%')

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ {current_year}-{current_month:02d} uchun xatolik: {str(e)}')
                )

        # Xulosa
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'Oylik hisobot yaratish tugadi!')
        )
        self.stdout.write(f'Yaratildi: {created_count}')
        self.stdout.write(f'Yangilandi: {updated_count}')
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'Xatoliklar: {error_count}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Xatoliklar: {error_count}')
            )

        # Qo'shimcha ma'lumot
        if created_count > 0 or updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\nFoydalanish:')
            )
            self.stdout.write('- Web interfeys orqali hisobotlarni ko\'rish mumkin')
            self.stdout.write('- PDF/Excel formatida eksport qilish mumkin')
            self.stdout.write('- Dashboard\'da statistikalar ko\'rsatiladi')