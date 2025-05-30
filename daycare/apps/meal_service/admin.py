from django.contrib import admin

from .models import *

admin.site.register(MealService)
admin.site.register(ServiceLog)
admin.site.register(ServiceFeedback)
