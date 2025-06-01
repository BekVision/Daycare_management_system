from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import IngredientCategory, Ingredient, Stock, StockTransaction


class IngredientCategoryForm(forms.ModelForm):
    class Meta:
        model = IngredientCategory
        fields = ['name', 'description', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kategoriya nomi'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Kategoriya haqida qisqa tavsif'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_display_order(self):
        display_order = self.cleaned_data.get('display_order')
        if display_order < 0:
            raise ValidationError('Tartib raqami noldan kichik bo\'lmasligi kerak')
        return display_order


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'category', 'unit', 'min_threshold', 'max_threshold',
                  'cost_per_unit', 'barcode', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingredient nomi'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'kg, litr, dona, kv.m'
            }),
            'min_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Minimal zaxira miqdori'
            }),
            'max_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Maksimal zaxira miqdori'
            }),
            'cost_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Birlik narxi (so\'m)'
            }),
            'barcode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Shtrix kod (ixtiyoriy)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingredient haqida ma\'lumot'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_threshold = cleaned_data.get('min_threshold')
        max_threshold = cleaned_data.get('max_threshold')

        if min_threshold and max_threshold and min_threshold > max_threshold:
            raise ValidationError('Minimal chegara maksimal chegaradan katta bo\'lmasligi kerak')

        return cleaned_data


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['current_quantity', 'reserved_quantity', 'last_restock_date', 'expiry_date']
        widgets = {
            'current_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Joriy miqdor'
            }),
            'reserved_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Rezerv qilingan miqdor'
            }),
            'last_restock_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        current_quantity = cleaned_data.get('current_quantity')
        reserved_quantity = cleaned_data.get('reserved_quantity')

        if current_quantity and reserved_quantity and reserved_quantity > current_quantity:
            raise ValidationError('Rezerv miqdor joriy miqdordan ko\'p bo\'lmasligi kerak')

        return cleaned_data


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['ingredient', 'transaction_type', 'quantity', 'unit_cost',
                  'supplier', 'invoice_number', 'expiry_date', 'notes']
        widgets = {
            'ingredient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Miqdor'
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Birlik narxi (so\'m)'
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
                'rows': 3,
                'placeholder': 'Qo\'shimcha eslatmalar'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat faol ingredientlarni ko'rsatish
        self.fields['ingredient'].queryset = Ingredient.objects.filter(is_active=True)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise ValidationError('Miqdor noldan katta bo\'lishi kerak')
        return quantity


class StockAdjustmentForm(forms.Form):
    """Stock tuzatish uchun alohida form"""
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Ingredient'
    )
    new_quantity = forms.FloatField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Yangi miqdor'
        }),
        label='Yangi miqdor'
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Tuzatish sababi'
        }),
        label='Sabab'
    )


class InventorySearchForm(forms.Form):
    """Ombor qidiruv formi"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingredient nomi bo\'yicha qidirish'
        })
    )
    category = forms.ModelChoiceField(
        queryset=IngredientCategory.objects.filter(is_active=True),
        required=False,
        empty_label='Barcha kategoriyalar',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    stock_status = forms.ChoiceField(
        choices=[
            ('', 'Barcha holatlar'),
            ('available', 'Mavjud'),
            ('low', 'Kam'),
            ('out', 'Tugagan'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    unit = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Birlik'
        })
    )


class TransactionFilterForm(forms.Form):
    """Tranzaksiya filtrlash formi"""
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.filter(is_active=True),
        required=False,
        empty_label='Barcha ingredientlar',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    transaction_type = forms.ChoiceField(
        choices=[('', 'Barcha turlar')] + StockTransaction.TRANSACTION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    supplier = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Supplier nomi'
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


class BulkStockUpdateForm(forms.Form):
    """Ko'p ingredient uchun stock yangilash"""
    ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Ingredientlar'
    )
    action = forms.ChoiceField(
        choices=[
            ('restock', 'Qayta to\'ldirish'),
            ('adjust', 'Tuzatish'),
            ('reserve', 'Rezerv qilish'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Amal'
    )
    quantity = forms.FloatField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Miqdor'
        }),
        label='Miqdor'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Eslatmalar'
        }),
        label='Izoh'
    )


class StockUpdateForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['current_quantity', 'last_restock_date']
        widgets = {
            'current_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': 'Joriy miqdor'
            }),
            'last_restock_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
        labels = {
            'current_quantity': 'Joriy miqdor',
            'last_restock_date': 'Oxirgi to\'ldirilgan vaqt'
        }