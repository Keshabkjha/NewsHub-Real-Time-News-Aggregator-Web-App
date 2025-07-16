"""
API views for handling push notification subscriptions and other API endpoints.
"""

import json
import logging
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from pywebpush import webpush, WebPushException

from .models import PushNotificationSubscription
from .webpush_config import get_webpush_settings

logger = logging.getLogger(__name__)

# Get WebPush settings
WEBPUSH_SETTINGS = get_webpush_settings()

@require_http_methods(["POST"])
@login_required
def subscribe_push(request):
    """
    API endpoint to subscribe a user to push notifications.
    
    Request body should be a JSON object with the following structure:
    {
        "endpoint": "https://fcm.googleapis.com/fcm/send/...",
        "keys": {
            "auth": "...",
            "p256dh": "..."
        }
    }
    """
    try:
        # Parse the request body
        data = json.loads(request.body)
        
        # Validate the subscription data
        if not all(key in data for key in ['endpoint', 'keys']):
            return JsonResponse(
                {'error': 'Invalid subscription data'}, 
                status=400
            )
        
        if not all(key in data['keys'] for key in ['auth', 'p256dh']):
            return JsonResponse(
                {'error': 'Invalid subscription keys'}, 
                status=400
            )
        
        # Create or update the subscription
        subscription, created = PushNotificationSubscription.objects.update_or_create(
            user=request.user,
            endpoint=data['endpoint'],
            defaults={
                'auth': data['keys']['auth'],
                'p256dh': data['keys']['p256dh'],
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'ip_address': request.META.get('REMOTE_ADDR'),
                'is_active': True,
                'last_seen': timezone.now()
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'created': created,
            'id': subscription.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON data'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Error subscribing to push notifications: {str(e)}")
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=500
        )

@require_http_methods(["POST"])
@login_required
def unsubscribe_push(request):
    """
    API endpoint to unsubscribe a user from push notifications.
    
    Request body should be a JSON object with the endpoint to unsubscribe:
    {
        "endpoint": "https://fcm.googleapis.com/fcm/send/..."
    }
    """
    try:
        # Parse the request body
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return JsonResponse(
                {'error': 'Endpoint is required'}, 
                status=400
            )
        
        # Delete the subscription
        deleted, _ = PushNotificationSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint
        ).delete()
        
        return JsonResponse({
            'status': 'success',
            'deleted': deleted > 0
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON data'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Error unsubscribing from push notifications: {str(e)}")
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=500
        )

@require_http_methods(["POST"])
@login_required
def verify_subscription(request):
    """
    API endpoint to verify if a push notification subscription is still valid.
    
    Request body should be a JSON object with the endpoint to verify:
    {
        "endpoint": "https://fcm.googleapis.com/fcm/send/..."
    }
    """
    try:
        # Parse the request body
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        
        if not endpoint:
            return JsonResponse(
                {'error': 'Endpoint is required'}, 
                status=400
            )
        
        # Check if the subscription exists and is active
        subscription = PushNotificationSubscription.objects.filter(
            user=request.user,
            endpoint=endpoint,
            is_active=True
        ).first()
        
        if not subscription:
            return JsonResponse({
                'status': 'not_found',
                'valid': False
            })
        
        # Update the last seen timestamp
        subscription.last_seen = timezone.now()
        subscription.save(update_fields=['last_seen'])
        
        return JsonResponse({
            'status': 'success',
            'valid': True,
            'subscription_id': subscription.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON data'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Error verifying push subscription: {str(e)}")
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=500
        )

@require_http_methods(["POST"])
@login_required
def update_subscription(request):
    """
    API endpoint to update an existing push notification subscription.
    
    This is typically called when the browser's subscription has changed.
    
    Request body should be a JSON object with both old and new subscription data:
    {
        "old_endpoint": "https://fcm.googleapis.com/fcm/send/...",
        "new_subscription": {
            "endpoint": "https://fcm.googleapis.com/fcm/send/...",
            "keys": {
                "auth": "...",
                "p256dh": "..."
            }
        }
    }
    """
    try:
        # Parse the request body
        data = json.loads(request.body)
        old_endpoint = data.get('old_endpoint')
        new_subscription = data.get('new_subscription')
        
        if not old_endpoint or not new_subscription:
            return JsonResponse(
                {'error': 'Both old_endpoint and new_subscription are required'}, 
                status=400
            )
        
        # Validate the new subscription data
        if not all(key in new_subscription for key in ['endpoint', 'keys']):
            return JsonResponse(
                {'error': 'Invalid new subscription data'}, 
                status=400
            )
            
        if not all(key in new_subscription['keys'] for key in ['auth', 'p256dh']):
            return JsonResponse(
                {'error': 'Invalid new subscription keys'}, 
                status=400
            )
        
        # Delete the old subscription if it exists
        PushNotificationSubscription.objects.filter(
            user=request.user,
            endpoint=old_endpoint
        ).delete()
        
        # Create the new subscription
        subscription = PushNotificationSubscription.objects.create(
            user=request.user,
            endpoint=new_subscription['endpoint'],
            auth=new_subscription['keys']['auth'],
            p256dh=new_subscription['keys']['p256dh'],
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            ip_address=request.META.get('REMOTE_ADDR'),
            is_active=True,
            last_seen=timezone.now()
        )
        
        return JsonResponse({
            'status': 'success',
            'subscription_id': subscription.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Invalid JSON data'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Error updating push subscription: {str(e)}")
        return JsonResponse(
            {'error': 'Internal server error'}, 
            status=500
        )

@require_http_methods(["GET"])
@login_required
def get_public_key(request):
    """
    API endpoint to get the VAPID public key for push notifications.
    """
    return JsonResponse({
        'public_key': WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY']
    })

def send_push_notification(user, payload):
    """
    Helper function to send a push notification to a user.
    
    Args:
        user: The user to send the notification to
        payload: Dictionary containing the notification data
        
    Returns:
        dict: Results of the send operation
    """
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    # Get all active subscriptions for the user
    subscriptions = PushNotificationSubscription.objects.filter(
        user=user,
        is_active=True
    )
    
    if not subscriptions.exists():
        results['errors'].append('No active subscriptions found for user')
        return results
    
    # Send the notification to each subscription
    for subscription in subscriptions:
        try:
            # Add default values if not provided
            notification_payload = {
                'title': 'NewsHub',
                'icon': WEBPUSH_SETTINGS['DEFAULT_NOTIFICATION_ICON'],
                'badge': WEBPUSH_SETTINGS['DEFAULT_NOTIFICATION_BADGE'],
                'vibrate': WEBPUSH_SETTINGS['DEFAULT_NOTIFICATION_VIBRATE'],
                'renotify': WEBPUSH_SETTINGS['DEFAULT_NOTIFICATION_RENOTIFY'],
                'requireInteraction': WEBPUSH_SETTINGS['DEFAULT_NOTIFICATION_REQUIRE_INTERACTION'],
                'tag': WEBPUSH_SETTINGS['DEFAULT_NOTIFICATION_TAG'],
                'timestamp': timezone.now().timestamp() * 1000,  # Convert to milliseconds
                **payload
            }
            
            # Send the push notification
            webpush(
                subscription_info={
                    'endpoint': subscription.endpoint,
                    'keys': {
                        'auth': subscription.auth,
                        'p256dh': subscription.p256dh
                    }
                },
                data=json.dumps(notification_payload),
                vapid_private_key=WEBPUSH_SETTINGS['VAPID_PRIVATE_KEY'],
                vapid_claims={
                    'sub': f"mailto:{WEBPUSH_SETTINGS['VAPID_ADMIN_EMAIL']}"
                }
            )
            
            # Update the last seen timestamp
            subscription.last_seen = timezone.now()
            subscription.save(update_fields=['last_seen'])
            
            results['success'] += 1
            
        except WebPushException as e:
            # Handle specific WebPush errors
            error_msg = str(e)
            
            # Check if the subscription is no longer valid
            if '410' in error_msg:  # Gone
                logger.info(f"Deactivating invalid subscription: {subscription.id}")
                subscription.is_active = False
                subscription.save(update_fields=['is_active'])
            
            results['failed'] += 1
            results['errors'].append(f"WebPush error: {error_msg}")
            
        except Exception as e:
            # Handle other errors
            error_msg = str(e)
            logger.error(f"Error sending push notification: {error_msg}")
            results['failed'] += 1
            results['errors'].append(f"Error: {error_msg}")
    
    return results
