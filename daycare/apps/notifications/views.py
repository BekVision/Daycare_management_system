# notifications/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Notification, NotificationPreference
from .forms import NotificationPreferenceForm


@login_required
def notification_list(request):
    """Bildirishnomalar ro'yxati"""
    notifications = Notification.objects.filter(recipient=request.user)

    # Filtrlash
    type_filter = request.GET.get('type')
    priority_filter = request.GET.get('priority')
    read_filter = request.GET.get('read')

    if type_filter:
        notifications = notifications.filter(type=type_filter)
    if priority_filter:
        notifications = notifications.filter(priority=priority_filter)
    if read_filter == '1':
        notifications = notifications.filter(is_read=True)
    elif read_filter == '0':
        notifications = notifications.filter(is_read=False)

    # Qidiruv
    search = request.GET.get('search')
    if search:
        notifications = notifications.filter(
            Q(title__icontains=search) |
            Q(message__icontains=search)
        )

    notifications = notifications.order_by('-created_at')

    # Sahifalash
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Ko'rilgan deb belgilash
    unread_notifications = notifications.filter(is_seen=False)
    if unread_notifications.exists():
        unread_notifications.update(is_seen=True)

    # Filter options
    type_choices = Notification.TYPE_CHOICES
    priority_choices = Notification.PRIORITY_CHOICES

    context = {
        'page_obj': page_obj,
        'type_choices': type_choices,
        'priority_choices': priority_choices,
        'search': search,
        'type_filter': type_filter,
        'priority_filter': priority_filter,
        'read_filter': read_filter,
        'total_notifications': notifications.count(),
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count(),
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_detail(request, pk):
    """Bildirishnoma tafsilotlari"""
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user
    )

    # O'qilgan deb belgilash
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()

    context = {
        'notification': notification,
    }
    return render(request, 'notifications/notification_detail.html', context)


@login_required
def notification_preferences(request):
    """Bildirishnoma sozlamalari"""
    preference, created = NotificationPreference.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sozlamalar saqlandi.')
            return redirect('notifications:preferences')
    else:
        form = NotificationPreferenceForm(instance=preference)

    context = {
        'form': form,
        'preference': preference,
    }
    return render(request, 'notifications/notification_preferences.html', context)


# =============================================
# AJAX VIEWS
# =============================================

@require_POST
@login_required
def mark_as_read(request, pk):
    """Bildirishnomani o'qilgan deb belgilash"""
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user
    )

    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()

    return JsonResponse({
        'success': True,
        'message': 'Bildirishnoma o\'qilgan deb belgilandi.'
    })


@require_POST
@login_required
def mark_as_unread(request, pk):
    """Bildirishnomani o'qilmagan deb belgilash"""
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user
    )

    notification.is_read = False
    notification.read_at = None
    notification.save()

    return JsonResponse({
        'success': True,
        'message': 'Bildirishnoma o\'qilmagan deb belgilandi.'
    })


@require_POST
@login_required
def mark_all_as_read(request):
    """Barcha bildirishnomalarni o'qilgan deb belgilash"""
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )

    return JsonResponse({
        'success': True,
        'message': f'{count} ta bildirishnoma o\'qilgan deb belgilandi.',
        'count': count
    })


@require_POST
@login_required
def delete_notification(request, pk):
    """Bildirishnomani o'chirish"""
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user
    )

    notification.delete()

    return JsonResponse({
        'success': True,
        'message': 'Bildirishnoma o\'chirildi.'
    })


@login_required
def get_unread_count(request):
    """O'qilmagan bildirishnomalar soni"""
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        'unread_count': count
    })


@login_required
def get_recent_notifications(request):
    """So'nggi bildirishnomalar"""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:10]

    data = {
        'notifications': [
            {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message[:100] + '...' if len(
                    notification.message) > 100 else notification.message,
                'type': notification.type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
                'action_url': notification.action_url,
            }
            for notification in notifications
        ],
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    }

    return JsonResponse(data)