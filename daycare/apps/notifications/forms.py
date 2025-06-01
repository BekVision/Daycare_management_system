# notifications/forms.py
from django import forms
from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    """Bildirishnoma sozlamalari formi"""

    class Meta:
        model = NotificationPreference
        fields = [
            'email_notifications', 'sms_notifications', 'browser_notifications',
            'low_stock_alerts', 'waste_alerts', 'meal_alerts', 'report_alerts',
            'low_stock_threshold', 'notification_frequency'
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'browser_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'low_stock_alerts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'waste_alerts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'meal_alerts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'report_alerts': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': '10.0'
            }),
            'notification_frequency': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'email_notifications': 'Email bildirishnomalar',
            'sms_notifications': 'SMS bildirishnomalar',
            'browser_notifications': 'Brauzer bildirishnomalari',
            'low_stock_alerts': 'Kam zaxira ogohlantirishi',
            'waste_alerts': 'Chiqindi ogohlantirishi',
            'meal_alerts': 'Ovqat ogohlantirishi',
            'report_alerts': 'Hisobot ogohlantirishi',
            'low_stock_threshold': 'Kam zaxira chegarasi (%)',
            'notification_frequency': 'Bildirishnoma chastotasi'
        }
        help_texts = {
            'low_stock_threshold': 'Zaxira bu foizdan kam bo\'lganda ogohlantirish yuborish',
            'notification_frequency': 'Qanchalik tez-tez bildirishnoma olishni xohlaysiz'
        }