from django.core.management.base import BaseCommand
from apps.common.models import AppSettings


class Command(BaseCommand):
    help = 'Standart tizim sozlamalarini yaratish'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('Standart sozlamalar yaratilmoqda...')
        )

        # Standart sozlamalar ro'yxati
        default_settings = [
            {
                'key': 'SITE_NAME',
                'value': 'Bog\'cha Ombor va Ovqat Tizimi',
                'data_type': 'STRING',
                'description': 'Sayt nomi',
                'is_editable': True
            },
            {
                'key': 'ADMIN_EMAILS',
                'value': 'admin@daycare.com',
                'data_type': 'STRING',
                'description': 'Administrator email manzillari (vergul bilan ajratilgan)',
                'is_editable': True
            },
            {
                'key': 'MAX_PORTION_SIZE',
                'value': '10',
                'data_type': 'INTEGER',
                'description': 'Maksimal porsiya hajmi',
                'is_editable': True
            },
            {
                'key': 'MIN_STOCK_THRESHOLD',
                'value': '5.0',
                'data_type': 'FLOAT',
                'description': 'Minimal zaxira chegarasi',
                'is_editable': True
            },
            {
                'key': 'ENABLE_NOTIFICATIONS',
                'value': 'true',
                'data_type': 'BOOLEAN',
                'description': 'Bildirishnomalarni yoqish/o\'chirish',
                'is_editable': True
            },
            {
                'key': 'WASTE_THRESHOLD_PERCENTAGE',
                'value': '15.0',
                'data_type': 'FLOAT',
                'description': 'Chiqindi chegarasi (foizda)',
                'is_editable': True
            },
            {
                'key': 'INVENTORY_ALERT_SETTINGS',
                'value': '{"low_stock": true, "expiry_warning": true, "days_before_expiry": 7}',
                'data_type': 'JSON',
                'description': 'Ombor ogohlantirish sozlamalari',
                'is_editable': True
            },
            {
                'key': 'MEAL_SERVICE_HOURS',
                'value': '{"breakfast": "08:00", "lunch": "12:00", "dinner": "18:00"}',
                'data_type': 'JSON',
                'description': 'Ovqat berish vaqtlari',
                'is_editable': True
            },
            {
                'key': 'AUTO_CLEANUP_DAYS',
                'value': '90',
                'data_type': 'INTEGER',
                'description': 'Loglarni avtomatik tozalash (kunlarda)',
                'is_editable': True
            },
            {
                'key': 'DEFAULT_CURRENCY',
                'value': 'UZS',
                'data_type': 'STRING',
                'description': 'Standart valyuta',
                'is_editable': True
            },
            {
                'key': 'SYSTEM_VERSION',
                'value': '1.0.0',
                'data_type': 'STRING',
                'description': 'Tizim versiyasi',
                'is_editable': False
            },
            {
                'key': 'MAINTENANCE_MODE',
                'value': 'false',
                'data_type': 'BOOLEAN',
                'description': 'Texnik ishlar rejimi',
                'is_editable': True
            },
            {
                'key': 'MAX_UPLOAD_SIZE',
                'value': '5242880',  # 5MB
                'data_type': 'INTEGER',
                'description': 'Maksimal fayl yuklash hajmi (baytlarda)',
                'is_editable': True
            },
            {
                'key': 'ALLOWED_IMAGE_TYPES',
                'value': '["jpg", "jpeg", "png", "gif"]',
                'data_type': 'JSON',
                'description': 'Ruxsat etilgan rasm formatlari',
                'is_editable': True
            },
            {
                'key': 'SESSION_TIMEOUT',
                'value': '3600',
                'data_type': 'INTEGER',
                'description': 'Sessiya tugash vaqti (soniyalarda)',
                'is_editable': True
            }
        ]

        created_count = 0
        updated_count = 0

        for setting_data in default_settings:
            setting, created = AppSettings.objects.get_or_create(
                key=setting_data['key'],
                defaults={
                    'value': setting_data['value'],
                    'data_type': setting_data['data_type'],
                    'description': setting_data['description'],
                    'is_editable': setting_data['is_editable']
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Yaratildi: {setting_data["key"]}')
                )
            else:
                # Mavjud sozlamaning faqat tavsifini yangilash (agar bo'sh bo'lsa)
                if not setting.description and setting_data['description']:
                    setting.description = setting_data['description']
                    setting.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'📝 Yangilandi: {setting_data["key"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.HTTP_INFO(f'ℹ️  Mavjud: {setting_data["key"]}')
                    )

        # Natija
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Muvaffaqiyat!\n'
                f'  - Yaratildi: {created_count} ta sozlama\n'
                f'  - Yangilandi: {updated_count} ta sozlama\n'
                f'  - Jami: {AppSettings.objects.count()} ta sozlama'
            )
        )

        # Qo'shimcha ma'lumot
        self.stdout.write('\n' + self.style.HTTP_INFO('💡 Foydalanish:'))
        self.stdout.write('   - Sozlamalarni ko\'rish: /common/settings/')
        self.stdout.write('   - Admin panelda tahrirlash: /admin/common/appsettings/')
        self.stdout.write('   - Kodda ishlatish: get_setting("SITE_NAME")')

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Standart sozlamalar tayyor!')
        )