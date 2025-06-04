from django.contrib.auth.models import AbstractUser, BaseUserManager  # BaseUserManager ni import qiling
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """Foydalanuvchi rollari modeli"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('chef', 'Chef'),
        ('manager', 'Manager'),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=ROLE_CHOICES,
        verbose_name="Rol nomi"
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Rol tavsifi"
    )
    permissions = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Ruxsatlar ro'yxati"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan sana"
    )

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Rollar"
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


# CustomUserManager ni qo'shing
class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not username:
            raise ValueError(_('The Username field must be set'))

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)  # Superuser odatda aktiv bo'lishi kerak

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        # "Admin" rolini ma'lumotlar bazasidan topib, tayinlaymiz
        try:
            admin_role = Role.objects.get(name='admin')  # 'admin' choicesdagi qiymat bo'lishi kerak
            extra_fields['role'] = admin_role
        except Role.DoesNotExist:
            raise ValueError(_("Admin role does not exist. Please run 'python manage.py create_default_roles' first."))

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Maxsus foydalanuvchi modeli"""
    email = models.EmailField(
        unique=True,
        verbose_name="Email manzil"
    )
    first_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Ism"
    )
    last_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Familiya"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        verbose_name="Rol",
        # default='admin', # BU QATORNI O'CHIRING
        null=True,  # Rol majburiy bo'lmasa, null=True, blank=True qo'shing
        blank=True,
    )

    USERNAME_FIELD = 'username'  # Username fieldini saqlab qolganingiz yaxshi
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()  # Custom menejerni tayinlang

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"

    def get_full_name(self):
        """To'liq ismni qaytaradi"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def has_permission(self, permission):
        """Foydalanuvchining ma'lum ruxsatga ega ekanligini tekshiradi"""
        if self.role and self.role.permissions:
            return permission in self.role.permissions
        return False

    def is_admin(self):
        return self.role and self.role.name == 'admin'  # Role null bo'lishi mumkinligini hisobga oling

    def is_chef(self):
        return self.role and self.role.name == 'chef'

    def is_manager(self):
        return self.role and self.role.name == 'manager'


class UserProfile(models.Model):
    # ... (qolgan kod o'zgarishsiz qoladi) ...
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Foydalanuvchi"
    )
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Telefon raqami"
    )
    address = models.TextField(
        null=True,
        blank=True,
        verbose_name="Manzil"
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Tug'ilgan sana"
    )
    shift_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Ish boshlanish vaqti"
    )
    shift_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Ish tugash vaqti"
    )
    photo = models.ImageField(
        upload_to='profile_photos/',
        null=True,
        blank=True,
        verbose_name="Profil rasmi"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan sana"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan sana"
    )

    class Meta:
        verbose_name = "Foydalanuvchi profili"
        verbose_name_plural = "Foydalanuvchi profillari"

    def __str__(self):
        return f"{self.user.username} profili"







# from django.contrib.auth.models import AbstractUser
# from django.db import models
# from django.utils.translation import gettext_lazy as _
#
#
# class Role(models.Model):
#     """Foydalanuvchi rollari modeli"""
#     ROLE_CHOICES = [
#         ('admin', 'Admin'),
#         ('chef', 'Chef'),
#         ('manager', 'Manager'),
#     ]
#
#     name = models.CharField(
#         max_length=50,
#         unique=True,
#         choices=ROLE_CHOICES,
#         verbose_name="Rol nomi"
#     )
#     description = models.TextField(
#         null=True,
#         blank=True,
#         verbose_name="Rol tavsifi"
#     )
#     permissions = models.JSONField(
#         null=True,
#         blank=True,
#         verbose_name="Ruxsatlar ro'yxati"
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name="Yaratilgan sana"
#     )
#
#     class Meta:
#         verbose_name = "Rol"
#         verbose_name_plural = "Rollar"
#         ordering = ['name']
#
#     def __str__(self):
#         return self.get_name_display()
#
#
# class CustomUser(AbstractUser):
#     """Maxsus foydalanuvchi modeli"""
#     email = models.EmailField(
#         unique=True,
#         verbose_name="Email manzil"
#     )
#     first_name = models.CharField(
#         max_length=150,
#         null=True,
#         blank=True,
#         verbose_name="Ism"
#     )
#     last_name = models.CharField(
#         max_length=150,
#         null=True,
#         blank=True,
#         verbose_name="Familiya"
#     )
#     role = models.ForeignKey(
#         Role,
#         on_delete=models.PROTECT,
#         verbose_name="Rol",
#         # default='admin',
#         # null = True,
#         # blank = True,
#     )
#
#     USERNAME_FIELD = 'username'
#     REQUIRED_FIELDS = ['email']
#
#     class Meta:
#         verbose_name = "Foydalanuvchi"
#         verbose_name_plural = "Foydalanuvchilar"
#         ordering = ['username']
#
#     def __str__(self):
#         return f"{self.username} ({self.get_full_name()})"
#
#     def get_full_name(self):
#         """To'liq ismni qaytaradi"""
#         if self.first_name and self.last_name:
#             return f"{self.first_name} {self.last_name}"
#         return self.username
#
#     def has_permission(self, permission):
#         """Foydalanuvchining ma'lum ruxsatga ega ekanligini tekshiradi"""
#         if self.role and self.role.permissions:
#             return permission in self.role.permissions
#         return False
#
#     def is_admin(self):
#         return self.role.name == 'admin'
#
#     def is_chef(self):
#         return self.role.name == 'chef'
#
#     def is_manager(self):
#         return self.role.name == 'manager'
#
#
# class UserProfile(models.Model):
#     """Foydalanuvchi profili modeli"""
#     user = models.OneToOneField(
#         CustomUser,
#         on_delete=models.CASCADE,
#         related_name='profile',
#         verbose_name="Foydalanuvchi"
#     )
#     phone_number = models.CharField(
#         max_length=20,
#         null=True,
#         blank=True,
#         verbose_name="Telefon raqami"
#     )
#     address = models.TextField(
#         null=True,
#         blank=True,
#         verbose_name="Manzil"
#     )
#     birth_date = models.DateField(
#         null=True,
#         blank=True,
#         verbose_name="Tug'ilgan sana"
#     )
#     shift_start = models.TimeField(
#         null=True,
#         blank=True,
#         verbose_name="Ish boshlanish vaqti"
#     )
#     shift_end = models.TimeField(
#         null=True,
#         blank=True,
#         verbose_name="Ish tugash vaqti"
#     )
#     photo = models.ImageField(
#         upload_to='profile_photos/',
#         null=True,
#         blank=True,
#         verbose_name="Profil rasmi"
#     )
#     created_at = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name="Yaratilgan sana"
#     )
#     updated_at = models.DateTimeField(
#         auto_now=True,
#         verbose_name="Yangilangan sana"
#     )
#
#     class Meta:
#         verbose_name = "Foydalanuvchi profili"
#         verbose_name_plural = "Foydalanuvchi profillari"
#
#     def __str__(self):
#         return f"{self.user.username} profili"