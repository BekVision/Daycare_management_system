from django.contrib import admin

from .models import *

admin.site.register(DailyReport)
admin.site.register(MonthlyReport)
admin.site.register(IngredientUsageReport)