# notifications/models.py
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('LOW_STOCK', 'Kam zaxira'),
        ('HIGH_WASTE', 'Yuqori chiqindi'),
        ('MEAL_READY', 'Ovqat tayyor'),
        ('MONTHLY_REPORT', 'Oylik hisobot'),
        ('SYSTEM_ALERT', 'Tizim ogohlantirishi'),
        ('EXPIRY_WARNING', 'Muddat ogohlantirishi')
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Past'),
        ('MEDIUM', 'O\'rta'),
        ('HIGH', 'Yuqori'),
        ('URGENT', 'Juda muhim')
    ]

    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipient = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='sent_notifications', null=True,
                               blank=True)
    is_read = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    related_object_id = models.IntegerField(null=True, blank=True)
    action_url = models.CharField(max_length=255, null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

    class Meta:
        verbose_name = "Bildirishnoma"
        verbose_name_plural = "Bildirishnomalar"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read'], name='idx_notif_rec_read'),
            models.Index(fields=['type', 'created_at'], name='idx_notification_type_created'),
        ]


class NotificationPreference(models.Model):
    FREQUENCY_CHOICES = [
        ('REAL_TIME', 'Real vaqtda'),
        ('HOURLY', 'Har soatda'),
        ('DAILY', 'Har kuni'),
        ('WEEKLY', 'Har hafta'),
    ]

    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    browser_notifications = models.BooleanField(default=True)
    low_stock_alerts = models.BooleanField(default=True)
    waste_alerts = models.BooleanField(default=True)
    meal_alerts = models.BooleanField(default=False)
    report_alerts = models.BooleanField(default=True)
    low_stock_threshold = models.FloatField(default=10.0)
    notification_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='REAL_TIME')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} bildirishnoma sozlamalari"

    class Meta:
        verbose_name = "Bildirishnoma sozlamasi"
        verbose_name_plural = "Bildirishnoma sozlamalari"


class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=50)
    subject_template = models.CharField(max_length=200)
    message_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Bildirishnoma shabloni"
        verbose_name_plural = "Bildirishnoma shablonlari"