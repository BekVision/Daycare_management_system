# reports/models.py
from django.db import models


class DailyReport(models.Model):
    report_date = models.DateField(unique=True)
    total_meals_planned = models.IntegerField(default=0)
    total_meals_served = models.IntegerField(default=0)
    total_portions_planned = models.IntegerField(default=0)
    total_portions_served = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_waste = models.FloatField(default=0)
    efficiency_percentage = models.FloatField(null=True, blank=True)
    waste_percentage = models.FloatField(null=True, blank=True)
    meals_data = models.JSONField(null=True, blank=True)
    ingredients_data = models.JSONField(null=True, blank=True)
    summary = models.JSONField(null=True, blank=True)
    generated_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='generated_daily_reports')
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Kunlik hisobot: {self.report_date}"

    class Meta:
        verbose_name = "Kunlik hisobot"
        verbose_name_plural = "Kunlik hisobotlar"
        ordering = ['-report_date']
        indexes = [
            models.Index(fields=['report_date'], name='idx_daily_report_date'),
        ]


class MonthlyReport(models.Model):
    report_month = models.DateField(unique=True)
    total_meals_served = models.IntegerField(default=0)
    total_portions_served = models.IntegerField(default=0)
    total_portions_possible = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_waste = models.FloatField(default=0)
    efficiency_percentage = models.FloatField(null=True, blank=True)
    waste_percentage = models.FloatField(null=True, blank=True)
    cost_per_portion = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    most_popular_meals = models.JSONField(null=True, blank=True)
    least_used_ingredients = models.JSONField(null=True, blank=True)
    cost_breakdown = models.JSONField(null=True, blank=True)
    recommendations = models.TextField(null=True, blank=True)
    generated_by = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='generated_monthly_reports')
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Oylik hisobot: {self.report_month.strftime('%Y-%m')}"

    class Meta:
        verbose_name = "Oylik hisobot"
        verbose_name_plural = "Oylik hisobotlar"
        ordering = ['-report_month']
        indexes = [
            models.Index(fields=['report_month'], name='idx_monthly_report'),
        ]


class IngredientUsageReport(models.Model):
    ingredient = models.ForeignKey('inventory.Ingredient', on_delete=models.CASCADE, related_name='usage_reports')
    report_date = models.DateField()
    opening_stock = models.FloatField(default=0)
    stock_in = models.FloatField(default=0)
    stock_used = models.FloatField(default=0)
    stock_waste = models.FloatField(default=0)
    closing_stock = models.FloatField(default=0)
    cost_per_unit = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_percentage = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ingredient.name} - {self.report_date}"

    class Meta:
        verbose_name = "Ingredient ishlatish hisoboti"
        verbose_name_plural = "Ingredient ishlatish hisobotlari"
        ordering = ['-report_date', 'ingredient__name']
        indexes = [
            models.Index(fields=['ingredient', 'report_date'], name='idx_ingredient_usage_date'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'report_date'], name='unique_ingredient_report_date')
        ]