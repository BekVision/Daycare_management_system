from django import forms
from django.core.exceptions import ValidationError
from .models import IngredientCategory, Ingredient, Stock, StockTransaction


class IngredientCategoryForm(forms.ModelForm):
    class Meta:
        model = IngredientCategory
        fields = ['name', 'description', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kategoriya nomini kiriting'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Kategoriya haqida qisqacha ma\'lumot',
                'rows': 3
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Kategoriya nomi',
            'description': 'Tavsif',
            'display_order': 'Tartib raqami',
            'is_active': 'Faol'
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = [
            'name', 'unit', 'category', 'min_threshold', 'max_threshold',
            'cost_per_unit', 'barcode', 'description', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingredient nomini kiriting'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masalan: kg, dona, litr'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'min_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Minimal miqdor'
            }),
            'max_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Maksimal miqdor (ixtiyoriy)'
            }),
            'cost_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Birlik narxi'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Barcode (ixtiyoriy)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ingredient haqida ma\'lumot',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Ingredient nomi',
            'unit': 'O\'lchov birligi',
            'category': 'Kategoriya',
            'min_threshold': 'Minimal chegara',
            'max_threshold': 'Maksimal chegara',
            'cost_per_unit': 'Birlik narxi',
            'barcode': 'Barcode',
            'description': 'Tavsif',
            'is_active': 'Faol'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat faol kategoriyalarni ko'rsatish
        self.fields['category'].queryset = IngredientCategory.objects.filter(is_active=True)

    def clean_min_threshold(self):
        min_threshold = self.cleaned_data.get('min_threshold')
        if min_threshold is not None and min_threshold < 0:
            raise ValidationError("Minimal chegara noldan kichik bo'lmasligi kerak")
        return min_threshold

    def clean_max_threshold(self):
        max_threshold = self.cleaned_data.get('max_threshold')
        if max_threshold is not None and max_threshold < 0:
            raise ValidationError("Maksimal chegara noldan kichik bo'lmasligi kerak")
        return max_threshold

    def clean(self):
        cleaned_data = super().clean()
        min_threshold = cleaned_data.get('min_threshold')
        max_threshold = cleaned_data.get('max_threshold')

        if min_threshold is not None and max_threshold is not None:
            if min_threshold > max_threshold:
                raise ValidationError("Minimal chegara maksimal chegaradan katta bo'lmasligi kerak")

        return cleaned_data


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = [
            'ingredient', 'current_quantity', 'reserved_quantity',
            'last_restock_date', 'expiry_date'
        ]
        widgets = {
            'ingredient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'current_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Joriy miqdor'
            }),
            'reserved_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Zaxira miqdor'
            }),
            'last_restock_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'ingredient': 'Ingredient',
            'current_quantity': 'Joriy miqdor',
            'reserved_quantity': 'Zaxira miqdor',
            'last_restock_date': 'Oxirgi to\'ldirish sanasi',
            'expiry_date': 'Muddati tugash sanasi'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat faol ingredientlarni ko'rsatish
        self.fields['ingredient'].queryset = Ingredient.objects.filter(is_active=True)


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = [
            'ingredient', 'transaction_type', 'quantity', 'unit_cost',
            'total_cost', 'supplier', 'invoice_number', 'expiry_date', 'notes'
        ]
        widgets = {
            'ingredient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'placeholder': 'Miqdor'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Birlik narxi'
            }),
            'total_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Umumiy narx'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Yetkazib beruvchi nomi'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hisob-faktura raqami'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Qo\'shimcha ma\'lumotlar',
                'rows': 3
            })
        }
        labels = {
            'ingredient': 'Ingredient',
            'transaction_type': 'Tranzaksiya turi',
            'quantity': 'Miqdor',
            'unit_cost': 'Birlik narxi',
            'total_cost': 'Umumiy narx',
            'supplier': 'Yetkazib beruvchi',
            'invoice_number': 'Hisob-faktura raqami',
            'expiry_date': 'Muddati tugash sanasi',
            'notes': 'Izohlar'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat faol ingredientlarni ko'rsatish
        self.fields['ingredient'].queryset = Ingredient.objects.filter(is_active=True)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise ValidationError("Miqdor noldan katta bo'lishi kerak")
        return quantity

    def clean_unit_cost(self):
        unit_cost = self.cleaned_data.get('unit_cost')
        if unit_cost is not None and unit_cost < 0:
            raise ValidationError("Birlik narxi noldan kichik bo'lmasligi kerak")
        return unit_cost

    def clean_total_cost(self):
        total_cost = self.cleaned_data.get('total_cost')
        if total_cost is not None and total_cost < 0:
            raise ValidationError("Umumiy narx noldan kichik bo'lmasligi kerak")
        return total_cost

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        unit_cost = cleaned_data.get('unit_cost')
        total_cost = cleaned_data.get('total_cost')

        # Agar quantity va unit_cost kiritilgan bo'lsa, total_cost ni avtomatik hisoblash
        if quantity is not None and unit_cost is not None and total_cost is None:
            cleaned_data['total_cost'] = quantity * unit_cost

        return cleaned_data


class StockAdjustmentForm(forms.ModelForm):
    """Zaxira miqdorini sozlash uchun maxsus form"""
    adjustment_reason = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sozlash sababini kiriting'
        }),
        label='Sozlash sababi'
    )

    class Meta:
        model = StockTransaction
        fields = ['ingredient', 'quantity', 'notes']
        widgets = {
            'ingredient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Yangi miqdor'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Qo\'shimcha ma\'lumotlar',
                'rows': 3
            })
        }
        labels = {
            'ingredient': 'Ingredient',
            'quantity': 'Yangi miqdor',
            'notes': 'Izohlar'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ingredient'].queryset = Ingredient.objects.filter(is_active=True)

    def save(self, commit=True, user=None):
        # transaction_type ni ADJUSTMENT ga o'rnatish
        self.instance.transaction_type = 'ADJUSTMENT'
        if user:
            self.instance.created_by = user
        return super().save(commit)


class StockSearchForm(forms.Form):
    """Zaxira qidiruv formi"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingredient nomi bo\'yicha qidirish...'
        }),
        label='Qidirish'
    )

    category = forms.ModelChoiceField(
        queryset=IngredientCategory.objects.filter(is_active=True),
        required=False,
        empty_label="Barcha kategoriyalar",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Kategoriya'
    )

    low_stock_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Faqat kam zaxiralar'
    )

    expired_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Faqat muddati tugagan'
    )