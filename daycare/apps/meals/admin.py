from django.contrib import admin

from .models import *

admin.site.register(MealCategory)
admin.site.register(Meal)
admin.site.register(Recipe)
admin.site.register(MealNutrition)
