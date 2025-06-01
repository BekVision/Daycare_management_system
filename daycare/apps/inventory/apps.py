from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory'
    verbose_name = 'Ombor va Zaxira'

    def ready(self):
        # Signals import qilish (agar kerak bo'lsa)
        try:
            import apps.inventory.signals
        except ImportError:
            pass