from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    """
    Model for storing user notifications.
    Can be used for various types of notifications including:
    - New articles matching user's interests
    - System announcements
    - Interactions with user's content
    """
    NOTIFICATION_TYPES = [
        ('keyword_alert', 'Keyword Alert'),
        ('new_article', 'New Article'),
        ('trending', 'Trending'),
        ('system', 'System'),
        ('recommendation', 'Recommendation'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Generic foreign key to link to various content types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    url = models.URLField(blank=True, null=True)
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    
    # Read status
    read = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type.upper()}: {self.title}"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        if not self.read:
            self.read = True
            self.save(update_fields=['read', 'updated_at'])
    
    def mark_as_unread(self):
        """Mark the notification as unread."""
        if self.read:
            self.read = False
            self.save(update_fields=['read', 'updated_at'])
    
    @classmethod
    def get_unread_count(cls, user):
        """Get the count of unread notifications for a user."""
        return cls.objects.filter(user=user, read=False).count()
    
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
        """Helper method to create a notification."""
        content_type = None
        object_id = None
        
        if content_object is not None:
            content_type = ContentType.objects.get_for_model(content_object)
            object_id = content_object.pk
        
        return cls.objects.create(
            user=user,
            content_type=content_type,
            object_id=object_id,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url
        )


class NotificationPreference(models.Model):
    """
    Model for storing user preferences for different types of notifications.
    """
    NOTIFICATION_CHANNELS = [
        ('email', 'Email'),
        ('web', 'Web'),
        ('push', 'Push Notification'),
        ('none', 'None'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Notification type preferences
    keyword_alerts = models.CharField(
        max_length=10,
        choices=NOTIFICATION_CHANNELS,
        default='push',
        help_text='How to be notified about keyword alerts'
    )
    
    recommended_articles = models.CharField(
        max_length=10,
        choices=NOTIFICATION_CHANNELS,
        default='email',
        help_text='How to be notified about recommended articles'
    )
    
    trending_articles = models.CharField(
        max_length=10,
        choices=NOTIFICATION_CHANNELS,
        default='web',
        help_text='How to be notified about trending articles'
    )
    
    system_messages = models.CharField(
        max_length=10,
        choices=NOTIFICATION_CHANNELS,
        default='web',
        help_text='How to be notified about system messages'
    )
    
    # Email preferences
    email_digest_frequency = models.CharField(
        max_length=10,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('never', 'Never'),
        ],
        default='daily',
        help_text='How often to receive email digests'
    )
    
    email_digest_time = models.TimeField(
        default='08:00',
        help_text='Preferred time to receive email digests'
    )
    
    # Push notification preferences
    push_notifications_enabled = models.BooleanField(
        default=True,
        help_text='Enable push notifications'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    
    @classmethod
    def get_or_create_preferences(cls, user):
        """Get or create notification preferences for a user."""
        preferences, created = cls.objects.get_or_create(user=user)
        return preferences
    
    def get_preferred_channel(self, notification_type):
        """Get the preferred notification channel for a notification type."""
        channel_map = {
            'keyword_alert': self.keyword_alerts,
            'recommendation': self.recommended_articles,
            'trending': self.trending_articles,
            'system': self.system_messages,
        }
        return channel_map.get(notification_type, 'web')
    
    def should_send_email(self, notification_type):
        """Check if an email should be sent for the given notification type."""
        channel = self.get_preferred_channel(notification_type)
        return channel == 'email' or (channel == 'push' and not self.push_notifications_enabled)
    
    def should_send_push(self, notification_type):
        """Check if a push notification should be sent for the given notification type."""
        if not self.push_notifications_enabled:
            return False
        channel = self.get_preferred_channel(notification_type)
        return channel == 'push' or channel == 'web'


class PushNotificationSubscription(models.Model):
    """
    Model for storing WebPush notification subscriptions for users.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    
    # WebPush subscription data
    endpoint = models.URLField(max_length=500)
    auth = models.CharField(max_length=100)
    p256dh = models.CharField(max_length=100)
    
    # Browser/device info
    browser = models.CharField(max_length=50, blank=True, null=True)
    device = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Push Notification Subscription'
        verbose_name_plural = 'Push Notification Subscriptions'
        unique_together = ('user', 'endpoint')
    
    def __str__(self):
        return f"Push subscription for {self.user.username} ({self.device or 'Unknown device'})"
    
    def update_last_seen(self):
        """Update the last seen timestamp."""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
    
    @classmethod
    def cleanup_old_subscriptions(cls, days=30):
        """Remove old subscriptions that haven't been seen in the specified number of days."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(last_seen__lt=cutoff_date).delete()
