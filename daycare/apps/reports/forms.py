# reports/forms.py
from django import forms
from django.core.exceptions import ValidationError
from datetime import date, datetime
import calendar


class ReportFilterForm(forms.Form):
    """Hisobotlarni filtrlash formi"""

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Boshlanish sanasi'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Tugash sanasi'
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError('Boshlanish sanasi tugash sanasidan katta bo\'lmasligi kerak.')

            if end_date > date.today():
                raise ValidationError('Tugash sanasi bugungi kundan katta bo\'lmasligi kerak.')

        return cleaned_data


class DailyReportGenerateForm(forms.Form):
    """Kunlik hisobot yaratish formi"""

    report_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Hisobot sanasi'
    )

    def clean_report_date(self):
        report_date = self.cleaned_data['report_date']

        if report_date > date.today():
            raise ValidationError('Kelajakdagi sana uchun hisobot yaratib bo\'lmaydi.')

        return report_date


class MonthlyReportGenerateForm(forms.Form):
    """Oylik hisobot yaratish formi"""

    MONTH_CHOICES = [
        (1, 'Yanvar'), (2, 'Fevral'), (3, 'Mart'), (4, 'Aprel'),
        (5, 'May'), (6, 'Iyun'), (7, 'Iyul'), (8, 'Avgust'),
        (9, 'Sentyabr'), (10, 'Oktyabr'), (11, 'Noyabr'), (12, 'Dekabr')
    ]

    year = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 2020,
            'max': date.today().year
        }),
        label='Yil'
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Oy'
    )

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        month = cleaned_data.get('month')

        if year and month:
            month = int(month)
            report_date = date(year, month, 1)
            today = date.today()

            if report_date.year > today.year or (report_date.year == today.year and report_date.month > today.month):
                raise ValidationError('Kelajakdagi oy uchun hisobot yaratib bo\'lmaydi.')

        return cleaned_data


class IngredientUsageFilterForm(forms.Form):
    """Ingredient ishlatish hisoboti filtri"""

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Boshlanish sanasi'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Tugash sanasi'
    )
    ingredient = forms.ModelChoiceField(
        queryset=None,  # View'da to'ldiriladi
        required=False,
        empty_label='Barcha ingredientlar',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Ingredient'
    )
    category = forms.ModelChoiceField(
        queryset=None,  # View'da to'ldiriladi
        required=False,
        empty_label='Barcha kategoriyalar',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Kategoriya'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Queryset'larni import qilish view'da amalga oshiriladi
        # chunki circular import'dan qochish uchun


class ReportExportForm(forms.Form):
    """Hisobot eksport formi"""

    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV')
    ]

    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label='Eksport formati'
    )
    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Grafiklarni qo\'shish'
    )
    include_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Batafsil ma\'lumotlarni qo\'shish'
    )