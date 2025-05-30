from django.contrib.auth.models import AbstractUser
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
        verbose_name="Rol"
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

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
        return self.role.name == 'admin'

    def is_chef(self):
        return self.role.name == 'chef'

    def is_manager(self):
        return self.role.name == 'manager'


class UserProfile(models.Model):
    """Foydalanuvchi profili modeli"""
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