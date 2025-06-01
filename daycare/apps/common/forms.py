from django import forms
from .models import AppSettings, SystemHealth, ActivityLog
import json


class AppSettingsForm(forms.ModelForm):
    class Meta:
        model = AppSettings
        fields = ['value', 'description']
        widgets = {
            'value': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Qiymatni kiriting'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Tavsif (ixtiyoriy)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Data type ga qarab widget o'zgartirish
            if self.instance.data_type == 'BOOLEAN':
                self.fields['value'].widget = forms.Select(
                    choices=[
                        ('true', 'Ha'),
                        ('false', 'Yo\'q'),
                        ('1', '1'),
                        ('0', '0'),
                    ],
                    attrs={'class': 'form-select'}
                )
            elif self.instance.data_type == 'INTEGER':
                self.fields['value'].widget = forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '1'
                })
            elif self.instance.data_type == 'FLOAT':
                self.fields['value'].widget = forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.01'
                })

    def clean_value(self):
        value = self.cleaned_data['value']
        data_type = self.instance.data_type if self.instance else 'STRING'

        # Data type ga qarab validatsiya
        if data_type == 'INTEGER':
            try:
                int(value)
            except ValueError:
                raise forms.ValidationError('Butun son kiritilishi kerak')

        elif data_type == 'FLOAT':
            try:
                float(value)
            except ValueError:
                raise forms.ValidationError('Haqiqiy son kiritilishi kerak')

        elif data_type == 'JSON':
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise forms.ValidationError('To\'g\'ri JSON format kiritilishi kerak')

        return value


class SystemHealthForm(forms.ModelForm):
    class Meta:
        model = SystemHealth
        fields = ['component', 'status', 'response_time', 'error_message', 'details']
        widgets = {
            'component': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'response_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'placeholder': 'Javob vaqti (soniya)'
            }),
            'error_message': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Xato xabari (ixtiyoriy)'
            }),
            'details': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'JSON formatida qo\'shimcha ma\'lumotlar'
            }),
        }

    def clean_details(self):
        details = self.cleaned_data.get('details')
        if details:
            try:
                json.loads(details)
            except json.JSONDecodeError:
                raise forms.ValidationError('To\'g\'ri JSON format kiritilishi kerak')
        return details


class ActivityLogFilterForm(forms.Form):
    """Activity log filter formi"""
    user = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Barcha foydalanuvchilar",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    action = forms.ChoiceField(
        choices=[('', 'Barcha amallar')] + list(ActivityLog.ACTION_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    object_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ob\'ekt turi'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.accounts.models import CustomUser
        self.fields['user'].queryset = CustomUser.objects.filter(is_active=True)


class SettingsSearchForm(forms.Form):
    """Settings qidiruv formi"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kalit so\'z yoki tavsif bo\'yicha qidirish'
        })
    )
    data_type = forms.ChoiceField(
        choices=[('', 'Barcha turlar')] + AppSettings.DATA_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )