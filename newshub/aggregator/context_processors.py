from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

def vapid_key(request):
    """
    Add WebPush VAPID public key to template context.
    """
    return {'vapid_public_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY']}

def notification_count(request):
    """
    Add notification-related data to template context.
    """
    if not request.user.is_authenticated:
        return {}
        
    # Get unread notifications count
    unread_count = 0
    if hasattr(request.user, 'notifications'):
        unread_count = request.user.notifications.filter(read=False).count()
    
    # Get recent alerts
    recent_alerts = []
    if hasattr(request.user, 'keywordalerts'):
        recent_alerts = request.user.keywordalerts.order_by('-created_at')[:5]
    
    # Get user's followed topics
    followed_topics = []
    if hasattr(request.user, 'topicfollows'):
        followed_topics = request.user.topicfollows.values_list('category', flat=True)
    
    # Get user's recent activity
    recent_activity = {}
    if hasattr(request.user, 'bookmarks'):
        recent_activity['recent_bookmarks'] = request.user.bookmarks.select_related('article').order_by('-created_at')[:3]
    
    return {
        'unread_notification_count': unread_count,
        'recent_alerts': recent_alerts,
        'followed_topics': followed_topics,
        **recent_activity,
    }
