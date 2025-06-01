from django.core.management.base import BaseCommand
from apps.common.utils import check_system_health
from apps.common.models import SystemHealth


class Command(BaseCommand):
    help = 'Tizim salomatligini tekshirish'

    def add_arguments(self, parser):
        parser.add_argument(
            '--component',
            type=str,
            help='Ma\'lum komponentni tekshirish (DATABASE, REDIS, EMAIL, STORAGE)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Batafsil ma\'lumot ko\'rsatish',
        )

    def handle(self, *args, **options):
        component = options.get('component')
        verbose = options.get('verbose', False)

        self.stdout.write(
            self.style.WARNING('Tizim salomatligini tekshirish boshlandi...')
        )

        if component:
            # Ma'lum komponentni tekshirish
            self.stdout.write(f'Komponent tekshirilmoqda: {component}')

            if component == 'DATABASE':
                from apps.common.utils import check_database_health
                result = check_database_health()
                self.display_result(result, verbose)
            elif component == 'REDIS':
                from apps.common.utils import check_redis_health
                result = check_redis_health()
                if result:
                    self.display_result(result, verbose)
                else:
                    self.stdout.write(
                        self.style.WARNING('Redis mavjud emas yoki sozlanmagan')
                    )
            elif component == 'EMAIL':
                from apps.common.utils import check_email_health
                result = check_email_health()
                self.display_result(result, verbose)
            elif component == 'STORAGE':
                from apps.common.utils import check_storage_health
                result = check_storage_health()
                self.display_result(result, verbose)
            else:
                self.stdout.write(
                    self.style.ERROR(f'Noma\'lum komponent: {component}')
                )
                return
        else:
            # Barcha komponentlarni tekshirish
            results = check_system_health()

            overall_healthy = True
            for result in results:
                self.display_result(result, verbose)
                if not result.get('healthy', False):
                    overall_healthy = False

            # Umumiy natija
            if overall_healthy:
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Barcha komponentlar sog\'lom!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('\n❌ Ba\'zi komponentlarda muammo aniqlandi!')
                )

        self.stdout.write(
            self.style.SUCCESS('Tekshiruv tugadi!')
        )

    def display_result(self, result, verbose=False):
        """Natijani chiqarish"""
        component = result['component']
        status = result['status']
        healthy = result.get('healthy', False)

        if healthy:
            icon = '✅'
            style = self.style.SUCCESS
        else:
            icon = '❌'
            style = self.style.ERROR

        # Asosiy ma'lumot
        message = f'{icon} {component}: {status}'

        if 'response_time' in result:
            message += f' ({result["response_time"]:.3f}s)'

        self.stdout.write(style(message))

        # Batafsil ma'lumot
        if verbose or not healthy:
            if 'error' in result:
                self.stdout.write(f'   Xato: {result["error"]}')

            if verbose and 'response_time' in result:
                response_time = result['response_time']
                if response_time < 0.5:
                    perf = 'Zo\'r'
                elif response_time < 1.0:
                    perf = 'Yaxshi'
                elif response_time < 2.0:
                    perf = 'O\'rtacha'
                else:
                    perf = 'Sekin'

                self.stdout.write(f'   Unumdorlik: {perf}')