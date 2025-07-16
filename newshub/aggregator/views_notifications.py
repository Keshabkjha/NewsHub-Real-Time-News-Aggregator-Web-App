import json
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.db.models import Q, Count, F
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import Notification, NotificationPreference, PushNotificationSubscription
from .notification_service import NotificationService
from .forms import NotificationPreferenceForm, PushSubscriptionForm, EmailUnsubscribeForm
from .webpush_service import WebPushService

logger = logging.getLogger(__name__)

@login_required
def notification_list(request):
    """
    View to display all notifications for the current user with filtering and pagination.
    """
    # Get filter parameters
    notification_type = request.GET.get('type', 'all')
    read_status = request.GET.get('read', 'all')
    
    # Base queryset
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Apply filters
    if notification_type != 'all':
        notifications = notifications.filter(notification_type=notification_type)
    
    if read_status == 'read':
        notifications = notifications.filter(read=True)
    elif read_status == 'unread':
        notifications = notifications.filter(read=False)
    
    # Get unread count before marking as read (for the badge)
    unread_count = Notification.objects.filter(user=request.user, read=False).count()
    
    # Mark all notifications as read when viewing the list (if not in unread filter)
    if read_status != 'unread':
        NotificationService.mark_all_notifications_read(request.user)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(notifications, 20)  # 20 notifications per page
    
    try:
        notifications_page = paginator.page(page)
    except PageNotAnInteger:
        notifications_page = paginator.page(1)
    except EmptyPage:
        notifications_page = paginator.page(paginator.num_pages)
    
    # Get notification type choices for filter dropdown
    notification_types = [('all', 'All Types')] + [
        (choice[0], choice[1]) for choice in Notification.NOTIFICATION_TYPES
    ]
    
    return render(request, 'notifications/list.html', {
        'notifications': notifications_page,
        'unread_count': unread_count,
        'current_type': notification_type,
        'current_read_status': read_status,
        'notification_types': notification_types,
        'filter_active': any([notification_type != 'all', read_status != 'all']),
    })

@login_required
def notification_detail(request, notification_id):
    """
    View to display a single notification, mark it as read, and show related notifications.
    """
    # Get the notification and verify ownership
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Mark as read when viewed
    if not notification.read:
        notification.mark_as_read()
    
    # Get related notifications (same type, same user, excluding current)
    related_notifications = Notification.objects.filter(
        user=request.user,
        notification_type=notification.notification_type,
        read=False
    ).exclude(id=notification.id).order_by('-created_at')[:5]
    
    # Get previous and next notifications for navigation
    prev_notification = Notification.objects.filter(
        user=request.user,
        created_at__lt=notification.created_at
    ).order_by('-created_at').first()
    
    next_notification = Notification.objects.filter(
        user=request.user,
        created_at__gt=notification.created_at
    ).order_by('created_at').first()
    
    # Get unread count for the badge
    unread_count = Notification.objects.filter(user=request.user, read=False).count()
    
    return render(request, 'notifications/detail.html', {
        'notification': notification,
        'related_notifications': related_notifications,
        'prev_notification': prev_notification,
        'next_notification': next_notification,
        'unread_count': unread_count,
    })
    
    # If the notification has a URL, redirect to it
    if notification.url:
        return redirect(notification.url)
    
    return render(request, 'notifications/detail.html', {
        'notification': notification,
    })

@login_required
def mark_notification_read(request, notification_id):
    """
    API endpoint to mark a single notification as read.
    """
    if request.method == 'POST':
        success = NotificationService.mark_notification_read(notification_id, request.user)
        return JsonResponse({'success': success})
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@login_required
def mark_all_read(request):
    """
    API endpoint to mark all notifications as read.
    """
    if request.method == 'POST':
        count = NotificationService.mark_all_notifications_read(request.user)
        return JsonResponse({'success': True, 'count': count})
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@login_required
def notification_preferences(request):
    """
    View to manage notification preferences, including email and push notification settings.
    """
    # Get or create user preferences
    preferences, created = NotificationPreference.get_or_create_preferences(request.user)
    
    # Get push subscription status
    push_subscriptions = PushNotificationSubscription.objects.filter(
        user=request.user,
        is_active=True
    )
    
    # Handle form submissions
    if request.method == 'POST':
        # Determine which form was submitted
        if 'update_preferences' in request.POST:
            # Handle notification preferences form
            form = NotificationPreferenceForm(request.POST, instance=preferences)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your notification preferences have been updated.')
                return redirect('notifications:preferences')
            
        elif 'unsubscribe_email' in request.POST:
            # Handle email unsubscribe form
            form = EmailUnsubscribeForm(request.POST)
            if form.is_valid():
                # Update preferences to disable all email notifications
                preferences.email_notifications_enabled = False
                preferences.marketing_emails = False
                preferences.save()
                messages.success(request, 'You have been unsubscribed from all email notifications.')
                return redirect('notifications:preferences')
        
        elif 'subscribe_push' in request.POST:
            # Handle push subscription form (handled by JavaScript, this is just a fallback)
            form = PushSubscriptionForm(request.POST)
            if form.is_valid():
                # This will be handled by the JavaScript push manager
                messages.info(request, 'Please use the browser prompt to enable push notifications.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Error with push subscription: {error}")
    else:
        # Initialize forms for GET request
        form = NotificationPreferenceForm(instance=preferences)
    
    # Get notification type choices for the template
    notification_types = Notification.NOTIFICATION_TYPES
    
    # Get the VAPID public key for push notifications
    from .webpush_config import get_webpush_settings
    webpush_settings = get_webpush_settings()
    vapid_public_key = webpush_settings.get('VAPID_PUBLIC_KEY', '')
    
    return render(request, 'notifications/preferences.html', {
        'form': form,
        'preferences': preferences,
        'push_subscriptions': push_subscriptions,
        'has_push_support': hasattr(request, 'user') and request.user.is_authenticated and 
                           hasattr(request.user, 'notification_preferences'),
        'vapid_public_key': vapid_public_key,
        'notification_types': notification_types,
        'unread_count': Notification.objects.filter(user=request.user, read=False).count(),
    })

@login_required
@require_http_methods(["POST"])
def save_push_subscription(request):
    """
    API endpoint to save a push notification subscription.
    
    Expected JSON payload:
    {
        "endpoint": "https://fcm.googleapis.com/...",
        "keys": {
            "p256dh": "...",
            "auth": "..."
        },
        "user_visible_only": true
    }
    """
    try:
        # Parse the JSON data from the request body
        data = json.loads(request.body)
        
        # Validate the subscription data
        if not all(key in data for key in ['endpoint', 'keys']):
            return JsonResponse(
                {'error': 'Missing required subscription data'}, 
                status=400
            )
        
        # Get or create the subscription
        subscription, created = PushNotificationSubscription.objects.get_or_create(
            user=request.user,
            endpoint=data['endpoint'],
            defaults={
                'auth': data['keys'].get('auth', ''),
                'p256dh': data['keys'].get('p256dh', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'ip_address': request.META.get('REMOTE_ADDR', '')[:45],
                'is_active': True
            }
        )
        
        # If the subscription exists but was inactive, reactivate it
        if not created and not subscription.is_active:
            subscription.is_active = True
            subscription.save(update_fields=['is_active', 'modified_at'])
        
        # Update the last active timestamp
        subscription.update_last_active()
        
        return JsonResponse({
            'status': 'success',
            'subscription_id': subscription.id,
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error saving push subscription: {str(e)}", exc_info=True)
        return JsonResponse(
            {'error': 'An error occurred while processing your request'}, 
            status=500
        )

@login_required
@require_http_methods(["POST"])
def remove_push_subscription(request, subscription_id=None):
    """
    API endpoint to remove a push notification subscription.
    If no subscription_id is provided, all subscriptions for the user will be deactivated.
    
    Expected URL: /notifications/push/unsubscribe/ or /notifications/push/unsubscribe/<id>/
    """
    try:
        if subscription_id is not None:
            # Deactivate specific subscription
            subscription = get_object_or_404(
                PushNotificationSubscription,
                id=subscription_id,
                user=request.user
            )
            subscription.deactivate()
            message = 'Push notification subscription has been deactivated.'
        else:
            # Deactivate all subscriptions for the user
            count = PushNotificationSubscription.objects.filter(
                user=request.user,
                is_active=True
            ).update(is_active=False)
            message = f'Deactivated {count} push notification subscription(s).'
            
        return JsonResponse({
            'status': 'success',
            'message': message
        })
        
    except Exception as e:
        logger.error("Error removing push subscription: %s", str(e), exc_info=True)
        return JsonResponse(
            {'error': 'An error occurred while processing your request'}, 
            status=500
        )

@login_required
def get_unread_count(request):
    """
    API endpoint to get the count of unread notifications.
    """
    count = Notification.objects.filter(user=request.user, read=False).count()
    return JsonResponse({'count': count})
