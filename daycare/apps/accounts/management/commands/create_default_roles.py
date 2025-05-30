from django.core.management.base import BaseCommand
from accounts.models import Role
from accounts.permissions import PERMISSIONS


class Command(BaseCommand):
    help = 'Standart rollarni yaratish'

    def handle(self, *args, **options):
        roles_data = [
            {
                'name': 'admin',
                'description': 'Tizim administratori - barcha imkoniyatlarga kirish',
                'permissions': PERMISSIONS['admin']
            },
            {
                'name': 'manager',
                'description': 'Menejer - ombor va hisobotlarni boshqarish',
                'permissions': PERMISSIONS['manager']
            },
            {
                'name': 'chef',
                'description': 'Oshpaz - faqat ovqat berish imkoniyati',
                'permissions': PERMISSIONS['chef']
            }
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'permissions': role_data['permissions']
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Rol yaratildi: {role.get_name_display()}')
                )
            else:
                # Mavjud rolning ruxsatlarini yangilash
                role.permissions = role_data['permissions']
                role.save()
                self.stdout.write(
                    self.style.WARNING(f'Rol yangilandi: {role.get_name_display()}')
                )

        self.stdout.write(
            self.style.SUCCESS('Barcha standart rollar muvaffaqiyatli yaratildi!')
        )