
from django import forms
from .models import AppSettings, ActivityLog, SystemHealth
import json


class AppSettingsForm(forms.ModelForm):
    class Meta:
        model = AppSettings
        fields = ['key', 'value', 'description', 'data_type', 'is_editable']
        widgets = {
            'key': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sozlama kaliti'
            }),
            'value': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Sozlama qiymati'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Sozlama tavsifi'
            }),
            'data_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_editable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_value(self):
        value = self.cleaned_data['value']
        data_type = self.cleaned_data.get('data_type')

        if data_type == 'INTEGER':
            try:
                int(value)
            except ValueError:
                raise forms.ValidationError("Butun son kiriting")
        elif data_type == 'FLOAT':
            try:
                float(value)
            except ValueError:
                raise forms.ValidationError("Haqiqiy son kiriting")
        elif data_type == 'BOOLEAN':
            if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                raise forms.ValidationError("Mantiqiy qiymat kiriting (true/false)")
        elif data_type == 'JSON':
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise forms.ValidationError("To'g'ri JSON format kiriting")

        return value


class ActivityLogFilterForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Barcha foydalanuvchilar",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    action = forms.ChoiceField(
        choices=[('', 'Barcha harakatlar')] + ActivityLog.ACTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    object_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Obyekt turi'
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
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Xato xabari'
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Batafsil ma\'lumot (JSON format)'
            })
        }

    def clean_details(self):
        details = self.cleaned_data.get('details')
        if details:
            try:
                json.loads(details)
            except json.JSONDecodeError:
                raise forms.ValidationError("To'g'ri JSON format kiriting")
        return details
