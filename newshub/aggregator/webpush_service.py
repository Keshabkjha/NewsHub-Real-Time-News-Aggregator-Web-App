import json
import logging
from django.conf import settings
from django.urls import reverse
from webpush import send_user_notification
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)

class WebPushService:
    """
    Service for sending WebPush notifications to users' browsers.
    """
    
    @staticmethod
    def send_notification(user_id, title, message, url=None, icon=None, ttl=86400):
        """
        Send a WebPush notification to a specific user.
        
        Args:
            user_id (int): ID of the user to notify
            title (str): Notification title
            message (str): Notification message
            url (str, optional): URL to open when notification is clicked
            icon (str, optional): URL of the notification icon
            ttl (int): Time to live in seconds (default: 24 hours)
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            user = User.objects.get(id=user_id)
            
            # Check if user has push notifications enabled
            if not hasattr(user, 'notification_preferences') or \
               not user.notification_preferences.push_notifications_enabled:
                logger.debug(f"Push notifications disabled for user {user_id}")
                return False
            
            # Prepare notification payload
            payload = {
                'head': title,
                'body': message,
                'icon': icon or f"{settings.STATIC_URL}images/logo-192x192.png",
                'url': url or settings.SITE_URL,
            }
            
            # Send the notification
            send_user_notification(
                user=user,
                payload=payload,
                ttl=ttl
            )
            
            logger.info(f"WebPush notification sent to user {user_id}: {title}")
            return True
            
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to send WebPush notification to user {user_id}: {str(e)}")
            return False
    
    @classmethod
    def send_keyword_alert(cls, user_id, keyword, article_id, article_title, article_source):
        """
        Send a WebPush notification for a keyword alert match.
        
        Args:
            user_id (int): ID of the user to notify
            keyword (str): The keyword that was matched
            article_id (int): ID of the matching article
            article_title (str): Title of the article
            article_source (str): Source of the article
            
        Returns:
            bool: True if notification was sent successfully
        """
        title = f"🔔 New article matching '{keyword}'"
        message = f"{article_title[:100]}{'...' if len(article_title) > 100 else ''}"
        url = f"{settings.SITE_URL}{reverse('article_detail', args=[article_id])}"
        
        return cls.send_notification(
            user_id=user_id,
            title=title,
            message=message,
            url=url
        )
    
    @classmethod
    def send_daily_digest_reminder(cls, user_id, article_count):
        """
        Send a WebPush reminder about the daily digest.
        
        Args:
            user_id (int): ID of the user to notify
            article_count (int): Number of new articles in the digest
            
        Returns:
            bool: True if notification was sent successfully
        """
        title = "📰 Your Daily Digest is Ready!"
        message = f"Check out {article_count} new articles we've picked for you today."
        url = f"{settings.SITE_URL}{reverse('home')}"
        
        return cls.send_notification(
            user_id=user_id,
            title=title,
            message=message,
            url=url
        )
    
    @classmethod
    def send_weekly_summary(cls, user_id, stats):
        """
        Send a WebPush notification with weekly summary.
        
        Args:
            user_id (int): ID of the user to notify
            stats (dict): User statistics for the week
            
        Returns:
            bool: True if notification was sent successfully
        """
        title = "📊 Your Weekly Reading Summary"
        message = f"You've read {stats.get('article_count', 0)} articles across {stats.get('category_count', 0)} categories this week!"
        url = f"{settings.SITE_URL}{reverse('dashboard')}"
        
        return cls.send_notification(
            user_id=user_id,
            title=title,
            message=message,
            url=url
        )
    
    @classmethod
    def send_system_notification(cls, user_id, title, message, url=None):
        """
        Send a system notification via WebPush.
        
        Args:
            user_id (int): ID of the user to notify
            title (str): Notification title
            message (str): Notification message
            url (str, optional): URL to open when notification is clicked
            
        Returns:
            bool: True if notification was sent successfully
        """
        return cls.send_notification(
            user_id=user_id,
            title=title,
            message=message,
            url=url
        )
    
    @classmethod
    def cleanup_expired_subscriptions(cls, days_inactive=30):
        """
        Clean up expired WebPush subscriptions.
        
        Args:
            days_inactive (int): Number of days after which a subscription is considered inactive
            
        Returns:
            tuple: (deleted_count, total_checked)
        """
        from .models import PushNotificationSubscription
        
        cutoff_date = timezone.now() - timedelta(days=days_inactive)
        expired_subs = PushNotificationSubscription.objects.filter(
            last_seen__lt=cutoff_date
        )
        
        deleted_count = expired_subs.count()
        expired_subs.delete()
        
        logger.info(f"Cleaned up {deleted_count} expired WebPush subscriptions")
        return deleted_count
