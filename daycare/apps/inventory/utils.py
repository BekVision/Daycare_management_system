from datetime import datetime, date, timedelta
from django.core.mail import send_mail
from django.db.models import Sum
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import Ingredient, Stock, StockTransaction


def log_inventory_activity(user, action, ingredient=None, request=None, extra_data=None):
    """Inventory faoliyatini qayd qilish"""
    try:
        from apps.common.utils import log_activity

        object_type = 'Ingredient'
        object_id = ingredient.id if ingredient else None
        object_repr = str(ingredient) if ingredient else None

        changes = extra_data or {}

        log_activity(
            user=user,
            action=action,
            object_type=object_type,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes,
            request=request
        )
    except ImportError:
        # Common app mavjud bo'lmasa, log qilmaslik
        pass


def check_low_stock():
    """Kam zaxira mahsulotlarni tekshirish"""
    low_stock_ingredients = []

    for ingredient in Ingredient.objects.filter(is_active=True):
        if ingredient.is_low_stock():
            low_stock_ingredients.append({
                'ingredient': ingredient,
                'current_stock': ingredient.available_quantity(),
                'min_threshold': ingredient.min_threshold,
                'shortage': ingredient.min_threshold - ingredient.available_quantity(),
            })

    return low_stock_ingredients


def check_expiring_items(days=7):
    """Muddati tugayotgan mahsulotlarni tekshirish"""
    today = timezone.now().date()
    expiry_date = today + timedelta(days=days)

    expiring_stocks = Stock.objects.filter(
        expiry_date__lte=expiry_date,
        expiry_date__gte=today,
        current_quantity__gt=0
    ).select_related('ingredient')

    return expiring_stocks


def send_stock_alert(ingredient, alert_type='low_stock'):
    """Stock ogohlantirishi yuborish"""
    try:
        from apps.common.utils import get_setting, send_system_alert

        if alert_type == 'low_stock':
            title = f'Kam zaxira: {ingredient.name}'
            message = f'{ingredient.name} mahsuloti zaxirasi kam ({ingredient.available_quantity()} {ingredient.unit}). Minimal chegara: {ingredient.min_threshold} {ingredient.unit}'
            level = 'warning'
        elif alert_type == 'out_of_stock':
            title = f'Zaxira tugadi: {ingredient.name}'
            message = f'{ingredient.name} mahsuloti zaxirasi tugagan'
            level = 'error'
        elif alert_type == 'expiring':
            title = f'Muddati tugayapti: {ingredient.name}'
            message = f'{ingredient.name} mahsulotining muddati tugayapti'
            level = 'warning'
        else:
            return False

        send_system_alert(title, message, level)
        return True

    except ImportError:
        # Common app mavjud bo'lmasa, email yuborish
        return send_stock_email_alert(ingredient, alert_type)


def send_stock_email_alert(ingredient, alert_type):
    """Email orqali stock ogohlantirishi"""
    try:
        # Admin emaillarni olish
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
        if isinstance(admin_emails, str):
            admin_emails = [email.strip() for email in admin_emails.split(',') if email.strip()]

        if not admin_emails:
            return False

        context = {
            'ingredient': ingredient,
            'alert_type': alert_type,
            'current_stock': ingredient.available_quantity(),
            'min_threshold': ingredient.min_threshold,
            'site_name': getattr(settings, 'SITE_NAME', 'Bog\'cha Tizimi'),
            'timestamp': datetime.now(),
        }

        if alert_type == 'low_stock':
            subject = f'Kam zaxira ogohlantirishi: {ingredient.name}'
            template = 'inventory/emails/low_stock_alert.html'
        elif alert_type == 'out_of_stock':
            subject = f'Zaxira tugadi: {ingredient.name}'
            template = 'inventory/emails/out_of_stock_alert.html'
        elif alert_type == 'expiring':
            subject = f'Muddati tugayapti: {ingredient.name}'
            template = 'inventory/emails/expiring_alert.html'
        else:
            return False

        html_message = render_to_string(template, context)

        send_mail(
            subject=subject,
            message=f'{subject}\n\n{ingredient.name} - {ingredient.available_quantity()} {ingredient.unit}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=True
        )

        return True

    except Exception as e:
        print(f'Stock alert yuborishda xato: {e}')
        return False


def calculate_ingredient_value(ingredient):
    """Ingredient qiymatini hisoblash"""
    try:
        if ingredient.cost_per_unit and ingredient.stock.current_quantity:
            return ingredient.cost_per_unit * ingredient.stock.current_quantity
    except (Stock.DoesNotExist, AttributeError):
        pass
    return 0


def get_inventory_statistics(days=30):
    """Ombor statistikasi"""
    today = timezone.now().date()
    start_date = today - timedelta(days=days)

    stats = {
        'total_ingredients': Ingredient.objects.filter(is_active=True).count(),
        'low_stock_count': 0,
        'out_of_stock_count': 0,
        'total_value': 0,
        'transactions_count': StockTransaction.objects.filter(
            created_at__date__gte=start_date
        ).count(),
        'top_transactions': [],
        'category_breakdown': {},
    }

    # Stock holati
    for ingredient in Ingredient.objects.filter(is_active=True):
        if ingredient.is_out_of_stock():
            stats['out_of_stock_count'] += 1
        elif ingredient.is_low_stock():
            stats['low_stock_count'] += 1

        # Qiymat hisoblash
        stats['total_value'] += calculate_ingredient_value(ingredient)

    # Eng ko'p ishlatilgan ingredientlar
    from django.db.models import Sum
    stats['top_transactions'] = StockTransaction.objects.filter(
        created_at__date__gte=start_date,
        transaction_type='OUT'
    ).values('ingredient__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]

    # Kategoriya bo'yicha breakdown
    from .models import IngredientCategory
    for category in IngredientCategory.objects.filter(is_active=True):
        ingredients = category.ingredients.filter(is_active=True)
        stats['category_breakdown'][category.name] = {
            'ingredient_count': ingredients.count(),
            'low_stock_count': sum(1 for ing in ingredients if ing.is_low_stock()),
            'total_value': sum(calculate_ingredient_value(ing) for ing in ingredients),
        }

    return stats


def generate_restock_suggestions():
    """Qayta to'ldirish tavsiyalari"""
    suggestions = []

    for ingredient in Ingredient.objects.filter(is_active=True):
        if ingredient.is_low_stock() or ingredient.is_out_of_stock():
            # Oxirgi 30 kun davomida o'rtacha istemol
            last_30_days = timezone.now().date() - timedelta(days=30)
            avg_consumption = StockTransaction.objects.filter(
                ingredient=ingredient,
                transaction_type='OUT',
                created_at__date__gte=last_30_days
            ).aggregate(avg_quantity=Sum('quantity'))['avg_quantity'] or 0

            # 30 kunlik ehtiyoj + xavfsizlik zahirasi
            suggested_quantity = max(
                ingredient.min_threshold * 2,  # Minimal x2
                avg_consumption * 1.5,  # O'rtacha + 50%
                ingredient.max_threshold or ingredient.min_threshold * 3
            )

            suggestions.append({
                'ingredient': ingredient,
                'current_stock': ingredient.available_quantity(),
                'suggested_quantity': suggested_quantity,
                'avg_monthly_consumption': avg_consumption,
                'priority': 'high' if ingredient.is_out_of_stock() else 'medium',
            })

    # Prioritet bo'yicha sortlash
    suggestions.sort(key=lambda x: (
        x['priority'] == 'high',  # Out of stock birinchi
        x['current_stock']  # Eng kam zaxira
    ), reverse=True)

    return suggestions


def bulk_update_stock(ingredients, action, quantity, user, notes=None):
    """Ko'p ingredient uchun bulk stock yangilash"""
    results = []

    for ingredient in ingredients:
        try:
            if action == 'restock':
                # Qayta to'ldirish
                transaction = StockTransaction.objects.create(
                    ingredient=ingredient,
                    transaction_type='IN',
                    quantity=quantity,
                    notes=notes or f'Bulk restock - {quantity} {ingredient.unit}',
                    created_by=user
                )
            elif action == 'adjust':
                # Tuzatish
                transaction = StockTransaction.objects.create(
                    ingredient=ingredient,
                    transaction_type='ADJUSTMENT',
                    quantity=quantity,
                    notes=notes or f'Bulk adjustment - {quantity} {ingredient.unit}',
                    created_by=user
                )
            elif action == 'reserve':
                # Rezerv qilish
                stock, created = Stock.objects.get_or_create(
                    ingredient=ingredient,
                    defaults={'last_updated_by': user}
                )
                stock.reserved_quantity += quantity
                stock.last_updated_by = user
                stock.save()

                log_inventory_activity(
                    user=user,
                    action='STOCK_RESERVED',
                    ingredient=ingredient,
                    extra_data={'reserved_quantity': quantity}
                )

                transaction = None

            results.append({
                'ingredient': ingredient,
                'success': True,
                'message': f'{ingredient.name} muvaffaqiyatli yangilandi'
            })

        except Exception as e:
            results.append({
                'ingredient': ingredient,
                'success': False,
                'message': f'{ingredient.name}: {str(e)}'
            })

    return results


def export_inventory_report(format='csv'):
    """Ombor hisobotini eksport qilish"""
    import csv
    from io import StringIO
    from django.http import HttpResponse

    output = StringIO()

    if format == 'csv':
        writer = csv.writer(output)
        writer.writerow([
            'Ingredient', 'Kategoriya', 'Birlik', 'Joriy zaxira',
            'Rezerv', 'Mavjud', 'Min chegara', 'Holat', 'Muddati'
        ])

        for ingredient in Ingredient.objects.filter(is_active=True).select_related('category'):
            try:
                stock = ingredient.stock
                status = 'Tugagan' if ingredient.is_out_of_stock() else 'Kam' if ingredient.is_low_stock() else 'Yetarli'
                expiry = stock.expiry_date.strftime('%d.%m.%Y') if stock.expiry_date else '-'

                writer.writerow([
                    ingredient.name,
                    ingredient.category.name,
                    ingredient.unit,
                    stock.current_quantity,
                    stock.reserved_quantity,
                    stock.available_quantity(),
                    ingredient.min_threshold,
                    status,
                    expiry
                ])
            except Stock.DoesNotExist:
                writer.writerow([
                    ingredient.name,
                    ingredient.category.name,
                    ingredient.unit,
                    0, 0, 0,
                    ingredient.min_threshold,
                    'Zaxira yo\'q',
                    '-'
                ])

    output.seek(0)
    return output.getvalue()


def validate_barcode(barcode, ingredient_id=None):
    """Barcode ni tekshirish"""
    if not barcode:
        return True, None

    # Mavjud barcode tekshirish
    existing = Ingredient.objects.filter(barcode=barcode)
    if ingredient_id:
        existing = existing.exclude(id=ingredient_id)

    if existing.exists():
        return False, f'Bu barcode allaqachon {existing.first().name} da ishlatilgan'

    # Barcode format tekshirish (sodda versiya)
    if not barcode.isdigit() or len(barcode) < 8:
        return False, 'Barcode kamida 8 ta raqamdan iborat bo\'lishi kerak'

    return True, None


def predict_stock_needs(ingredient, days_ahead=30):
    """Stock ehtiyojini bashorat qilish"""
    # So'nggi 90 kunlik istemol tahlili
    last_90_days = timezone.now().date() - timedelta(days=90)

    transactions = StockTransaction.objects.filter(
        ingredient=ingredient,
        transaction_type='OUT',
        created_at__date__gte=last_90_days
    ).order_by('created_at')

    if not transactions.exists():
        return {
            'predicted_consumption': 0,
            'recommended_restock': ingredient.min_threshold,
            'confidence': 'low',
            'trend': 'stable'
        }

    # Haftalik istemol o'rtachasi
    from django.db.models import Sum
    weekly_consumption = []
    current_date = last_90_days

    while current_date <= timezone.now().date():
        week_end = current_date + timedelta(days=7)
        week_total = transactions.filter(
            created_at__date__gte=current_date,
            created_at__date__lt=week_end
        ).aggregate(total=Sum('quantity'))['total'] or 0

        weekly_consumption.append(week_total)
        current_date = week_end

    if not weekly_consumption:
        avg_weekly = 0
        trend = 'stable'
    else:
        avg_weekly = sum(weekly_consumption) / len(weekly_consumption)

        # Trend aniqlash
        if len(weekly_consumption) >= 4:
            recent_avg = sum(weekly_consumption[-4:]) / 4
            older_avg = sum(weekly_consumption[:-4]) / max(len(weekly_consumption) - 4, 1)

            if recent_avg > older_avg * 1.2:
                trend = 'increasing'
            elif recent_avg < older_avg * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

    # Bashorat
    weeks_ahead = days_ahead / 7
    predicted_consumption = avg_weekly * weeks_ahead

    # Trend bo'yicha tuzatish
    if trend == 'increasing':
        predicted_consumption *= 1.3
    elif trend == 'decreasing':
        predicted_consumption *= 0.8

    # Tavsiya
    current_stock = ingredient.available_quantity()
    recommended_restock = max(
        predicted_consumption - current_stock + ingredient.min_threshold,
        0
    )

    confidence = 'high' if len(weekly_consumption) >= 8 else 'medium' if len(weekly_consumption) >= 4 else 'low'

    return {
        'predicted_consumption': predicted_consumption,
        'recommended_restock': recommended_restock,
        'confidence': confidence,
        'trend': trend,
        'current_stock': current_stock,
        'avg_weekly_consumption': avg_weekly
    }