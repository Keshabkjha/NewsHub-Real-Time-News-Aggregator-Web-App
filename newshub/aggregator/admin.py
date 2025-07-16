from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Article, Bookmark, TopicFollow, UserPreference, 
    KeywordAlert, AlertClick, Notification, 
    NotificationPreference, PushNotificationSubscription
)

User = get_user_model()


class UserActivityFilter(admin.SimpleListFilter):
    """Filter users based on their recent activity."""
    title = 'recent activity'
    parameter_name = 'recent_activity'
    
    def lookups(self, request, model_admin):
        return (
            ('today', 'Active today'),
            ('week', 'Active this week'),
            ('month', 'Active this month'),
            ('inactive_30', 'Inactive for 30+ days'),
            ('never', 'Never logged in'),
        )
    
    def queryset(self, request, queryset):
        now = timezone.now()
        
        if self.value() == 'today':
            today = now.date()
            return queryset.filter(last_login__date=today)
        elif self.value() == 'week':
            week_ago = now - timedelta(days=7)
            return queryset.filter(last_login__gte=week_ago)
        elif self.value() == 'month':
            month_ago = now - timedelta(days=30)
            return queryset.filter(last_login__gte=month_ago)
        elif self.value() == 'inactive_30':
            month_ago = now - timedelta(days=30)
            return queryset.filter(last_login__lt=month_ago)
        elif self.value() == 'never':
            return queryset.filter(last_login__isnull=True)


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    """Custom admin for the User model with enhanced functionality."""
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'is_active', 'is_staff', 'date_joined', 'last_login',
        'article_count', 'bookmark_count', 'notification_count'
    )
    list_filter = (UserActivityFilter, 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            article_count=Count('bookmark__article', distinct=True),
            bookmark_count=Count('bookmark', distinct=True),
            notification_count=Count('notifications', distinct=True),
        )
    
    def article_count(self, obj):
        return obj.article_count
    article_count.admin_order_field = 'article_count'
    
    def bookmark_count(self, obj):
        return obj.bookmark_count
    bookmark_count.admin_order_field = 'bookmark_count'
    
    def notification_count(self, obj):
        return obj.notification_count
    notification_count.admin_order_field = 'notification_count'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin configuration for the Article model."""
    list_display = ('title', 'source', 'category', 'published_at', 'bookmark_count')
    list_filter = ('category', 'source', 'published_at')
    search_fields = ('title', 'content', 'summary')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'published_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            bookmark_count=Count('bookmark')
        )
    
    def bookmark_count(self, obj):
        return obj.bookmark_count
    bookmark_count.admin_order_field = 'bookmark_count'


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    """Admin configuration for the Bookmark model."""
    list_display = ('user', 'article_title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'article__title')
    
    def article_title(self, obj):
        return obj.article.title
    article_title.short_description = 'Article'


@admin.register(TopicFollow)
class TopicFollowAdmin(admin.ModelAdmin):
    """Admin configuration for the TopicFollow model."""
    list_display = ('user', 'category')
    list_filter = ('category',)
    search_fields = ('user__username', 'category')


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """Admin configuration for the UserPreference model."""
    list_display = ('user', 'email_frequency', 'preferred_hour')
    list_filter = ('email_frequency',)
    search_fields = ('user__username',)


@admin.register(KeywordAlert)
class KeywordAlertAdmin(admin.ModelAdmin):
    """Admin configuration for the KeywordAlert model."""
    list_display = ('user', 'keyword', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'keyword')


@admin.register(AlertClick)
class AlertClickAdmin(admin.ModelAdmin):
    """Admin configuration for the AlertClick model."""
    list_display = ('user', 'article_title', 'keyword', 'clicked_at')
    list_filter = ('keyword', 'clicked_at')
    search_fields = ('user__username', 'article__title', 'keyword')
    
    def article_title(self, obj):
        return obj.article.title
    article_title.short_description = 'Article'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for the Notification model."""
    list_display = ('user', 'title', 'notification_type', 'read', 'created_at')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = queryset.update(read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin configuration for the NotificationPreference model."""
    list_display = ('user', 'email_digest_frequency', 'push_notifications_enabled')
    list_filter = ('email_digest_frequency', 'push_notifications_enabled')
    search_fields = ('user__username',)


@admin.register(PushNotificationSubscription)
class PushNotificationSubscriptionAdmin(admin.ModelAdmin):
    """Admin configuration for the PushNotificationSubscription model."""
    list_display = ('user', 'browser', 'os', 'device', 'last_seen')
    list_filter = ('browser', 'os', 'last_seen')
    search_fields = ('user__username', 'device')
    readonly_fields = ('created_at', 'last_seen')
    actions = ['cleanup_old_subscriptions']
    
    def cleanup_old_subscriptions(self, request, queryset):
        """Remove subscriptions older than 30 days."""
        from .models import PushNotificationSubscription
        deleted = PushNotificationSubscription.cleanup_old_subscriptions()
        self.message_user(request, f"Deleted {deleted[0]} old subscription(s).")
    cleanup_old_subscriptions.short_description = "Clean up old subscriptions (30+ days)"


# Custom admin site header
admin.site.site_header = "NewsHub Admin"
admin.site.site_title = "NewsHub Admin Portal"
admin.site.index_title = "Welcome to NewsHub Admin Portal"
