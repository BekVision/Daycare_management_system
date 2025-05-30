from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory'
    verbose_name = 'Inventory (Ombor)'

    def ready(self):
        # Signal larni import qilish
        import apps.inventory.signals

        # Admin panelda ko'rsatish uchun
        from django.contrib import admin

        # Inventory app uchun maxsus admin sozlamalari
        if hasattr(admin.site, '_registry'):
            # Custom admin configuration
            pass