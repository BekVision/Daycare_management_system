# meals/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Meal, MealCategory, Recipe, MealNutrition
from apps.inventory.models import Ingredient


class MealCategoryForm(forms.ModelForm):
    """Ovqat kategoriyasi formi"""

    class Meta:
        model = MealCategory
        fields = ['name', 'description', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kategoriya nomi'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Kategoriya haqida qisqacha ma\'lumot'
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
            'display_order': 'Ko\'rsatish tartibi',
            'is_active': 'Faol'
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Bir xil nomli kategoriya tekshiruvi
            qs = MealCategory.objects.filter(name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('Bu nomli kategoriya allaqachon mavjud.')
        return name


class MealForm(forms.ModelForm):
    """Ovqat formi"""

    class Meta:
        model = Meal
        fields = [
            'name', 'category', 'description', 'preparation_time',
            'cooking_time', 'difficulty_level', 'portions_per_recipe',
            'calories_per_portion', 'photo', 'instructions', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ovqat nomi'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ovqat haqida qisqacha tavsif'
            }),
            'preparation_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Daqiqalarda'
            }),
            'cooking_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Daqiqalarda'
            }),
            'difficulty_level': forms.Select(
                choices=[(i, f'Daraja {i}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'portions_per_recipe': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'calories_per_portion': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Bir porsiyadagi kaloriya'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Tayyorlash yo\'riqnomasi'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Ovqat nomi',
            'category': 'Kategoriya',
            'description': 'Tavsif',
            'preparation_time': 'Tayyorlash vaqti (daqiqa)',
            'cooking_time': 'Pishirish vaqti (daqiqa)',
            'difficulty_level': 'Qiyinlik darajasi',
            'portions_per_recipe': 'Retsept uchun porsiya soni',
            'calories_per_portion': 'Bir porsiyadagi kaloriya',
            'photo': 'Rasm',
            'instructions': 'Tayyorlash yo\'riqnomasi',
            'is_active': 'Faol'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Faqat faol kategoriyalarni ko'rsatish
        self.fields['category'].queryset = MealCategory.objects.filter(
            is_active=True
        ).order_by('display_order', 'name')
        self.fields['category'].empty_label = 'Kategoriya tanlang'

    def clean_portions_per_recipe(self):
        portions = self.cleaned_data.get('portions_per_recipe')
        if portions and portions <= 0:
            raise ValidationError('Porsiya soni noldan katta bo\'lishi kerak.')
        return portions

    def clean_preparation_time(self):
        time = self.cleaned_data.get('preparation_time')
        if time and time < 0:
            raise ValidationError('Vaqt manfiy bo\'lishi mumkin emas.')
        return time

    def clean_cooking_time(self):
        time = self.cleaned_data.get('cooking_time')
        if time and time < 0:
            raise ValidationError('Vaqt manfiy bo\'lishi mumkin emas.')
        return time


class RecipeForm(forms.ModelForm):
    """Retsept formi"""

    class Meta:
        model = Recipe
        fields = [
            'meal', 'ingredient', 'quantity_per_portion',
            'is_optional', 'notes', 'display_order'
        ]
        widgets = {
            'meal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ingredient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity_per_portion': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001',
                'placeholder': '0.000'
            }),
            'is_optional': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Qo\'shimcha izohlar'
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            })
        }
        labels = {
            'meal': 'Ovqat',
            'ingredient': 'Ingredient',
            'quantity_per_portion': 'Bir porsiya uchun miqdor',
            'is_optional': 'Ixtiyoriy',
            'notes': 'Izohlar',
            'display_order': 'Ko\'rsatish tartibi'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Faqat faol ovqatlarni ko'rsatish
        self.fields['meal'].queryset = Meal.objects.filter(
            is_active=True
        ).order_by('name')

        # Faqat faol ingredientlarni ko'rsatish
        self.fields['ingredient'].queryset = Ingredient.objects.filter(
            is_active=True
        ).order_by('name')

        self.fields['meal'].empty_label = 'Ovqat tanlang'
        self.fields['ingredient'].empty_label = 'Ingredient tanlang'

    def clean_quantity_per_portion(self):
        quantity = self.cleaned_data.get('quantity_per_portion')
        if quantity and quantity <= 0:
            raise ValidationError('Miqdor noldan katta bo\'lishi kerak.')
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        meal = cleaned_data.get('meal')
        ingredient = cleaned_data.get('ingredient')

        if meal and ingredient:
            # Bir xil ovqat uchun bir xil ingredient tekshiruvi
            qs = Recipe.objects.filter(meal=meal, ingredient=ingredient)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'{meal.name} ovqati uchun {ingredient.name} retsepti allaqachon mavjud.'
                )

        return cleaned_data


class MealNutritionForm(forms.ModelForm):
    """Ovqat ozuqa qiymati formi"""

    class Meta:
        model = MealNutrition
        fields = [
            'calories_per_100g', 'protein_per_100g', 'fat_per_100g',
            'carbs_per_100g', 'fiber_per_100g', 'sugar_per_100g', 'sodium_per_100g'
        ]
        widgets = {
            'calories_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'kcal'
            }),
            'protein_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'gram'
            }),
            'fat_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'gram'
            }),
            'carbs_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'gram'
            }),
            'fiber_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'gram'
            }),
            'sugar_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'gram'
            }),
            'sodium_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'placeholder': 'mg'
            })
        }
        labels = {
            'calories_per_100g': 'Kaloriya (100g)',
            'protein_per_100g': 'Oqsil (100g)',
            'fat_per_100g': 'Yog\' (100g)',
            'carbs_per_100g': 'Uglerod (100g)',
            'fiber_per_100g': 'Tola (100g)',
            'sugar_per_100g': 'Shakar (100g)',
            'sodium_per_100g': 'Natriy (100g)'
        }

    def clean(self):
        cleaned_data = super().clean()

        # Manfiy qiymatlarni tekshirish
        for field_name, value in cleaned_data.items():
            if value is not None and value < 0:
                raise ValidationError(f'{self.fields[field_name].label} manfiy bo\'lishi mumkin emas.')

        return cleaned_data