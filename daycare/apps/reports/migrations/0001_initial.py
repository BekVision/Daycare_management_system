# Generated by Django 5.2.1 on 2025-05-29 14:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_date', models.DateField(unique=True)),
                ('total_meals_planned', models.IntegerField(default=0)),
                ('total_meals_served', models.IntegerField(default=0)),
                ('total_portions_planned', models.IntegerField(default=0)),
                ('total_portions_served', models.IntegerField(default=0)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_waste', models.FloatField(default=0)),
                ('efficiency_percentage', models.FloatField(blank=True, null=True)),
                ('waste_percentage', models.FloatField(blank=True, null=True)),
                ('meals_data', models.JSONField(blank=True, null=True)),
                ('ingredients_data', models.JSONField(blank=True, null=True)),
                ('summary', models.JSONField(blank=True, null=True)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('generated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generated_daily_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Kunlik hisobot',
                'verbose_name_plural': 'Kunlik hisobotlar',
                'indexes': [models.Index(fields=['report_date'], name='unique_daily_report_date')],
            },
        ),
        migrations.CreateModel(
            name='IngredientUsageReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_date', models.DateField()),
                ('opening_stock', models.FloatField(default=0)),
                ('stock_in', models.FloatField(default=0)),
                ('stock_used', models.FloatField(default=0)),
                ('stock_waste', models.FloatField(default=0)),
                ('closing_stock', models.FloatField(default=0)),
                ('cost_per_unit', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('total_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('usage_percentage', models.FloatField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usage_reports', to='inventory.ingredient')),
            ],
            options={
                'verbose_name': 'Ingredient ishlatish hisoboti',
                'verbose_name_plural': 'Ingredient ishlatish hisobotlari',
                'indexes': [models.Index(fields=['ingredient', 'report_date'], name='unique_ingredient_usage_date')],
                'constraints': [models.UniqueConstraint(fields=('ingredient', 'report_date'), name='unique_ingredient_report_date')],
            },
        ),
        migrations.CreateModel(
            name='MonthlyReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_month', models.DateField(unique=True)),
                ('total_meals_served', models.IntegerField(default=0)),
                ('total_portions_served', models.IntegerField(default=0)),
                ('total_portions_possible', models.IntegerField(default=0)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_waste', models.FloatField(default=0)),
                ('efficiency_percentage', models.FloatField(blank=True, null=True)),
                ('waste_percentage', models.FloatField(blank=True, null=True)),
                ('cost_per_portion', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('most_popular_meals', models.JSONField(blank=True, null=True)),
                ('least_used_ingredients', models.JSONField(blank=True, null=True)),
                ('cost_breakdown', models.JSONField(blank=True, null=True)),
                ('recommendations', models.TextField(blank=True, null=True)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('generated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='generated_monthly_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Oylik hisobot',
                'verbose_name_plural': 'Oylik hisobotlar',
                'indexes': [models.Index(fields=['report_month'], name='unique_monthly_report')],
            },
        ),
    ]
