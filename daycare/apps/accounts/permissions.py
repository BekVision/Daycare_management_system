from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Admin foydalanuvchilar uchun ruxsat"""

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                request.user.is_admin()
        )


class IsManagerUser(permissions.BasePermission):
    """Manager yoki admin foydalanuvchilar uchun ruxsat"""

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                (request.user.is_admin() or request.user.is_manager())
        )


class IsChefUser(permissions.BasePermission):
    """Chef, manager yoki admin foydalanuvchilar uchun ruxsat"""

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                (request.user.is_admin() or
                 request.user.is_manager() or
                 request.user.is_chef())
        )


class IsOwnerOrAdminUser(permissions.BasePermission):
    """Ob'ekt egasi yoki admin foydalanuvchilar uchun ruxsat"""

    def has_object_permission(self, request, view, obj):
        # Admin har doim ruxsat oladi
        if request.user.is_admin():
            return True

        # Ob'ekt egasi ruxsat oladi
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False


# Permission constants
PERMISSIONS = {
    'admin': [
        'view_all_users',
        'create_user',
        'edit_user',
        'delete_user',
        'view_all_reports',
        'create_report',
        'edit_settings',
        'view_system_health',
        'manage_inventory',
        'manage_meals',
        'serve_meals',
    ],
    'manager': [
        'view_reports',
        'manage_inventory',
        'view_users',
        'manage_meals',
        'serve_meals',
    ],
    'chef': [
        'serve_meals',
        'view_inventory',
        'view_meals',
    ]
}