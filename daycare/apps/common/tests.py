from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from unittest.mock import patch
import json
from .models import AppSettings, ActivityLog, SystemHealth
from .utils import log_activity, get_setting, set_setting, check_system_health
from .forms import AppSettingsForm

User = get_user_model()


class AppSettingsModelTest(TestCase):
    """AppSettings modeli uchun testlar"""

    def test_create_setting(self):
        """Sozlama yaratish testi"""
        setting = AppSettings.objects.create(
            key='TEST_SETTING',
            value='test_value',
            data_type='STRING',
            description='Test sozlama'
        )
        self.assertEqual(setting.key, 'TEST_SETTING')
        self.assertEqual(setting.value, 'test_value')
        self.assertTrue(setting.is_editable)

    def test_get_typed_value_string(self):
        """String qiymat olish testi"""
        setting = AppSettings.objects.create(
            key='STRING_TEST',
            value='hello world',
            data_type='STRING'
        )
        self.assertEqual(setting.get_typed_value(), 'hello world')

    def test_get_typed_value_integer(self):
        """Integer qiymat olish testi"""
        setting = AppSettings.objects.create(
            key='INT_TEST',
            value='42',
            data_type='INTEGER'
        )
        self.assertEqual(setting.get_typed_value(), 42)

    def test_get_typed_value_float(self):
        """Float qiymat olish testi"""
        setting = AppSettings.objects.create(
            key='FLOAT_TEST',
            value='3.14',
            data_type='FLOAT'
        )
        self.assertAlmostEqual(setting.get_typed_value(), 3.14)

    def test_get_typed_value_boolean(self):
        """Boolean qiymat olish testi"""
        setting_true = AppSettings.objects.create(
            key='BOOL_TRUE',
            value='true',
            data_type='BOOLEAN'
        )
        setting_false = AppSettings.objects.create(
            key='BOOL_FALSE',
            value='false',
            data_type='BOOLEAN'
        )
        self.assertTrue(setting_true.get_typed_value())
        self.assertFalse(setting_false.get_typed_value())

    def test_get_typed_value_json(self):
        """JSON qiymat olish testi"""
        setting = AppSettings.objects.create(
            key='JSON_TEST',
            value='{"key": "value", "number": 42}',
            data_type='JSON'
        )
        expected = {"key": "value", "number": 42}
        self.assertEqual(setting.get_typed_value(), expected)


class ActivityLogModelTest(TestCase):
    """ActivityLog modeli uchun testlar"""

    def setUp(self):
        from apps.accounts.models import Role
        self.role = Role.objects.create(name='admin')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass',
            role=self.role
        )

    def test_create_activity_log(self):
        """Activity log yaratish testi"""
        log = ActivityLog.objects.create(
            user=self.user,
            action='USER_LOGIN',
            object_type='User',
            object_id=self.user.id,
            object_repr=str(self.user)
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'USER_LOGIN')
        self.assertEqual(log.object_type, 'User')

    def test_activity_log_str(self):
        """Activity log string representation testi"""
        log = ActivityLog.objects.create(
            user=self.user,
            action='USER_LOGIN',
            object_type='User'
        )
        expected = f"{self.user.username} - Foydalanuvchi kirdi - {log.timestamp}"
        self.assertEqual(str(log), expected)


class SystemHealthModelTest(TestCase):
    """SystemHealth modeli uchun testlar"""

    def test_create_system_health(self):
        """System health yaratish testi"""
        health = SystemHealth.objects.create(
            component='DATABASE',
            status=SystemHealth.StatusChoices.HEALTHY,
            response_time=0.5
        )
        self.assertEqual(health.component, 'DATABASE')
        self.assertEqual(health.status, 'HEALTHY')
        self.assertEqual(health.response_time, 0.5)

    def test_system_health_str(self):
        """System health string representation testi"""
        health = SystemHealth.objects.create(
            component='DATABASE',
            status=SystemHealth.StatusChoices.HEALTHY
        )
        expected = f"Ma'lumotlar bazasi - Sog'lom - {health.checked_at}"
        self.assertEqual(str(health), expected)


class UtilsTest(TestCase):
    """Utils funksiyalari uchun testlar"""

    def setUp(self):
        from apps.accounts.models import Role
        self.role = Role.objects.create(name='admin')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass',
            role=self.role
        )

    def test_log_activity(self):
        """Activity log yaratish funksiyasi testi"""
        log_activity(
            user=self.user,
            action='TEST_ACTION',
            object_type='TestObject',
            object_id=1,
            object_repr='Test Object'
        )

        log = ActivityLog.objects.get(action='TEST_ACTION')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.object_type, 'TestObject')

    def test_get_setting(self):
        """Setting olish funksiyasi testi"""
        AppSettings.objects.create(
            key='TEST_KEY',
            value='test_value',
            data_type='STRING'
        )

        value = get_setting('TEST_KEY')
        self.assertEqual(value, 'test_value')

        # Mavjud bo'lmagan setting
        default_value = get_setting('NON_EXISTENT', 'default')
        self.assertEqual(default_value, 'default')

    def test_set_setting(self):
        """Setting o'rnatish funksiyasi testi"""
        setting = set_setting('NEW_KEY', 'new_value', 'STRING', 'Test description')

        self.assertEqual(setting.key, 'NEW_KEY')
        self.assertEqual(setting.value, 'new_value')
        self.assertEqual(setting.description, 'Test description')

        # Mavjud settingni yangilash
        updated_setting = set_setting('NEW_KEY', 'updated_value')
        self.assertEqual(updated_setting.value, 'updated_value')

    @patch('apps.common.utils.connection')
    def test_check_database_health(self, mock_connection):
        """Database health check testi"""
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = (1,)

        from .utils import check_database_health
        result = check_database_health()

        self.assertTrue(result['healthy'])
        self.assertEqual(result['component'], 'DATABASE')
        self.assertIn('response_time', result)


class FormsTest(TestCase):
    """Forms uchun testlar"""

    def setUp(self):
        self.setting = AppSettings.objects.create(
            key='TEST_SETTING',
            value='test_value',
            data_type='STRING'
        )

    def test_app_settings_form_valid(self):
        """AppSettings form validation testi"""
        form_data = {
            'value': 'new_value',
            'description': 'Updated description'
        }
        form = AppSettingsForm(data=form_data, instance=self.setting)
        self.assertTrue(form.is_valid())

    def test_app_settings_form_integer_validation(self):
        """Integer field validation testi"""
        int_setting = AppSettings.objects.create(
            key='INT_SETTING',
            value='42',
            data_type='INTEGER'
        )

        # Valid integer
        form_data = {'value': '100', 'description': ''}
        form = AppSettingsForm(data=form_data, instance=int_setting)
        self.assertTrue(form.is_valid())

        # Invalid integer
        form_data = {'value': 'not_a_number', 'description': ''}
        form = AppSettingsForm(data=form_data, instance=int_setting)
        self.assertFalse(form.is_valid())

    def test_app_settings_form_json_validation(self):
        """JSON field validation testi"""
        json_setting = AppSettings.objects.create(
            key='JSON_SETTING',
            value='{"key": "value"}',
            data_type='JSON'
        )

        # Valid JSON
        form_data = {'value': '{"new_key": "new_value"}', 'description': ''}
        form = AppSettingsForm(data=form_data, instance=json_setting)
        self.assertTrue(form.is_valid())

        # Invalid JSON
        form_data = {'value': '{invalid json}', 'description': ''}
        form = AppSettingsForm(data=form_data, instance=json_setting)
        self.assertFalse(form.is_valid())


class ViewsTest(TestCase):
    """Views uchun testlar"""

    def setUp(self):
        self.client = Client()
        from apps.accounts.models import Role
        self.admin_role = Role.objects.create(name='admin')
        self.chef_role = Role.objects.create(name='chef')

        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass',
            role=self.admin_role
        )

        self.chef_user = User.objects.create_user(
            username='chef',
            email='chef@test.com',
            password='chefpass',
            role=self.chef_role
        )

        self.setting = AppSettings.objects.create(
            key='TEST_SETTING',
            value='test_value',
            data_type='STRING',
            is_editable=True
        )

    def test_settings_list_admin_access(self):
        """Admin uchun settings list sahifasi testi"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('common:settings_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST_SETTING')

    def test_settings_list_chef_access_denied(self):
        """Chef uchun settings list ruxsat yo'q testi"""
        self.client.login(username='chef', password='chefpass')
        response = self.client.get(reverse('common:settings_list'))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_settings_edit_get(self):
        """Settings edit GET request testi"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(
            reverse('common:settings_edit', args=[self.setting.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST_SETTING')

    def test_settings_edit_post(self):
        """Settings edit POST request testi"""
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(
            reverse('common:settings_edit', args=[self.setting.id]),
            {
                'value': 'updated_value',
                'description': 'Updated description'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Check if setting was updated
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, 'updated_value')

    def test_activity_logs_view(self):
        """Activity logs view testi"""
        # Create some activity logs
        ActivityLog.objects.create(
            user=self.admin_user,
            action='TEST_ACTION',
            object_type='TestObject'
        )

        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('common:activity_logs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TEST_ACTION')

    def test_system_health_view(self):
        """System health view testi"""
        # Create health check data
        SystemHealth.objects.create(
            component='DATABASE',
            status=SystemHealth.StatusChoices.HEALTHY,
            response_time=0.5
        )

        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('common:system_health'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DATABASE')

    def test_settings_api_view(self):
        """Settings API view testi"""
        self.client.login(username='admin', password='adminpass')

        # Get specific setting
        response = self.client.get(
            reverse('common:settings_api'),
            {'key': 'TEST_SETTING'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['key'], 'TEST_SETTING')
        self.assertEqual(data['value'], 'test_value')

        # Get all settings
        response = self.client.get(reverse('common:settings_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('TEST_SETTING', data)


class ManagementCommandsTest(TestCase):
    """Management commands uchun testlar"""

    def test_create_default_settings_command(self):
        """Default settings yaratish command testi"""
        # Command ishga tushirishdan oldin
        initial_count = AppSettings.objects.count()

        # Command ishga tushirish
        call_command('create_default_settings')

        # Command ishga tushirishdan keyin
        final_count = AppSettings.objects.count()
        self.assertGreater(final_count, initial_count)

        # Ba'zi standart sozlamalar mavjudligini tekshirish
        self.assertTrue(AppSettings.objects.filter(key='SITE_NAME').exists())
        self.assertTrue(AppSettings.objects.filter(key='ADMIN_EMAILS').exists())

    def test_cleanup_logs_command_dry_run(self):
        """Cleanup logs command dry run testi"""
        # Ba'zi eski loglar yaratish
        from datetime import timedelta
        from django.utils import timezone

        ActivityLog.objects.create(
            user_id=1,  # Dummy user ID
            action='OLD_ACTION',
            object_type='TestObject',
            timestamp=timezone.now() - timedelta(days=100)
        )

        initial_count = ActivityLog.objects.count()

        # Dry run command
        call_command('cleanup_logs', '--days=30', '--dry-run')

        # Hech narsa o'chirilmasligi kerak
        final_count = ActivityLog.objects.count()
        self.assertEqual(initial_count, final_count)

    @patch('apps.common.utils.check_system_health')
    def test_health_check_command(self, mock_health_check):
        """Health check command testi"""
        mock_health_check.return_value = [
            {
                'component': 'DATABASE',
                'status': 'HEALTHY',
                'healthy': True,
                'response_time': 0.1
            }
        ]

        # Command ishga tushirish
        call_command('health_check')

        # Mock funksiya chaqirilganligini tekshirish
        mock_health_check.assert_called_once()


class IntegrationTest(TestCase):
    """Integration testlar"""

    def setUp(self):
        from apps.accounts.models import Role
        self.admin_role = Role.objects.create(name='admin')
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass',
            role=self.admin_role
        )
        self.client = Client()

    def test_full_settings_workflow(self):
        """To'liq settings workflow testi"""
        self.client.login(username='admin', password='adminpass')

        # 1. Default settings yaratish
        call_command('create_default_settings')

        # 2. Settings list ko'rish
        response = self.client.get(reverse('common:settings_list'))
        self.assertEqual(response.status_code, 200)

        # 3. Biror settingni tahrirlash
        setting = AppSettings.objects.filter(is_editable=True).first()
        if setting:
            response = self.client.post(
                reverse('common:settings_edit', args=[setting.id]),
                {
                    'value': 'new_test_value',
                    'description': 'Updated in integration test'
                }
            )
            self.assertEqual(response.status_code, 302)

            # 4. Activity log yaratilganligini tekshirish
            self.assertTrue(
                ActivityLog.objects.filter(
                    user=self.admin_user,
                    action='SETTING_UPDATED'
                ).exists()
            )

    def test_health_monitoring_workflow(self):
        """Health monitoring workflow testi"""
        self.client.login(username='admin', password='adminpass')

        # 1. Health check ishga tushirish
        response = self.client.post(reverse('common:run_health_check'))
        self.assertEqual(response.status_code, 302)

        # 2. Health data yaratilganligini tekshirish
        self.assertTrue(SystemHealth.objects.exists())

        # 3. Health page ko'rish
        response = self.client.get(reverse('common:system_health'))
        self.assertEqual(response.status_code, 200)