from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import date, time
from decimal import Decimal

from .models import MealService, ServiceLog, ServiceFeedback
from .utils import (
    calculate_possible_portions_for_meal,
    check_ingredient_availability,
    get_daily_service_stats
)
from apps.accounts.models import Role
from apps.meals.models import Meal, MealCategory, Recipe
from apps.inventory.models import Ingredient, IngredientCategory, Stock

User = get_user_model()


class MealServiceModelTest(TestCase):
    def setUp(self):
        # Role yaratish
        self.admin_role = Role.objects.create(name='admin', description='Admin role')
        self.chef_role = Role.objects.create(name='chef', description='Chef role')

        # Foydalanuvchilar yaratish
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=self.admin_role
        )

        self.chef_user = User.objects.create_user(
            username='chef',
            email='chef@test.com',
            password='testpass123',
            role=self.chef_role
        )

        # Kategoriyalar yaratish
        self.ingredient_category = IngredientCategory.objects.create(name='Test Category')
        self.meal_category = MealCategory.objects.create(name='Test Meals')

        # Ingredientlar yaratish
        self.ingredient1 = Ingredient.objects.create(
            name='Go\'sht',
            unit='kg',
            category=self.ingredient_category,
            min_threshold=5.0,
            cost_per_unit=Decimal('50000.00'),
            created_by=self.admin_user
        )

        self.ingredient2 = Ingredient.objects.create(
            name='Kartoshka',
            unit='kg',
            category=self.ingredient_category,
            min_threshold=10.0,
            cost_per_unit=Decimal('5000.00'),
            created_by=self.admin_user
        )

        # Stock yaratish
        self.stock1 = Stock.objects.create(
            ingredient=self.ingredient1,
            current_quantity=20.0,
            last_updated_by=self.admin_user
        )

        self.stock2 = Stock.objects.create(
            ingredient=self.ingredient2,
            current_quantity=50.0,
            last_updated_by=self.admin_user
        )

        # Ovqat yaratish
        self.meal = Meal.objects.create(
            name='Test Osh',
            category=self.meal_category,
            portions_per_recipe=4,
            created_by=self.admin_user
        )

        # Retsept yaratish
        self.recipe1 = Recipe.objects.create(
            meal=self.meal,
            ingredient=self.ingredient1,
            quantity_per_portion=0.2  # 200g go'sht har bir porsiya uchun
        )

        self.recipe2 = Recipe.objects.create(
            meal=self.meal,
            ingredient=self.ingredient2,
            quantity_per_portion=0.3  # 300g kartoshka har bir porsiya uchun
        )

    def test_meal_service_creation(self):
        """MealService yaratishni test qilish"""
        meal_service = MealService.objects.create(
            meal=self.meal,
            portions_planned=10,
            portions_served=0,
            service_date=date.today(),
            service_time=time(12, 0),
            meal_type='LUNCH',
            served_by=self.chef_user,
            created_by=self.chef_user
        )

        self.assertEqual(meal_service.meal, self.meal)
        self.assertEqual(meal_service.portions_planned, 10)
        self.assertEqual(meal_service.status, 'PLANNED')
        self.assertEqual(str(meal_service), f"{self.meal.name} - Tushlik ({date.today()})")

    def test_meal_service_validation(self):
        """MealService validatsiyani test qilish"""
        meal_service = MealService(
            meal=self.meal,
            portions_planned=-5,  # Noto'g'ri qiymat
            portions_served=0,
            service_date=date.today(),
            service_time=time(12, 0),
            meal_type='LUNCH',
            served_by=self.chef_user,
            created_by=self.chef_user
        )

        with self.assertRaises(Exception):
            meal_service.clean()

    def test_service_log_creation(self):
        """ServiceLog yaratishni test qilish"""
        meal_service = MealService.objects.create(
            meal=self.meal,
            portions_planned=10,
            portions_served=10,
            service_date=date.today(),
            service_time=time(12, 0),
            meal_type='LUNCH',
            status='SERVED',
            served_by=self.chef_user,
            created_by=self.chef_user
        )

        service_log = ServiceLog.objects.create(
            meal_service=meal_service,
            ingredient=self.ingredient1,
            quantity_planned=2.0,
            quantity_used=1.8,
            stock_before=20.0,
            stock_after=18.2,
            unit_cost=Decimal('50000.00'),
            total_cost=Decimal('90000.00')
        )

        self.assertEqual(service_log.meal_service, meal_service)
        self.assertEqual(service_log.ingredient, self.ingredient1)
        self.assertEqual(service_log.quantity_used, 1.8)

    def test_service_feedback_creation(self):
        """ServiceFeedback yaratishni test qilish"""
        meal_service = MealService.objects.create(
            meal=self.meal,
            portions_planned=10,
            portions_served=10,
            service_date=date.today(),
            service_time=time(12, 0),
            meal_type='LUNCH',
            status='SERVED',
            served_by=self.chef_user,
            created_by=self.chef_user
        )

        feedback = ServiceFeedback.objects.create(
            meal_service=meal_service,
            feedback_by=self.admin_user,
            taste_rating=5,
            portion_rating=4,
            overall_rating=5,
            comments='Juda mazali edi!'
        )

        self.assertEqual(feedback.meal_service, meal_service)
        self.assertEqual(feedback.taste_rating, 5)
        self.assertEqual(feedback.overall_rating, 5)


class MealServiceUtilsTest(TestCase):
    def setUp(self):
        # ModelTest dagi setUp ni qayta ishlatish
        super().setUp()

        # Role yaratish
        self.admin_role = Role.objects.create(name='admin')
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=self.admin_role
        )

        # Kategoriyalar
        self.ingredient_category = IngredientCategory.objects.create(name='Test Category')
        self.meal_category = MealCategory.objects.create(name='Test Meals')

        # Ingredientlar
        self.ingredient1 = Ingredient.objects.create(
            name='Go\'sht',
            unit='kg',
            category=self.ingredient_category,
            created_by=self.admin_user
        )

        self.stock1 = Stock.objects.create(
            ingredient=self.ingredient1,
            current_quantity=10.0,
            last_updated_by=self.admin_user
        )

        # Ovqat
        self.meal = Meal.objects.create(
            name='Test Osh',
            category=self.meal_category,
            created_by=self.admin_user
        )

        # Retsept
        self.recipe1 = Recipe.objects.create(
            meal=self.meal,
            ingredient=self.ingredient1,
            quantity_per_portion=0.5  # 500g har bir porsiya uchun
        )

    def test_calculate_possible_portions(self):
        """Mumkin bo'lgan porsiyalarni hisoblashni test qilish"""
        possible_portions = calculate_possible_portions_for_meal(self.meal)
        # 10kg / 0.5kg = 20 porsiya
        self.assertEqual(possible_portions, 20)

    def test_check_ingredient_availability(self):
        """Ingredient mavjudligini tekshirish"""
        result = check_ingredient_availability(self.meal, portions=15)

        self.assertTrue(result['all_available'])
        self.assertEqual(len(result['ingredients']), 1)

        ingredient_status = result['ingredients'][0]
        self.assertEqual(ingredient_status['required'], 7.5)  # 15 * 0.5
        self.assertEqual(ingredient_status['available'], 10.0)
        self.assertTrue(ingredient_status['is_sufficient'])

    def test_check_ingredient_availability_insufficient(self):
        """Yetarli bo'lmagan ingredient holatini test qilish"""
        result = check_ingredient_availability(self.meal, portions=25)

        self.assertFalse(result['all_available'])

        ingredient_status = result['ingredients'][0]
        self.assertEqual(ingredient_status['required'], 12.5)  # 25 * 0.5
        self.assertEqual(ingredient_status['available'], 10.0)
        self.assertFalse(ingredient_status['is_sufficient'])

    def test_daily_service_stats(self):
        """Kunlik statistikani test qilish"""
        # Xizmat yaratish
        MealService.objects.create(
            meal=self.meal,
            portions_planned=20,
            portions_served=18,
            service_date=date.today(),
            service_time=time(12, 0),
            meal_type='LUNCH',
            status='SERVED',
            served_by=self.admin_user,
            created_by=self.admin_user
        )

        stats = get_daily_service_stats(date.today())

        self.assertEqual(stats['total_services'], 1)
        self.assertEqual(stats['total_planned'], 20)
        self.assertEqual(stats['total_served'], 18)
        self.assertEqual(stats['efficiency'], 90.0)


class MealServiceViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Role va userlar
        self.admin_role = Role.objects.create(name='admin')
        self.chef_role = Role.objects.create(name='chef')

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=self.admin_role
        )

        self.chef_user = User.objects.create_user(
            username='chef',
            email='chef@test.com',
            password='testpass123',
            role=self.chef_role
        )

        # Kategoriyalar
        self.meal_category = MealCategory.objects.create(name='Test Meals')

        # Ovqat
        self.meal = Meal.objects.create(
            name='Test Osh',
            category=self.meal_category,
            created_by=self.admin_user
        )

    def test_service_list_view(self):
        """Xizmatlar ro'yxati sahifasini test qilish"""
        self.client.login(username='admin', password='testpass123')

        response = self.client.get(reverse('meal_service:service_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ovqat Xizmatlari')

    def test_service_create_view_chef_access(self):
        """Chef rolida xizmat yaratish sahifasiga kirish"""
        self.client.login(username='chef', password='testpass123')

        response = self.client.get(reverse('meal_service:service_create'))
        self.assertEqual(response.status_code, 200)

    def test_service_create_post(self):
        """Xizmat yaratish POST so'rovini test qilish"""
        self.client.login(username='chef', password='testpass123')

        data = {
            'meal': self.meal.id,
            'portions_planned': 10,
            'service_date': date.today(),
            'service_time': '12:00',
            'meal_type': 'LUNCH',
            'notes': 'Test notes'
        }

        response = self.client.post(reverse('meal_service:service_create'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Xizmat yaratilganligini tekshirish
        self.assertTrue(MealService.objects.filter(meal=self.meal).exists())

    def test_service_detail_view(self):
        """Xizmat tafsilotlari sahifasini test qilish"""
        meal_service = MealService.objects.create(
            meal=self.meal,
            portions_planned=10,
            portions_served=8,
            service_date=date.today(),
            service_time=time(12, 0),
            meal_type='LUNCH',
            served_by=self.chef_user,
            created_by=self.chef_user
        )

        self.client.login(username='admin', password='testpass123')

        response = self.client.get(
            reverse('meal_service:service_detail', kwargs={'pk': meal_service.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, meal_service.meal.name)

    def test_unauthorized_access(self):
        """Ruxsatsiz kirishni test qilish"""
        response = self.client.get(reverse('meal_service:service_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class MealServiceIntegrationTest(TestCase):
    """To'liq integratsiya testlari"""

    def setUp(self):
        # To'liq test muhitini yaratish
        self.admin_role = Role.objects.create(name='admin')
        self.chef_role = Role.objects.create(name='chef')

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=self.admin_role
        )

        self.chef_user = User.objects.create_user(
            username='chef',
            email='chef@test.com',
            password='testpass123',
            role=self.chef_role
        )

        # Kategoriyalar
        self.ingredient_category = IngredientCategory.objects.create(name='Main')
        self.meal_category = MealCategory.objects.create(name='Main Dishes')

        # Ingredientlar
        self.ingredient = Ingredient.objects.create(
            name='Rice',
            unit='kg',
            category=self.ingredient_category,
            cost_per_unit=Decimal('8000.00'),
            created_by=self.admin_user
        )

        self.stock = Stock.objects.create(
            ingredient=self.ingredient,
            current_quantity=50.0,
            last_updated_by=self.admin_user
        )

        # Ovqat va retsept
        self.meal = Meal.objects.create(
            name='Osh',
            category=self.meal_category,
            created_by=self.admin_user
        )

        self.recipe = Recipe.objects.create(
            meal=self.meal,
            ingredient=self.ingredient,
            quantity_per_portion=0.2
        )

    def test_complete_meal_service_workflow(self):
        """To'liq ovqat xizmati jarayonini test qilish"""
        self.client.login(username='chef', password='testpass123')

        # 1. Xizmat yaratish
        data = {
            'meal': self.meal.id,
            'portions_planned': 20,
            'service_date': date.today(),
            'service_time': '12:00',
            'meal_type': 'LUNCH'
        }

        response = self.client.post(reverse('meal_service:service_create'), data)
        self.assertEqual(response.status_code, 302)

        meal_service = MealService.objects.get(meal=self.meal)
        self.assertEqual(meal_service.status, 'PLANNED')

        # 2. Ovqat berish
        serve_url = reverse('meal_service:serve_meal', kwargs={'pk': meal_service.pk})
        response = self.client.post(serve_url)

        # Response JSON formatda bo'lishi kerak
        self.assertEqual(response.status_code, 200)

        # Xizmat holatini tekshirish
        meal_service.refresh_from_db()
        self.assertEqual(meal_service.status, 'SERVED')
        self.assertEqual(meal_service.portions_served, 20)

        # Stock yangilanganligini tekshirish
        self.stock.refresh_from_db()
        expected_stock = 50.0 - (20 * 0.2)  # 50 - 4 = 46
        self.assertEqual(self.stock.current_quantity, expected_stock)

        # ServiceLog yaratilganligini tekshirish
        self.assertTrue(
            ServiceLog.objects.filter(
                meal_service=meal_service,
                ingredient=self.ingredient
            ).exists()
        )