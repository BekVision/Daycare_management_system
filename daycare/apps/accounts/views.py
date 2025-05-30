from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CustomUser, UserProfile, Role
from .forms import CustomUserCreationForm, UserProfileForm, LoginForm


def login_view(request):
    """Foydalanuvchi kirish sahifasi"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Activity log yaratish (faqat core.models mavjud bo'lsa)
                try:
                    from core.models import ActivityLog
                    ActivityLog.objects.create(
                        user=user,
                        action='USER_LOGIN',
                        object_type='User',
                        object_id=user.id,
                        object_repr=str(user),
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )
                except ImportError:
                    pass  # core app hali yaratilmagan
                return redirect('accounts:dashboard')
            else:
                messages.error(request, 'Noto\'g\'ri foydalanuvchi nomi yoki parol')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Foydalanuvchi chiqish"""
    # Activity log yaratish (faqat core.models mavjud bo'lsa)
    try:
        from core.models import ActivityLog
        ActivityLog.objects.create(
            user=request.user,
            action='USER_LOGOUT',
            object_type='User',
            object_id=request.user.id,
            object_repr=str(request.user),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
    except ImportError:
        pass  # core app hali yaratilmagan
    logout(request)
    messages.success(request, 'Muvaffaqiyatli chiqildi')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Foydalanuvchi profili ko'rish"""
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': request.user.profile
    })


@login_required
def profile_edit(request):
    """Foydalanuvchi profili tahrirlash"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil muvaffaqiyatli yangilandi')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user.profile)

    return render(request, 'accounts/profile_edi.html', {'form': form})


class UserCreateView(LoginRequiredMixin, CreateView):
    """Yangi foydalanuvchi yaratish"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_create.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Activity log yaratish (faqat core.models mavjud bo'lsa)
        try:
            from core.models import ActivityLog
            ActivityLog.objects.create(
                user=self.request.user,
                action='USER_CREATED',
                object_type='User',
                object_id=self.object.id,
                object_repr=str(self.object),
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT')
            )
        except ImportError:
            pass  # core app hali yaratilmagan
        messages.success(self.request, 'Foydalanuvchi muvaffaqiyatli yaratildi')
        return response

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin():
            messages.error(request, 'Bu sahifaga kirish uchun ruxsat yo\'q')
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class UserListView(LoginRequiredMixin, ListView):
    """Foydalanuvchilar ro'yxati"""
    model = CustomUser
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin():
            messages.error(request, 'Bu sahifaga kirish uchun ruxsat yo\'q')
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard(request):
    """Asosiy dashboard sahifasi"""
    context = {
        'user': request.user,
        'role': request.user.role.name,
    }

    # Role ga qarab turli ma'lumotlar ko'rsatish
    if request.user.is_admin():
        try:
            from core.models import ActivityLog
            context['recent_activities'] = ActivityLog.objects.select_related('user')[:10]
        except ImportError:
            context['recent_activities'] = []

        try:
            from inventory.models import Stock
            from django.db import models
            context['low_stock_count'] = Stock.objects.filter(
                current_quantity__lte=models.F('ingredient__min_threshold')
            ).count()
        except ImportError:
            context['low_stock_count'] = 0

        try:
            from meals.models import Meal
            context['total_meals'] = Meal.objects.filter(is_active=True).count()
        except ImportError:
            context['total_meals'] = 0

        context['total_users'] = CustomUser.objects.filter(is_active=True).count()

    elif request.user.is_manager():
        try:
            from inventory.models import Stock
            from django.db import models
            context['low_stock_items'] = Stock.objects.filter(
                current_quantity__lte=models.F('ingredient__min_threshold')
            ).select_related('ingredient')[:5]
        except ImportError:
            context['low_stock_items'] = []

        try:
            from reports.models import DailyReport
            from datetime import date
            context['today_report'] = DailyReport.objects.filter(report_date=date.today()).first()
        except ImportError:
            context['today_report'] = None

    elif request.user.is_chef():
        try:
            from meal_service.models import MealService
            from datetime import date
            context['today_services'] = MealService.objects.filter(
                service_date=date.today()
            ).select_related('meal')[:5]
        except ImportError:
            context['today_services'] = []

        try:
            from meals.models import Meal
            context['available_meals'] = Meal.objects.filter(is_active=True)[:10]
        except ImportError:
            context['available_meals'] = []

    return render(request, 'accounts/dashboard.html', context)