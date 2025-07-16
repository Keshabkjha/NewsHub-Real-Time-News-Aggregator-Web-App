import json
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings

User = get_user_model()

class NotificationPreference(models.Model):
    """
    Model to store user's notification preferences.
    """
    NOTIFICATION_TYPES = [
        ('system', 'System Notifications'),
        ('keyword_alert', 'Keyword Alerts'),
        ('daily_digest', 'Daily Digest'),
        ('weekly_digest', 'Weekly Digest'),
        ('recommendations', 'Article Recommendations'),
    ]
    
    CHANNEL_CHOICES = [
        ('none', 'None'),
        ('email', 'Email'),
        ('web', 'Browser'),
        ('push', 'Push Notification'),
    ]
    
    FREQUENCY_CHOICES = [
        ('none', 'Never'),
        ('immediate', 'Immediately'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Global notification settings
    email_notifications_enabled = models.BooleanField(default=True)
    push_notifications_enabled = models.BooleanField(default=True)
    email_digest_frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='daily'
    )
    marketing_emails = models.BooleanField(
        default=True,
        help_text='Receive marketing and promotional emails'
    )
    
    # Per-notification type preferences
    preferences = models.JSONField(
        default=dict,
        help_text='JSON field storing per-notification type preferences'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    @classmethod
    def get_or_create_preferences(cls, user):
        """
        Get or create notification preferences for a user.
        """
        if not user or not user.is_authenticated:
            return None
            
        preferences, created = cls.objects.get_or_create(user=user)
        if created:
            # Initialize default preferences for new users
            default_prefs = {
                'system': 'web',  # Default to web notifications for system messages
                'keyword_alert': 'email',  # Default to email for keyword alerts
                'daily_digest': 'email',   # Default to email for daily digests
                'weekly_digest': 'email',  # Default to email for weekly digests
                'recommendations': 'web',  # Default to web for recommendations
            }
            preferences.preferences = default_prefs
            preferences.save()
            
        return preferences
    
    def get_preferred_channel(self, notification_type):
        """
        Get the preferred notification channel for a given notification type.
        """
        return self.preferences.get(notification_type, 'none')
    
    def set_preferred_channel(self, notification_type, channel):
        """
        Set the preferred notification channel for a given notification type.
        """
        if notification_type in dict(self.NOTIFICATION_TYPES).keys():
            self.preferences[notification_type] = channel
            self.save()
            return True
        return False
    
    def is_notification_enabled(self, notification_type):
        """
        Check if a specific notification type is enabled for any channel.
        """
        return self.get_preferred_channel(notification_type) != 'none'


class Notification(models.Model):
    """
    Model to store user notifications.
    """
    NOTIFICATION_TYPES = [
        ('system', 'System Notification'),
        ('keyword_alert', 'Keyword Alert'),
        ('daily_digest', 'Daily Digest'),
        ('weekly_digest', 'Weekly Digest'),
        ('recommendation', 'Article Recommendation'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    
    # Generic foreign key to link to any model
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # URL to redirect to when notification is clicked
    url = models.URLField(blank=True, null=True)
    
    # Tracking
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"
    
    def mark_as_read(self):
        """
        Mark this notification as read.
        """
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])
    
    def get_absolute_url(self):
        """
        Get the URL to redirect to when this notification is clicked.
        """
        if self.url:
            return self.url
            
        # Default URLs based on notification type
        if self.notification_type == 'keyword_alert' and self.content_object:
            return f"/articles/{self.content_object.id}/"
            
        return "/notifications/"
    
    @classmethod
    def create_notification(
        cls, 
        user, 
        title, 
        message, 
        notification_type='system',
        content_object=None,
        url=None
    ):
        """
        Helper method to create a new notification.
        """
        content_type = None
        object_id = None
        
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.id
            
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            content_type=content_type,
            object_id=object_id,
            url=url
        )


class PushNotificationSubscription(models.Model):
    """
    Model to store WebPush notification subscriptions for users.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    
    # Browser information
    endpoint = models.URLField(max_length=500)
    auth = models.CharField(max_length=100)
    p256dh = models.CharField(max_length=100)
    
    # User agent and IP for security
    user_agent = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Push Notification Subscription'
        verbose_name_plural = 'Push Notification Subscriptions'
        unique_together = ('user', 'endpoint')
    
    def __str__(self):
        return f"Push subscription for {self.user.username}"
    
    def get_subscription_info(self):
        """
        Get the subscription info in the format expected by pywebpush.
        """
        return {
            'endpoint': self.endpoint,
            'keys': {
                'auth': self.auth,
                'p256dh': self.p256dh,
            }
        }
    
    def update_last_seen(self):
        """
        Update the last_seen timestamp.
        """
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
    
    @classmethod
    def create_or_update_subscription(
        cls, 
        user, 
        subscription_data,
        user_agent='',
        ip_address=None
    ):
        """
        Create or update a push notification subscription.
        """
        try:
            endpoint = subscription_data.get('endpoint')
            keys = subscription_data.get('keys', {})
            
            subscription, created = cls.objects.update_or_create(
                user=user,
                endpoint=endpoint,
                defaults={
                    'auth': keys.get('auth', ''),
                    'p256dh': keys.get('p256dh', ''),
                    'user_agent': user_agent[:500],
                    'ip_address': ip_address,
                    'is_active': True,
                }
            )
            
            return subscription, created
            
        except Exception as e:
            # Log the error but don't crash
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating/updating push subscription: {str(e)}")
            return None, False
