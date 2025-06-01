# reports/services.py
from django.db.models import Sum, Avg, Count, Q, F
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import calendar

from .models import DailyReport, MonthlyReport, IngredientUsageReport


class ReportService:
    """Hisobot yaratish va hisoblash servisi"""

    @staticmethod
    def generate_daily_report(report_date: date, generated_by) -> DailyReport:
        """Kunlik hisobot yaratish"""

        # Agar hisobot mavjud bo'lsa, yangilash
        daily_report, created = DailyReport.objects.get_or_create(
            report_date=report_date,
            defaults={'generated_by': generated_by}
        )

        # Ovqatlar ma'lumotlarini olish
        meals_data = ReportService._get_daily_meals_data(report_date)

        # Ingredientlar ma'lumotlarini olish
        ingredients_data = ReportService._get_daily_ingredients_data(report_date)

        # Asosiy hisoblar
        total_meals_planned = meals_data.get('total_planned', 0)
        total_meals_served = meals_data.get('total_served', 0)
        total_portions_planned = meals_data.get('portions_planned', 0)
        total_portions_served = meals_data.get('portions_served', 0)
        total_cost = meals_data.get('total_cost', Decimal('0'))
        total_waste = ingredients_data.get('total_waste', 0)

        # Samaradorlik hisobi
        efficiency_percentage = None
        if total_portions_planned > 0:
            efficiency_percentage = (total_portions_served / total_portions_planned) * 100

        # Chiqindi foizi
        waste_percentage = None
        total_used = ingredients_data.get('total_used', 0)
        if total_used > 0:
            waste_percentage = (total_waste / total_used) * 100

        # Xulosa yaratish
        summary = ReportService._generate_daily_summary(
            total_meals_served, total_portions_served, efficiency_percentage,
            waste_percentage, total_cost
        )

        # Hisobotni yangilash
        daily_report.total_meals_planned = total_meals_planned
        daily_report.total_meals_served = total_meals_served
        daily_report.total_portions_planned = total_portions_planned
        daily_report.total_portions_served = total_portions_served
        daily_report.total_cost = total_cost
        daily_report.total_waste = total_waste
        daily_report.efficiency_percentage = efficiency_percentage
        daily_report.waste_percentage = waste_percentage
        daily_report.meals_data = meals_data
        daily_report.ingredients_data = ingredients_data
        daily_report.summary = summary
        daily_report.generated_by = generated_by
        daily_report.save()

        return daily_report

    @staticmethod
    def generate_monthly_report(year: int, month: int, generated_by) -> MonthlyReport:
        """Oylik hisobot yaratish"""

        report_month = date(year, month, 1)

        # Agar hisobot mavjud bo'lsa, yangilash
        monthly_report, created = MonthlyReport.objects.get_or_create(
            report_month=report_month,
            defaults={'generated_by': generated_by}
        )

        # Oy boshidan oxirigacha sanalar
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        # Kunlik hisobotlardan ma'lumot olish
        daily_reports = DailyReport.objects.filter(
            report_date__range=[start_date, end_date]
        )

        # Asosiy hisoblar
        total_meals_served = daily_reports.aggregate(
            total=Sum('total_meals_served')
        )['total'] or 0

        total_portions_served = daily_reports.aggregate(
            total=Sum('total_portions_served')
        )['total'] or 0

        total_portions_possible = daily_reports.aggregate(
            total=Sum('total_portions_planned')
        )['total'] or 0

        total_cost = daily_reports.aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0')

        total_waste = daily_reports.aggregate(
            total=Sum('total_waste')
        )['total'] or 0

        # Samaradorlik hisobi
        efficiency_percentage = None
        if total_portions_possible > 0:
            efficiency_percentage = (total_portions_served / total_portions_possible) * 100

        # Chiqindi foizi
        waste_percentage = None
        if total_portions_served > 0:
            waste_percentage = (total_waste / total_portions_served) * 100

        # Porsiya uchun narx
        cost_per_portion = None
        if total_portions_served > 0:
            cost_per_portion = total_cost / total_portions_served

        # Eng mashhur ovqatlar
        most_popular_meals = ReportService._get_most_popular_meals(start_date, end_date)

        # Eng kam ishlatilgan ingredientlar
        least_used_ingredients = ReportService._get_least_used_ingredients(start_date, end_date)

        # Xarajat taqsimoti
        cost_breakdown = ReportService._get_cost_breakdown(start_date, end_date)

        # Tavsiyalar
        recommendations = ReportService._generate_monthly_recommendations(
            efficiency_percentage, waste_percentage, most_popular_meals, least_used_ingredients
        )

        # Hisobotni yangilash
        monthly_report.total_meals_served = total_meals_served
        monthly_report.total_portions_served = total_portions_served
        monthly_report.total_portions_possible = total_portions_possible
        monthly_report.total_cost = total_cost
        monthly_report.total_waste = total_waste
        monthly_report.efficiency_percentage = efficiency_percentage
        monthly_report.waste_percentage = waste_percentage
        monthly_report.cost_per_portion = cost_per_portion
        monthly_report.most_popular_meals = most_popular_meals
        monthly_report.least_used_ingredients = least_used_ingredients
        monthly_report.cost_breakdown = cost_breakdown
        monthly_report.recommendations = recommendations
        monthly_report.generated_by = generated_by
        monthly_report.save()

        return monthly_report

    @staticmethod
    def generate_ingredient_usage_reports(report_date: date) -> List[IngredientUsageReport]:
        """Ingredient ishlatish hisobotlarini yaratish"""

        # Bu yerda inventory app'dan ma'lumotlar kerak bo'ladi
        # Hozircha mock data bilan ishlaymiz

        reports = []
        # Bu qism inventory app bilan integratsiya qilinganda to'ldiriladi

        return reports

    @staticmethod
    def _get_daily_meals_data(report_date: date) -> Dict[str, Any]:
        """Kunlik ovqatlar ma'lumotlari"""

        # Bu yerda meals app'dan ma'lumotlar kerak
        # Hozircha mock data
        return {
            'total_planned': 0,
            'total_served': 0,
            'portions_planned': 0,
            'portions_served': 0,
            'total_cost': Decimal('0'),
            'meals': []
        }

    @staticmethod
    def _get_daily_ingredients_data(report_date: date) -> Dict[str, Any]:
        """Kunlik ingredientlar ma'lumotlari"""

        # Bu yerda inventory app'dan ma'lumotlar kerak
        # Hozircha mock data
        return {
            'total_used': 0,
            'total_waste': 0,
            'ingredients': []
        }

    @staticmethod
    def _generate_daily_summary(
            total_meals: int, total_portions: int, efficiency: Optional[float],
            waste: Optional[float], total_cost: Decimal
    ) -> Dict[str, Any]:
        """Kunlik xulosa yaratish"""

        summary = {
            'performance': 'normal',
            'waste_status': 'normal',
            'cost_status': 'normal',
            'recommendations': []
        }

        # Samaradorlik tahlili
        if efficiency:
            if efficiency >= 90:
                summary['performance'] = 'excellent'
            elif efficiency >= 75:
                summary['performance'] = 'good'
            elif efficiency < 60:
                summary['performance'] = 'poor'
                summary['recommendations'].append('Porsiya rejalashtirish yaxshilanishi kerak')

        # Chiqindi tahlili
        if waste:
            if waste < 3:
                summary['waste_status'] = 'excellent'
            elif waste < 7:
                summary['waste_status'] = 'good'
            elif waste >= 15:
                summary['waste_status'] = 'poor'
                summary['recommendations'].append('Chiqindilarni kamaytirish choralari ko\'rish kerak')

        return summary

    @staticmethod
    def _get_most_popular_meals(start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Eng mashhur ovqatlar"""

        # Bu yerda meals app'dan ma'lumotlar kerak
        return []

    @staticmethod
    def _get_least_used_ingredients(start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Eng kam ishlatilgan ingredientlar"""

        # Bu yerda inventory app'dan ma'lumotlar kerak
        return []

    @staticmethod
    def _get_cost_breakdown(start_date: date, end_date: date) -> Dict[str, Any]:
        """Xarajat taqsimoti"""

        # Bu yerda inventory app'dan ma'lumotlar kerak
        return {
            'by_category': [],
            'by_meal': [],
            'total': 0
        }

    @staticmethod
    def _generate_monthly_recommendations(
            efficiency: Optional[float], waste: Optional[float],
            popular_meals: List, unused_ingredients: List
    ) -> str:
        """Oylik tavsiyalar yaratish"""

        recommendations = []

        if efficiency and efficiency < 70:
            recommendations.append("Porsiya rejalashtirish jarayonini yaxshilash kerak.")

        if waste and waste > 10:
            recommendations.append("Chiqindilarni kamaytirish uchun maxsus dastur ishlab chiqish kerak.")

        if len(unused_ingredients) > 5:
            recommendations.append("Kam ishlatilgan ingredientlar ro'yxatini ko'rib chiqing.")

        if not recommendations:
            recommendations.append("Barcha ko'rsatkichlar me'yoriy darajada.")

        return " ".join(recommendations)


class ReportAnalyticsService:
    """Hisobot tahlil servisi"""

    @staticmethod
    def get_dashboard_data(days: int = 30) -> Dict[str, Any]:
        """Dashboard uchun ma'lumotlar"""

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        daily_reports = DailyReport.objects.filter(
            report_date__range=[start_date, end_date]
        )

        return {
            'total_reports': daily_reports.count(),
            'avg_efficiency': daily_reports.aggregate(
                avg=Avg('efficiency_percentage')
            )['avg'] or 0,
            'avg_waste': daily_reports.aggregate(
                avg=Avg('waste_percentage')
            )['avg'] or 0,
            'total_cost': daily_reports.aggregate(
                total=Sum('total_cost')
            )['total'] or Decimal('0'),
            'trend_data': ReportAnalyticsService._get_trend_data(daily_reports)
        }

    @staticmethod
    def _get_trend_data(daily_reports) -> Dict[str, List]:
        """Trend ma'lumotlari"""

        dates = []
        efficiency = []
        waste = []
        costs = []

        for report in daily_reports.order_by('report_date'):
            dates.append(report.report_date.strftime('%d.%m'))
            efficiency.append(report.efficiency_percentage or 0)
            waste.append(report.waste_percentage or 0)
            costs.append(float(report.total_cost))

        return {
            'dates': dates,
            'efficiency': efficiency,
            'waste': waste,
            'costs': costs
        }