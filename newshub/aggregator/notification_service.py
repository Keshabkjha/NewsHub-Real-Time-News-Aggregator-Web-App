import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Notification, NotificationPreference
from .email_service import EmailService
from .webpush_service import WebPushService

User = get_user_model()
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Unified service for handling all types of notifications.
    """
    
    @staticmethod
    def get_user_preferences(user):
        """
        Get or create notification preferences for a user.
        
        Args:
            user: User instance
            
        Returns:
            NotificationPreference: User's notification preferences
        """
        return NotificationPreference.get_or_create_preferences(user)
    
    @classmethod
    def send_notification(
        cls,
        user,
        title,
        message,
        notification_type='system',
        content_object=None,
        url=None,
        send_email=True,
        send_push=True,
        save_to_db=True
    ):
        """
        Send a notification to a user through multiple channels.
        
        Args:
            user: User instance to notify
            title (str): Notification title
            message (str): Notification message
            notification_type (str): Type of notification (system, alert, recommendation, etc.)
            content_object: Optional related object (e.g., Article, Comment)
            url (str, optional): URL to direct the user to
            send_email (bool): Whether to send an email notification
            send_push (bool): Whether to send a push notification
            save_to_db (bool): Whether to save the notification to the database
            
        Returns:
            Notification: The created notification instance or None if failed
        """
        if not user or not user.is_active:
            logger.warning(f"Cannot send notification to inactive or non-existent user: {user}")
            return None
            
        try:
            # Get user preferences
            preferences = cls.get_user_preferences(user)
            
            # Create notification in database
            notification = None
            if save_to_db:
                notification = Notification.create_notification(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    content_object=content_object,
                    url=url
                )
            
            # Send email if requested and user has email notifications enabled
            if send_email and user.email:
                email_pref = preferences.get_preferred_channel(notification_type)
                if email_pref == 'email' or (email_pref == 'push' and not preferences.push_notifications_enabled):
                    EmailService.send_notification_email(notification or {
                        'user': user,
                        'title': title,
                        'message': message,
                        'url': url,
                        'notification_type': notification_type
                    })
            
            # Send push notification if requested and user has push notifications enabled
            if send_push and preferences.push_notifications_enabled:
                push_pref = preferences.get_preferred_channel(notification_type)
                if push_pref in ['push', 'web']:
                    WebPushService.send_system_notification(
                        user_id=user.id,
                        title=title,
                        message=message,
                        url=url or (notification.get_absolute_url() if notification else None)
                    )
            
            return notification
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user.id}: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    def send_keyword_alert(cls, user, keyword, article):
        """
        Send a notification when a keyword alert is triggered.
        
        Args:
            user: User to notify
            keyword (str): The keyword that was matched
            article: Article that matched the keyword
            
        Returns:
            bool: True if notification was sent successfully
        """
        if not user or not user.is_active or not article:
            return False
            
        try:
            preferences = cls.get_user_preferences(user)
            
            # Create notification
            notification = cls.send_notification(
                user=user,
                title=f"New article matching '{keyword}'",
                message=f"{article.title}",
                notification_type='keyword_alert',
                content_object=article,
                url=f"/articles/{article.id}",
                send_email=preferences.keyword_alerts in ['email'],
                send_push=preferences.keyword_alerts in ['push', 'web']
            )
            
            # Additional push notification for keyword alerts
            if preferences.push_notifications_enabled and preferences.keyword_alerts in ['push', 'web']:
                WebPushService.send_keyword_alert(
                    user_id=user.id,
                    keyword=keyword,
                    article_id=article.id,
                    article_title=article.title,
                    article_source=article.source
                )
            
            return notification is not None
            
        except Exception as e:
            logger.error(f"Failed to send keyword alert to user {user.id}: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def send_daily_digest(cls, user, articles):
        """
        Send daily digest to a user.
        
        Args:
            user: User to send digest to
            articles (dict): Dictionary containing article lists
            
        Returns:
            bool: True if digest was sent successfully
        """
        if not user or not user.is_active or not user.email:
            return False
            
        try:
            preferences = cls.get_user_preferences(user)
            
            # Only send if user has daily digest enabled
            if preferences.email_digest_frequency != 'daily':
                return False
            
            # Send email
            email_sent = EmailService.send_daily_digest(user, articles)
            
            # Send push notification
            if preferences.push_notifications_enabled:
                total_articles = sum(len(lst) for lst in articles.values() if isinstance(lst, list))
                if total_articles > 0:
                    WebPushService.send_daily_digest_reminder(user.id, total_articles)
            
            return email_sent
            
        except Exception as e:
            logger.error(f"Failed to send daily digest to user {user.id}: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def send_weekly_digest(cls, user, stats, articles):
        """
        Send weekly digest to a user.
        
        Args:
            user: User to send digest to
            stats (dict): User statistics for the week
            articles (dict): Dictionary containing article lists
            
        Returns:
            bool: True if digest was sent successfully
        """
        if not user or not user.is_active or not user.email:
            return False
            
        try:
            preferences = cls.get_user_preferences(user)
            
            # Only send if user has weekly digest enabled
            if preferences.email_digest_frequency != 'weekly':
                return False
            
            # Send email
            email_sent = EmailService.send_weekly_digest(user, stats, articles)
            
            # Send push notification
            if preferences.push_notifications_enabled:
                WebPushService.send_weekly_summary(user.id, stats)
            
            return email_sent
            
        except Exception as e:
            logger.error(f"Failed to send weekly digest to user {user.id}: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def mark_notification_read(cls, notification_id, user):
        """
        Mark a notification as read.
        
        Args:
            notification_id (int): ID of the notification
            user: User who owns the notification
            
        Returns:
            bool: True if marked as read, False otherwise
        """
        try:
            notification = Notification.objects.get(id=notification_id, user=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to mark notification {notification_id} as read: {str(e)}")
            return False
    
    @classmethod
    def mark_all_notifications_read(cls, user):
        """
        Mark all notifications as read for a user.
        
        Args:
            user: User whose notifications to mark as read
            
        Returns:
            int: Number of notifications marked as read
        """
        try:
            updated = Notification.objects.filter(
                user=user,
                read=False
            ).update(read=True)
            return updated
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read for user {user.id}: {str(e)}")
            return 0
