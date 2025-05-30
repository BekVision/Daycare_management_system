from django.db import models


class MealCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ovqat kategoriyasi"
        verbose_name_plural = "Ovqat kategoriyalari"
        ordering = ['display_order', 'name']


class Meal(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(MealCategory, on_delete=models.CASCADE, related_name='meals')
    description = models.TextField(null=True, blank=True)
    preparation_time = models.IntegerField(null=True, blank=True)
    cooking_time = models.IntegerField(null=True, blank=True)
    difficulty_level = models.IntegerField(default=1)
    portions_per_recipe = models.IntegerField(default=1)
    calories_per_portion = models.FloatField(null=True, blank=True)
    photo = models.ImageField(upload_to='meals/', null=True, blank=True)
    instructions = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='created_meals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ovqat"
        verbose_name_plural = "Ovqatlar"


class Recipe(models.Model):
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='recipe_items')
    ingredient = models.ForeignKey('inventory.Ingredient', on_delete=models.CASCADE, related_name='used_in_recipes')
    quantity_per_portion = models.FloatField()
    is_optional = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.meal.name}: {self.ingredient.name} ({self.quantity_per_portion} {self.ingredient.unit})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity_per_portion <= 0:
            raise ValidationError("Miqdor noldan katta bo'lishi kerak")

    class Meta:
        verbose_name = "Retsept qismi"
        verbose_name_plural = "Retsept qismlari"
        unique_together = ('meal', 'ingredient')
        indexes = [
            models.Index(fields=['meal', 'ingredient'], name='idx_recipe_meal_ingredient'),
        ]
        ordering = ['meal', 'display_order']


class MealNutrition(models.Model):
    meal = models.OneToOneField(Meal, on_delete=models.CASCADE, related_name='nutrition')
    calories_per_100g = models.FloatField(null=True, blank=True)
    protein_per_100g = models.FloatField(null=True, blank=True)
    fat_per_100g = models.FloatField(null=True, blank=True)
    carbs_per_100g = models.FloatField(null=True, blank=True)
    fiber_per_100g = models.FloatField(null=True, blank=True)
    sugar_per_100g = models.FloatField(null=True, blank=True)
    sodium_per_100g = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.meal.name} ozuqa qiymati"

    class Meta:
        verbose_name = "Ovqat ozuqa qiymati"
        verbose_name_plural = "Ovqat ozuqa qiymatlari"