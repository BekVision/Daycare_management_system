from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Role, UserProfile
from .utils import (
    generate_secure_password, create_user_with_role,
    has_permission, validate_user_data, get_users_by_role
)
from .forms import CustomUserCreationForm, UserProfileForm

User = get_user_model()


class RoleModelTest(TestCase):
    """Role modeli uchun testlar"""

    def setUp(self):
        self.role_data = {
            'name': 'admin',
            'description': 'Administrator role',
            'permissions': ['view_all_users', 'create_user', 'edit_user']
        }

    def test_role_creation(self):
        """Role yaratish testi"""
        role = Role.objects.create(**self.role_data)
        self.assertEqual(role.name, 'admin')
        self.assertEqual(role.description, 'Administrator role')
        self.assertEqual(len(role.permissions), 3)

    def test_role_str_method(self):
        """Role __str__ metodi testi"""
        role = Role.objects.create(**self.role_data)
        self.assertEqual(str(role), 'Admin')

    def test_role_unique_name(self):
        """Role nomi noyobligini tekshirish"""
        Role.objects.create(**self.role_data)
        with self.assertRaises(Exception):
            Role.objects.create(**self.role_data)


class CustomUserModelTest(TestCase):
    """CustomUser modeli uchun testlar"""

    def setUp(self):
        self.role = Role.objects.create(
            name='manager',
            description='Manager role',
            permissions=['manage_inventory', 'view_reports']
        )

        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': self.role,
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_user_creation(self):
        """Foydalanuvchi yaratish testi"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.role, self.role)
        self.assertTrue(user.check_password('testpass123'))

    def test_user_str_method(self):
        """User __str__ metodi testi"""
        user = User.objects.create_user(**self.user_data)
        expected = f"testuser (Test User)"
        self.assertEqual(str(user), expected)

    def test_get_full_name(self):
        """get_full_name metodi testi"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), "Test User")

        # Ism va familiya bo'lmagan holat
        user.first_name = ""
        user.last_name = ""
        user.save()
        self.assertEqual(user.get_full_name(), "testuser")

    def test_role_methods(self):
        """Role tekshirish metodlari testi"""
        admin_role = Role.objects.create(name='admin')
        chef_role = Role.objects.create(name='chef')

        admin_user = User.objects.create_user(
            username='admin', email='admin@test.com',
            password='pass', role=admin_role
        )
        chef_user = User.objects.create_user(
            username='chef', email='chef@test.com',
            password='pass', role=chef_role
        )
        manager_user = User.objects.create_user(**self.user_data)

        self.assertTrue(admin_user.is_admin())
        self.assertFalse(admin_user.is_chef())
        self.assertFalse(admin_user.is_manager())

        self.assertTrue(chef_user.is_chef())
        self.assertFalse(chef_user.is_admin())

        self.assertTrue(manager_user.is_manager())
        self.assertFalse(manager_user.is_admin())

    def test_has_permission(self):
        """has_permission metodi testi"""
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.has_permission('manage_inventory'))
        self.assertTrue(user.has_permission('view_reports'))
        self.assertFalse(user.has_permission('create_user'))


class UserProfileModelTest(TestCase):
    """UserProfile modeli uchun testlar"""

    def setUp(self):
        self.role = Role.objects.create(name='chef')
        self.user = User.objects.create_user(
            username='chefuser',
            email='chef@test.com',
            password='pass123',
            role=self.role
        )

    def test_profile_auto_creation(self):
        """Profil avtomatik yaratilishini tekshirish"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_profile_str_method(self):
        """Profile __str__ metodi testi"""
        expected = f"{self.user.username} profili"
        self.assertEqual(str(self.user.profile), expected)


class UtilsTest(TestCase):
    """Utils funksiyalari uchun testlar"""

    def setUp(self):
        self.admin_role = Role.objects.create(
            name='admin',
            permissions=['view_all_users', 'create_user']
        )
        self.chef_role = Role.objects.create(
            name='chef',
            permissions=['serve_meals']
        )

    def test_generate_secure_password(self):
        """Xavfsiz parol yaratish testi"""
        password = generate_secure_password()
        self.assertEqual(len(password), 12)

        # Har xil turdagi belgilar mavjudligini tekshirish
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*" for c in password)

        self.assertTrue(has_lower)
        self.assertTrue(has_upper)
        self.assertTrue(has_digit)
        self.assertTrue(has_special)

    def test_create_user_with_role(self):
        """Rol bilan foydalanuvchi yaratish testi"""
        user = create_user_with_role(
            username='newuser',
            email='new@test.com',
            role_name='admin',
            first_name='New',
            last_name='User'
        )

        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.role, self.admin_role)
        self.assertEqual(user.first_name, 'New')

    def test_create_user_with_invalid_role(self):
        """Noto'g'ri rol bilan foydalanuvchi yaratish testi"""
        with self.assertRaises(ValueError):
            create_user_with_role(
                username='newuser',
                email='new@test.com',
                role_name='invalid_role'
            )

    def test_has_permission_function(self):
        """has_permission funksiyasi testi"""
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='pass',
            role=self.admin_role
        )
        chef_user = User.objects.create_user(
            username='chef',
            email='chef@test.com',
            password='pass',
            role=self.chef_role
        )

        self.assertTrue(has_permission(admin_user, 'create_user'))
        self.assertFalse(has_permission(chef_user, 'create_user'))
        self.assertTrue(has_permission(chef_user, 'serve_meals'))

    def test_get_users_by_role(self):
        """Rol bo'yicha foydalanuvchilarni olish testi"""
        User.objects.create_user(
            username='admin1', email='admin1@test.com',
            password='pass', role=self.admin_role
        )
        User.objects.create_user(
            username='admin2', email='admin2@test.com',
            password='pass', role=self.admin_role
        )
        User.objects.create_user(
            username='chef1', email='chef1@test.com',
            password='pass', role=self.chef_role
        )

        admin_users = get_users_by_role('admin')
        chef_users = get_users_by_role('chef')

        self.assertEqual(len(admin_users), 2)
        self.assertEqual(len(chef_users), 1)

    def test_validate_user_data(self):
        """Foydalanuvchi ma'lumotlarini validatsiya qilish testi"""
        valid_data = {
            'username': 'validuser',
            'email': 'valid@test.com',
            'role': self.admin_role.id
        }

        errors = validate_user_data(valid_data)
        self.assertEqual(len(errors), 0)

        # Noto'g'ri ma'lumotlar
        invalid_data = {
            'username': '',
            'email': 'invalid-email',
            'role': None
        }

        errors = validate_user_data(invalid_data)
        self.assertIn('username', errors)
        self.assertIn('role', errors)


class FormsTest(TestCase):
    """Forms uchun testlar"""

    def setUp(self):
        self.role = Role.objects.create(name='manager')

    def test_custom_user_creation_form_valid(self):
        """To'g'ri foydalanuvchi yaratish formi testi"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'complexpass123',
            'password2': 'complexpass123',
            'role': self.role.id
        }

        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_invalid(self):
        """Noto'g'ri foydalanuvchi yaratish formi testi"""
        form_data = {
            'username': '',
            'email': 'invalid-email',
            'password1': 'pass',
            'password2': 'different',
            'role': ''
        }

        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('role', form.errors)

    def test_user_profile_form(self):
        """Foydalanuvchi profil formi testi"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='pass',
            role=self.role
        )

        form_data = {
            'phone_number': '+998901234567',
            'address': 'Test address',
            'birth_date': '1990-01-01',
            'shift_start': '09:00',
            'shift_end': '18:00'
        }

        form = UserProfileForm(data=form_data, instance=user.profile)
        self.assertTrue(form.is_valid())


class ViewsTest(TestCase):
    """Views uchun testlar"""

    def setUp(self):
        self.client = Client()
        self.admin_role = Role.objects.create(
            name='admin',
            permissions=['view_all_users', 'create_user']
        )
        self.chef_role = Role.objects.create(name='chef')

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            role=self.admin_role
        )

        self.chef_user = User.objects.create_user(
            username='chef',
            email='chef@test.com',
            password='chefpass123',
            role=self.chef_role
        )

    def test_login_view_get(self):
        """Login sahifasini ochish testi"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Foydalanuvchi nomi')

    def test_login_view_post_valid(self):
        """To'g'ri ma'lumotlar bilan kirish testi"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'adminpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_login_view_post_invalid(self):
        """Noto'g'ri ma'lumotlar bilan kirish testi"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Noto\'g\'ri foydalanuvchi nomi yoki parol')

    def test_dashboard_view_admin(self):
        """Admin dashboard testi"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Xush kelibsiz, admin!')

    def test_dashboard_view_chef(self):
        """Chef dashboard testi"""
        self.client.login(username='chef', password='chefpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Xush kelibsiz, chef!')

    def test_profile_view(self):
        """Profil sahifasi testi"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin')

    def test_user_list_view_admin(self):
        """Admin uchun foydalanuvchilar ro'yxati testi"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Foydalanuvchilar ro\'yxati')

    def test_user_list_view_chef_forbidden(self):
        """Chef uchun foydalanuvchilar ro'yxati ruxsat yo'q testi"""
        self.client.login(username='chef', password='chefpass123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 302)

    def test_user_create_view_admin(self):
        """Admin uchun foydalanuvchi yaratish testi"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:user_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yangi foydalanuvchi yaratish')

    def test_logout_view(self):
        """Chiqish testi"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))


class AuthenticationTest(TestCase):
    """Autentifikatsiya testlari"""

    def setUp(self):
        self.role = Role.objects.create(name='manager')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            role=self.role
        )

    def test_login_required_views(self):
        """Login talab qiladigan sahifalar testi"""
        protected_urls = [
            reverse('accounts:dashboard'),
            reverse('accounts:profile'),
            reverse('accounts:profile_edit'),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_role_based_access(self):
        """Rol asosida kirish nazorati testi"""
        # Admin foydalanuvchi yaratish
        admin_role = Role.objects.create(name='admin')
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass',
            role=admin_role
        )

        # Chef foydalanuvchi yaratish
        chef_role = Role.objects.create(name='chef')
        chef_user = User.objects.create_user(
            username='chef',
            email='chef@test.com',
            password='chefpass',
            role=chef_role
        )

        # Admin sahifalariga kirish
        admin_urls = [
            reverse('accounts:user_list'),
            reverse('accounts:user_create'),
        ]

        # Admin bilan kirish
        self.client.login(username='admin', password='adminpass')
        for url in admin_urls:
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, 403)

        # Chef bilan kirish (ruxsat yo'q)
        self.client.login(username='chef', password='chefpass')
        for url in admin_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirect to dashboard