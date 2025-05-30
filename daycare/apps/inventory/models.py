from django.db import models

class IngredientCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ingredient kategoriyasi"
        verbose_name_plural = "Ingredient kategoriyalari"
        ordering = ['display_order', 'name']


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20)
    category = models.ForeignKey(IngredientCategory, on_delete=models.CASCADE, related_name='ingredients')
    min_threshold = models.FloatField(default=0)
    max_threshold = models.FloatField(null=True, blank=True)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='created_ingredients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.unit})"

    class Meta:
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredientlar"


class Stock(models.Model):
    ingredient = models.OneToOneField(Ingredient, on_delete=models.CASCADE, related_name='stock')
    current_quantity = models.FloatField(default=0)
    reserved_quantity = models.FloatField(default=0)
    last_restock_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    last_updated_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='updated_stocks')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ingredient.name} zaxirasi: {self.current_quantity} {self.ingredient.unit}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.current_quantity < 0:
            raise ValidationError("Joriy miqdor noldan past bo'lishi mumkin emas")
        if self.reserved_quantity < 0:
            raise ValidationError("Zaxira miqdor noldan past bo'lishi mumkin emas")

    class Meta:
        verbose_name = "Zaxira"
        verbose_name_plural = "Zaxiralar"


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Kirim'),
        ('OUT', 'Chiqim'),
        ('ADJUSTMENT', 'Tartibga solish'),
        ('WASTE', 'Chiqindi'),
        ('TRANSFER', "Ko'chirish"),
    ]

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.FloatField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference_type = models.CharField(max_length=50, null=True, blank=True)
    reference_id = models.CharField(max_length=100, null=True, blank=True)
    supplier = models.CharField(max_length=200, null=True, blank=True)
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='stock_transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.ingredient.name}: {self.quantity} {self.ingredient.unit}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity <= 0:
            raise ValidationError("Miqdor noldan katta bo'lishi kerak")

    class Meta:
        verbose_name = "Zaxira tranzaksiyasi"
        verbose_name_plural = "Zaxira tranzaksiyalari"
        indexes = [
            models.Index(fields=['created_at'], name='idx_txn_created'),
            models.Index(fields=['ingredient', 'created_at'], name='idx_txn_ing_date'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['reference_type', 'reference_id'],
                name='unique_transaction_ref',
                condition=models.Q(reference_type__isnull=False)
            )
        ]