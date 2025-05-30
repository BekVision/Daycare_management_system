
from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.common'
    verbose_name = 'Umumiy'

    def ready(self):
        from .utils import create_default_settings
        try:
            create_default_settings()
        except Exception:
            pass  # Database might not be ready yet
# from django.apps import AppConfig
#
#
# class CommonConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'apps.common'
