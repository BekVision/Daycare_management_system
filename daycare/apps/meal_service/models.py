from django.db import models


class MealService(models.Model):
    MEAL_TYPES = [
        ('BREAKFAST', 'Nonushta'),
        ('LUNCH', 'Tushlik'),
        ('DINNER', 'Kechki ovqat'),
        ('SNACK', 'Yengil ovqat'),
    ]

    STATUS_CHOICES = [
        ('PLANNED', 'Rejalashtirilgan'),
        ('PREPARING', 'Tayyorlanmoqda'),
        ('READY', 'Tayyor'),
        ('SERVED', 'Berildi'),
        ('CANCELLED', 'Bekor qilindi'),
    ]

    meal = models.ForeignKey('meals.Meal', on_delete=models.CASCADE, related_name='services')
    portions_planned = models.IntegerField()
    portions_served = models.IntegerField()
    service_date = models.DateField()
    service_time = models.TimeField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    waste_quantity = models.FloatField(default=0)
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    served_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='served_meals')
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='created_meal_services')
    served_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.meal.name} - {self.get_meal_type_display()} ({self.service_date})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.portions_planned <= 0:
            raise ValidationError("Rejalashtirilgan porsiyalar soni noldan katta bo'lishi kerak")
        if self.portions_served < 0:
            raise ValidationError("Berilgan porsiyalar soni manfiy bo'lishi mumkin emas")
        if self.portions_served > self.portions_planned:
            raise ValidationError("Berilgan porsiyalar soni rejalashtirilgandan ko'p bo'lishi mumkin emas")

    class Meta:
        verbose_name = "Ovqat xizmati"
        verbose_name_plural = "Ovqat xizmatlari"
        indexes = [
            models.Index(fields=['service_date'], name='idx_mealservice_date'),
            models.Index(fields=['served_by', 'served_at'], name='idx_mealservice_served_by_date'),
        ]


class ServiceLog(models.Model):
    meal_service = models.ForeignKey(MealService, on_delete=models.CASCADE, related_name='logs')
    ingredient = models.ForeignKey('inventory.Ingredient', on_delete=models.CASCADE, related_name='service_logs')
    quantity_planned = models.FloatField()
    quantity_used = models.FloatField()
    stock_before = models.FloatField()
    stock_after = models.FloatField()
    unit_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    waste_quantity = models.FloatField(default=0)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.meal_service} - {self.ingredient.name}"

    class Meta:
        verbose_name = "Xizmat qayd etish"
        verbose_name_plural = "Xizmat qayd etishlari"
        indexes = [
            models.Index(fields=['meal_service', 'ingredient'], name='idx_svc_ing'),
        ]


class ServiceFeedback(models.Model):
    meal_service = models.ForeignKey(MealService, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='meal_feedbacks')
    taste_rating = models.IntegerField(null=True, blank=True)
    portion_rating = models.IntegerField(null=True, blank=True)
    overall_rating = models.IntegerField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.meal_service} - {self.feedback_by.username} bahosi"

    class Meta:
        verbose_name = "Xizmat bahosi"
        verbose_name_plural = "Xizmat baholari"