import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Article, User, KeywordAlert, UserPreference, Notification, NotificationPreference
from .services import NewsAPIService, NLPService
from .notification_service import NotificationService
from .email_service import EmailService
from .webpush_service import WebPushService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_articles_task(self, category=None):
    """
    Task to fetch articles from NewsAPI and process them.
    """
    try:
        news_service = NewsAPIService()
        nlp_service = NLPService()
        
        # Fetch articles from NewsAPI
        articles = news_service.fetch_articles(category=category)
        
        # Process each article
        for article_data in articles:
            try:
                # Check if article already exists
                if Article.objects.filter(url=article_data['url']).exists():
                    continue
                
                # Generate summary using NLP
                summary = nlp_service.generate_summary(article_data['content'])
                
                # Classify article category
                category = nlp_service.classify_category(
                    article_data['title'], 
                    article_data.get('description', '')
                )
                
                # Create article
                article = Article.objects.create(
                    title=article_data['title'],
                    url=article_data['url'],
                    source=article_data['source']['name'],
                    published_at=article_data['publishedAt'],
                    content=article_data['content'],
                    summary=summary,
                    category=category,
                    image_url=article_data.get('urlToImage', '')
                )
                
                # Check for keyword matches and send alerts
                check_keyword_matches.delay(article.id)
                
            except Exception as e:
                logger.error(f"Error processing article {article_data.get('url', 'unknown')}: {str(e)}", 
                            exc_info=True)
                continue
                
        return f"Successfully processed {len(articles)} articles"
        
    except Exception as e:
        logger.error(f"Error in fetch_articles_task: {str(e)}", exc_info=True)
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_keyword_matches(self, article_id):
    """
    Check if an article matches any user's keyword alerts and send notifications.
    """
    try:
        article = Article.objects.get(id=article_id)
        
        # Get all active keyword alerts
        keyword_alerts = KeywordAlert.objects.filter(is_active=True).select_related('user')
        
        # Group alerts by user to batch notifications
        user_alerts = {}
        for alert in keyword_alerts:
            try:
                # Check if keyword exists in title, content, or summary
                keyword = alert.keyword.lower()
                if (keyword in article.title.lower() or 
                    keyword in article.content.lower() or 
                    (article.summary and keyword in article.summary.lower())):
                    
                    if alert.user_id not in user_alerts:
                        user_alerts[alert.user_id] = []
                    user_alerts[alert.user_id].append(alert.keyword)
                    
            except Exception as e:
                logger.error(f"Error processing alert {alert.id}: {str(e)}", exc_info=True)
                continue
        
        # Send notifications for each user with matching keywords
        for user_id, keywords in user_alerts.items():
            try:
                # Get unique keywords
                unique_keywords = list(set(keywords))
                keywords_str = ", ".join(unique_keywords[:3])
                if len(unique_keywords) > 3:
                    keywords_str += f" and {len(unique_keywords) - 3} more"
                
                # Send notification
                NotificationService.send_keyword_alert(
                    user_id=user_id,
                    article=article,
                    keywords=unique_keywords,
                    title=f"New articles about {keywords_str}",
                    message=f"{article.title}\n{article.summary or ''}",
                    url=reverse('article_detail', args=[article.id]),
                )
                
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {str(e)}", exc_info=True)
                continue
                
        return f"Processed keyword matches for article {article_id}"
        
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found")
        return f"Article {article_id} not found"
    except Exception as e:
        logger.error(f"Error in check_keyword_matches: {str(e)}", exc_info=True)
        self.retry(exc=e)

@shared_task
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_notification(self, user_id, title, message, url, notification_type='info', related_object=None):
    """
    Send a notification to a user via multiple channels based on their preferences.
    
    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        url: URL to direct the user to when they click the notification
        notification_type: Type of notification (e.g., 'info', 'alert', 'recommendation')
        related_object: Optional related object (e.g., Article, User, etc.)
    """
    try:
        # Get the user
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        # Get or create notification preferences for the user
        preferences = NotificationPreference.get_or_create_preferences(user)
        
        # Determine which channels to use based on notification type and preferences
        channels = []
        
        # Get the channel preference for this notification type
        channel_pref = getattr(preferences, f"{notification_type}_channel", 'web')
        
        if channel_pref == 'email':
            channels.append('email')
        elif channel_pref == 'push':
            channels.append('push')
        elif channel_pref == 'both':
            channels.extend(['email', 'push'])
        else:  # 'web' or any other value
            channels.append('web')
        
        # Send notification via selected channels
        if 'email' in channels and user.email:
            try:
                EmailService.send_notification_email(
                    user=user,
                    title=title,
                    message=message,
                    url=url,
                    notification_type=notification_type
                )
            except Exception as e:
                logger.error(f"Error sending email notification to {user.email}: {str(e)}", exc_info=True)
        
        if 'push' in channels:
            try:
                WebPushService.send_notification(
                    user=user,
                    title=title,
                    message=message,
                    url=url,
                    notification_type=notification_type
                )
            except Exception as e:
                logger.error(f"Error sending push notification to user {user_id}: {str(e)}", exc_info=True)
        
        # Always create a web notification
        try:
            NotificationService.create_notification(
                user=user,
                title=title,
                message=message,
                url=url,
                notification_type=notification_type,
                related_object=related_object
            )
        except Exception as e:
            logger.error(f"Error creating web notification for user {user_id}: {str(e)}", exc_info=True)
            raise  # Re-raise to trigger retry
        
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error in send_notification: {str(e)}", exc_info=True)
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_daily_digest(self):
    """
    Send daily digest emails to users who have opted in.
    """
    try:
        # Get users who have daily digest enabled
        users = User.objects.filter(
            notification_preferences__email_digest_frequency='daily',
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        # Get date range for the digest (last 24 hours)
        start_date = timezone.now() - timedelta(days=1)
        
        # Get trending articles (most viewed in the last 24 hours)
        trending_articles = Article.objects.filter(
            published_at__gte=start_date
        ).annotate(
            view_count=Count('articleview')
        ).order_by('-view_count', '-published_at')[:5]
        
        # Get recommended articles (based on user preferences)
        # This is a simplified example - in a real app, you'd use a recommendation engine
        recommended_articles = Article.objects.filter(
            published_at__gte=start_date
        ).order_by('-published_at')[:5]
        
        # Get all categories for the digest
        all_categories = Article.CATEGORY_CHOICES
        
        # Track stats
        emails_sent = 0
        emails_failed = 0
        
        for user in users:
            try:
                # Get user's notification preferences
                preferences = NotificationPreference.get_or_create_preferences(user)
                
                # Skip if user has unsubscribed from all emails
                if not preferences.email_notifications_enabled:
                    continue
                
                # Get user's preferred categories
                user_categories = preferences.get_preferred_categories()
                
                # Filter articles by user's preferred categories
                category_articles = {}
                for category in user_categories:
                    category_articles[category] = Article.objects.filter(
                        category=category,
                        published_at__gte=start_date
                    ).order_by('-published_at')[:5]
                
                # Prepare email context
                context = {
                    'user': user,
                    'date': timezone.now().strftime('%A, %B %d, %Y'),
                    'trending_articles': trending_articles,
                    'recommended_articles': recommended_articles,
                    'category_articles': category_articles,
                    'site_url': settings.SITE_URL,
                    'unsubscribe_url': f"{settings.SITE_URL}/unsubscribe/{user.unsubscribe_token}/",
                    'preferences_url': f"{settings.SITE_URL}/notifications/preferences/"
                }
                
                # Send email using EmailService
                success = EmailService.send_daily_digest(
                    user=user,
                    context=context
                )
                
                if success:
                    emails_sent += 1
                    logger.info(f"Sent daily digest to {user.email}")
                    
                    # Send push notification reminder
                    try:
                        WebPushService.send_daily_digest_reminder(
                            user=user,
                            article_count=sum(len(articles) for articles in category_articles.values())
                        )
                    except Exception as e:
                        logger.error(f"Error sending push notification to {user.email}: {str(e)}", exc_info=True)
                        
                else:
                    emails_failed += 1
                    logger.warning(f"Failed to send daily digest to {user.email}")
                
            except Exception as e:
                emails_failed += 1
                logger.error(f"Error processing daily digest for {user.email}: {str(e)}", exc_info=True)
                continue
                
        return {
            'status': 'completed',
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'total_users': users.count()
        }
        
    except Exception as e:
        logger.error(f"Error in send_daily_digest: {str(e)}", exc_info=True)
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_weekly_digest(self):
    """
    Send weekly digest emails to users who have opted in.
    """
    try:
        # Get users who have weekly digest enabled
        users = User.objects.filter(
            notification_preferences__email_digest_frequency='weekly',
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        # Get date range for the digest (last 7 days)
        start_date = timezone.now() - timedelta(weeks=1)
        
        # Get most viewed articles of the week
        most_viewed = Article.objects.filter(
            published_at__gte=start_date
        ).annotate(
            view_count=Count('articleview')
        ).order_by('-view_count', '-published_at')[:10]
        
        # Get trending articles (most engagement in the last 7 days)
        trending_articles = Article.objects.filter(
            published_at__gte=start_date
        ).annotate(
            engagement=Count('articleview') + Count('bookmarks') * 2 + Count('comments') * 3
        ).order_by('-engagement', '-published_at')[:5]
        
        # Get recommended articles (based on user preferences)
        # This is a simplified example - in a real app, you'd use a recommendation engine
        recommended_articles = Article.objects.filter(
            published_at__gte=start_date
        ).order_by('-published_at')[:5]
        
        # Get most popular categories of the week
        popular_categories = Article.objects.filter(
            published_at__gte=start_date
        ).values('category').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Track stats
        emails_sent = 0
        emails_failed = 0
        
        for user in users:
            try:
                # Get user's notification preferences
                preferences = NotificationPreference.get_or_create_preferences(user)
                
                # Skip if user has unsubscribed from all emails
                if not preferences.email_notifications_enabled:
                    continue
                
                # Get user's reading history (if any)
                read_articles = user.article_views.filter(
                    created_at__gte=start_date
                ).values_list('article_id', flat=True)
                
                # Get user's reading stats
                reading_stats = {
                    'articles_read': len(read_articles),
                    'time_spent': user.article_views.filter(
                        created_at__gte=start_date
                    ).aggregate(total_time=Sum('time_spent'))['total_time'] or 0,
                    'favorite_category': user.article_views.filter(
                        created_at__gte=start_date
                    ).values('article__category').annotate(
                        count=Count('id')
                    ).order_by('-count').values_list('article__category', flat=True).first()
                }
                
                # Prepare email context
                context = {
                    'user': user,
                    'start_date': (timezone.now() - timedelta(weeks=1)).strftime('%B %d'),
                    'end_date': timezone.now().strftime('%B %d, %Y'),
                    'most_viewed': most_viewed,
                    'trending_articles': trending_articles,
                    'recommended_articles': recommended_articles,
                    'popular_categories': popular_categories,
                    'reading_stats': reading_stats,
                    'site_url': settings.SITE_URL,
                    'unsubscribe_url': f"{settings.SITE_URL}/unsubscribe/{user.unsubscribe_token}/",
                    'preferences_url': f"{settings.SITE_URL}/notifications/preferences/"
                }
                
                # Send email using EmailService
                success = EmailService.send_weekly_digest(
                    user=user,
                    context=context
                )
                
                if success:
                    emails_sent += 1
                    logger.info(f"Sent weekly digest to {user.email}")
                    
                    # Send push notification reminder
                    try:
                        WebPushService.send_weekly_summary(
                            user=user,
                            article_count=len(most_viewed)
                        )
                    except Exception as e:
                        logger.error(f"Error sending push notification to {user.email}: {str(e)}", exc_info=True)
                        
                else:
                    emails_failed += 1
                    logger.warning(f"Failed to send weekly digest to {user.email}")
                
            except Exception as e:
                emails_failed += 1
                logger.error(f"Error processing weekly digest for {user.email}: {str(e)}", exc_info=True)
                continue
                
        return {
            'status': 'completed',
            'emails_sent': emails_sent,
            'emails_failed': emails_failed,
            'total_users': users.count()
        }
        
    except Exception as e:
        logger.error(f"Error in send_weekly_digest: {str(e)}", exc_info=True)
        self.retry(exc=e)
