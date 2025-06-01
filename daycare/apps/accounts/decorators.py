from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """Role asosida ruxsat beruvchi decorator"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role.name in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Bu sahifaga kirish uchun ruxsat yo\'q')
                return redirect('accounts:dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Admin roli talab qiladigan decorator"""
    return role_required(['admin'])(view_func)


def manager_required(view_func):
    """Manager yoki admin roli talab qiladigan decorator"""
    return role_required(['admin', 'manager'])(view_func)


def chef_required(view_func):
    """Chef, manager yoki admin roli talab qiladigan decorator"""
    return role_required(['admin', 'manager', 'chef'])(view_func)

def admin_or_manager_required(view_func):
   """Admin yoki Manager roli talab qiladigan decorator"""
   return role_required(['admin', 'manager'])(view_func)