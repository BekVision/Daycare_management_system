from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time

from .models import MealService, ServiceFeedback
from apps.meals.models import Meal


class MealServiceForm(forms.ModelForm):
    """Ovqat xizmati yaratish formasi"""

    class Meta:
        model = MealService
        fields = [
            'meal', 'portions_planned', 'service_date',
            'service_time', 'meal_type', 'notes'
        ]
        widgets = {
            'meal': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'onchange': 'checkIngredients()'
            }),
            'portions_planned': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'required': True,
                'onchange': 'checkIngredients()'
            }),
            'service_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'service_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'meal_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar...'
            })
        }
        labels = {
            'meal': 'Ovqat',
            'portions_planned': 'Rejalashtirilgan porsiyalar',
            'service_date': 'Xizmat sanasi',
            'service_time': 'Xizmat vaqti',
            'meal_type': 'Ovqat turi',
            'notes': 'Izohlar'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat faol ovqatlarni ko'rsatish
        self.fields['meal'].queryset = Meal.objects.filter(is_active=True).select_related('category')

        # Bugungi sana
        if not self.instance.pk:
            self.fields['service_date'].initial = date.today()
            self.fields['service_time'].initial = time(12, 0)  # 12:00 default

    def clean_service_date(self):
        service_date = self.cleaned_data.get('service_date')
        if service_date and service_date < date.today():
            raise ValidationError("Xizmat sanasi bugungi sanadan oldingi bo'lishi mumkin emas!")
        return service_date

    def clean_portions_planned(self):
        portions_planned = self.cleaned_data.get('portions_planned')
        if portions_planned and portions_planned <= 0:
            raise ValidationError("Porsiyalar soni 0 dan katta bo'lishi kerak!")
        if portions_planned and portions_planned > 1000:
            raise ValidationError("Porsiyalar soni 1000 dan oshmasligi kerak!")
        return portions_planned

    def clean(self):
        cleaned_data = super().clean()
        meal = cleaned_data.get('meal')
        portions_planned = cleaned_data.get('portions_planned')
        service_date = cleaned_data.get('service_date')
        service_time = cleaned_data.get('service_time')

        # Bir xil ovqat, sana va vaqtda xizmat borligini tekshirish
        if meal and service_date and service_time and not self.instance.pk:
            existing_service = MealService.objects.filter(
                meal=meal,
                service_date=service_date,
                service_time=service_time
            ).exists()

            if existing_service:
                raise ValidationError(
                    "Bu ovqat uchun berilgan sana va vaqtda allaqachon xizmat mavjud!"
                )

        return cleaned_data


class MealServiceUpdateForm(forms.ModelForm):
    """Ovqat xizmatini yangilash formasi"""

    class Meta:
        model = MealService
        fields = [
            'portions_planned', 'portions_served', 'service_date',
            'service_time', 'meal_type', 'status', 'waste_quantity', 'notes'
        ]
        widgets = {
            'portions_planned': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'required': True
            }),
            'portions_served': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'required': True
            }),
            'service_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'service_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'meal_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'waste_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar...'
            })
        }
        labels = {
            'portions_planned': 'Rejalashtirilgan porsiyalar',
            'portions_served': 'Berilgan porsiyalar',
            'service_date': 'Xizmat sanasi',
            'service_time': 'Xizmat vaqti',
            'meal_type': 'Ovqat turi',
            'status': 'Holat',
            'waste_quantity': 'Chiqindi miqdori',
            'notes': 'Izohlar'
        }

    def clean_portions_served(self):
        portions_served = self.cleaned_data.get('portions_served')
        portions_planned = self.cleaned_data.get('portions_planned') or self.instance.portions_planned

        if portions_served is not None:
            if portions_served < 0:
                raise ValidationError("Berilgan porsiyalar soni manfiy bo'lishi mumkin emas!")
            if portions_served > portions_planned:
                raise ValidationError("Berilgan porsiyalar rejalashtirilgandan ko'p bo'lishi mumkin emas!")

        return portions_served

    def clean_waste_quantity(self):
        waste_quantity = self.cleaned_data.get('waste_quantity')
        if waste_quantity and waste_quantity < 0:
            raise ValidationError("Chiqindi miqdori manfiy bo'lishi mumkin emas!")
        return waste_quantity


class ServiceFeedbackForm(forms.ModelForm):
    """Xizmat baholash formasi"""

    class Meta:
        model = ServiceFeedback
        fields = ['taste_rating', 'portion_rating', 'overall_rating', 'comments']
        widgets = {
            'taste_rating': forms.Select(
                choices=[(i, f"{i} yulduz") for i in range(1, 6)],
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'portion_rating': forms.Select(
                choices=[(i, f"{i} yulduz") for i in range(1, 6)],
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'overall_rating': forms.Select(
                choices=[(i, f"{i} yulduz") for i in range(1, 6)],
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Fikr-mulohazalaringizni yozing...'
            })
        }
        labels = {
            'taste_rating': 'Ta\'m bahosi',
            'portion_rating': 'Porsiya bahosi',
            'overall_rating': 'Umumiy baholash',
            'comments': 'Izohlar'
        }

    def clean_taste_rating(self):
        rating = self.cleaned_data.get('taste_rating')
        if rating and (rating < 1 or rating > 5):
            raise ValidationError("Baholash 1 dan 5 gacha bo'lishi kerak!")
        return rating

    def clean_portion_rating(self):
        rating = self.cleaned_data.get('portion_rating')
        if rating and (rating < 1 or rating > 5):
            raise ValidationError("Baholash 1 dan 5 gacha bo'lishi kerak!")
        return rating

    def clean_overall_rating(self):
        rating = self.cleaned_data.get('overall_rating')
        if rating and (rating < 1 or rating > 5):
            raise ValidationError("Baholash 1 dan 5 gacha bo'lishi kerak!")
        return rating


class MealServiceFilterForm(forms.Form):
    """Ovqat xizmatlari filtrlash formasi"""

    MEAL_TYPE_CHOICES = [('', 'Barchasi')] + MealService.MEAL_TYPES
    STATUS_CHOICES = [('', 'Barchasi')] + MealService.STATUS_CHOICES

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Boshlanish sanasi'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Tugash sanasi'
    )

    meal_type = forms.ChoiceField(
        choices=MEAL_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Ovqat turi'
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Holat'
    )

    meal = forms.ModelChoiceField(
        queryset=Meal.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label='Barcha ovqatlar',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Ovqat'
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError("Boshlanish sanasi tugash sanasidan katta bo'lishi mumkin emas!")

        return cleaned_data