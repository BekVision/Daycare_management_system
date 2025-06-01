from django.db import models


class AppSettings(models.Model):
    DATA_TYPE_CHOICES = [
        ('STRING', 'Matn'),
        ('INTEGER', 'Butun son'),
        ('FLOAT', 'Haqiqiy son'),
        ('BOOLEAN', 'Mantiqiy'),
        ('JSON', 'JSON'),
    ]

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(null=True, blank=True)
    data_type = models.CharField(max_length=20, choices=DATA_TYPE_CHOICES, default='STRING')
    is_editable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_typed_value(self):
        """Return value in correct data type"""
        if self.data_type == 'INTEGER':
            return int(self.value)
        elif self.data_type == 'FLOAT':
            return float(self.value)
        elif self.data_type == 'BOOLEAN':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'JSON':
            import json
            return json.loads(self.value)
        return self.value

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = "Dastur sozlamasi"
        verbose_name_plural = "Dastur sozlamalari"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        # User actions
        ('USER_LOGIN', 'Foydalanuvchi kirdi'),
        ('USER_LOGOUT', 'Foydalanuvchi chiqdi'),
        ('USER_CREATED', 'Foydalanuvchi yaratildi'),
        ('USER_UPDATED', 'Foydalanuvchi yangilandi'),
        ('USER_DELETED', 'Foydalanuvchi o\'chirildi'),

        # Inventory actions
        ('INGREDIENT_ADDED', 'Mahsulot qo\'shildi'),
        ('INGREDIENT_UPDATED', 'Mahsulot yangilandi'),
        ('INGREDIENT_DELETED', 'Mahsulot o\'chirildi'),
        ('DELIVERY_RECEIVED', 'Yetkazib berish qabul qilindi'),
        ('INVENTORY_ADJUSTED', 'Inventar tuzatildi'),

        # Meal actions
        ('MEAL_CREATED', 'Taom yaratildi'),
        ('MEAL_UPDATED', 'Taom yangilandi'),
        ('MEAL_DELETED', 'Taom o\'chirildi'),
        ('MEAL_SERVED', 'Taom berildi'),
        ('MEAL_CANCELLED', 'Taom bekor qilindi'),

        # System actions
        ('REPORT_GENERATED', 'Hisobot yaratildi'),
        ('NOTIFICATION_SENT', 'Bildirishnoma yuborildi'),
        ('ALERT_TRIGGERED', 'Ogohlantirish ishga tushdi'),
        ('SYSTEM_BACKUP', 'Tizim zaxirasi'),

        # Security actions
        ('LOGIN_FAILED', 'Muvaffaqiyatsiz kirish'),
        ('PERMISSION_DENIED', 'Ruxsat berilmadi'),
        ('SUSPICIOUS_ACTIVITY', 'Shubhali faoliyat'),
    ]

    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=50)
    object_id = models.IntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"

    class Meta:
        verbose_name = "Faoliyat qayd etishi"
        verbose_name_plural = "Faoliyat qayd etishlari"
        ordering = ['-timestamp']


class SystemHealth(models.Model):
    class StatusChoices(models.TextChoices):
        HEALTHY = "HEALTHY", "Sog'lom"
        WARNING = "WARNING", "Ogohlantirish"
        ERROR = "ERROR", "Xato"
        DOWN = "DOWN", "Ishlamayapti"

    COMPONENT_CHOICES = [
        ('DATABASE', 'Ma\'lumotlar bazasi'),
        ('REDIS', 'Redis'),
        ('CELERY', 'Celery'),
        ('EMAIL', 'Email'),
        ('STORAGE', 'Fayl saqlash'),
        ('API', 'API'),
        ('WEBSOCKET', 'WebSocket'),
    ]

    component = models.CharField(max_length=50, choices=COMPONENT_CHOICES)
    status = models.CharField(max_length=20, choices=StatusChoices.choices)
    response_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_component_display()} - {self.get_status_display()} - {self.checked_at}"

    class Meta:
        verbose_name = "Tizim salomatligi"
        verbose_name_plural = "Tizim salomatligi yozuvlari"
        ordering = ['-checked_at']