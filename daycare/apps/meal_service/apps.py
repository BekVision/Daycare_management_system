from django.apps import AppConfig


class MealServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.meal_service'
    verbose_name = 'Ovqat Xizmatlari'

    def ready(self):
        import apps.meal_service.signals