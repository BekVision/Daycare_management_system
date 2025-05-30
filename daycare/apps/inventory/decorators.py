# apps/accounts/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(permission_attr):
    """
    Role va permission tekshiruvchi decorator
    Usage: @role_required('can_manage_inventory')
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # User role tekshiruvi
            if not hasattr(request.user, 'role') or not request.user.role:
                messages.error(request, "Sizga role tayinlanmagan. Admin bilan bog'laning.")
                return redirect('dashboard')

            # Permissions tekshiruvi
            if not hasattr(request.user.role, 'permissions') or not request.user.role.permissions:
                messages.error(request, "Role uchun ruxsatlar sozlanmagan.")
                return redirect('dashboard')

            # Specific permission tekshiruvi
            if not getattr(request.user.role.permissions, permission_attr, False):
                messages.error(request, f"Bu amalni bajarish huquqingiz yo'q.")
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def inventory_required(view_func):
    """Inventar huquqi kerak bo'lgan view'lar uchun"""
    return role_required('can_manage_inventory')(view_func)