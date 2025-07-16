import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service for sending various types of emails in the application.
    """
    
    @staticmethod
    def _send_email(subject, to_email, template_name, context=None):
        """
        Base method to send an email using a template.
        
        Args:
            subject (str): Email subject
            to_email (str): Recipient email address
            template_name (str): Template name (without .html extension)
            context (dict): Context variables for the template
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if context is None:
            context = {}
            
        # Add common context variables
        context.update({
            'site_url': settings.SITE_URL,
            'current_year': timezone.now().year,
            'unsubscribe_url': f"{settings.SITE_URL}{reverse('email_preferences')}",
            'unsubscribe_all_url': f"{settings.SITE_URL}{reverse('unsubscribe_all')}?email={to_email}",
        })
        
        # Render HTML content
        html_content = render_to_string(f'emails/{template_name}.html', context)
        
        try:
            # Create email message
            msg = EmailMultiAlternatives(
                subject=subject,
                body=html_content,  # Fallback for non-HTML email clients
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
                reply_to=[settings.DEFAULT_REPLY_TO_EMAIL],
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send(fail_silently=False)
            logger.info(f"Email sent to {to_email} with subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}. Error: {str(e)}")
            return False
    
    @classmethod
    def send_daily_digest(cls, user, articles):
        """
        Send daily digest email to a user.
        
        Args:
            user: User instance
            articles (dict): Dictionary containing article lists (trending, recommended, etc.)
            
        Returns:
            bool: True if email was sent successfully
        """
        subject = f"📰 Your Daily News Digest - {timezone.now().strftime('%A, %B %-d')}"
        
        context = {
            'user': user,
            'date': timezone.now(),
            **articles  # Unpack all article lists into the context
        }
        
        return cls._send_email(
            subject=subject,
            to_email=user.email,
            template_name='daily_digest',
            context=context
        )
    
    @classmethod
    def send_weekly_digest(cls, user, stats, articles):
        """
        Send weekly digest email to a user.
        
        Args:
            user: User instance
            stats (dict): User statistics for the week
            articles (dict): Dictionary containing article lists for the week
            
        Returns:
            bool: True if email was sent successfully
        """
        subject = f"📊 Your Weekly News Digest - {timezone.now().strftime('%b %-d, %Y')}"
        
        context = {
            'user': user,
            'start_date': timezone.now() - timezone.timedelta(days=7),
            'end_date': timezone.now(),
            **stats,
            **articles
        }
        
        return cls._send_email(
            subject=subject,
            to_email=user.email,
            template_name='weekly_digest',
            context=context
        )
    
    @classmethod
    def send_keyword_alert(cls, user, keyword, articles, alert_id, notification_frequency):
        """
        Send an email notification when new articles match a user's keyword alert.
        
        Args:
            user: User instance
            keyword (str): The keyword that was matched
            articles (list): List of Article instances that match the keyword
            alert_id (int): ID of the keyword alert
            notification_frequency (str): How often the user receives these alerts
            
        Returns:
            bool: True if email was sent successfully
        """
        subject = f"🔔 {len(articles)} new article(s) matching '{keyword}'"
        
        context = {
            'user': user,
            'keyword': keyword,
            'articles': articles,
            'alert_id': alert_id,
            'notification_frequency': notification_frequency,
        }
        
        return cls._send_email(
            subject=subject,
            to_email=user.email,
            template_name='keyword_alert',
            context=context
        )
    
    @classmethod
    def send_welcome_email(cls, user):
        """
        Send a welcome email to a new user.
        
        Args:
            user: Newly registered user
            
        Returns:
            bool: True if email was sent successfully
        """
        subject = "👋 Welcome to NewsHub - Start Exploring!"
        
        context = {
            'user': user,
        }
        
        return cls._send_email(
            subject=subject,
            to_email=user.email,
            template_name='welcome',
            context=context
        )
    
    @classmethod
    def send_password_reset_email(cls, user, reset_url):
        """
        Send a password reset email.
        
        Args:
            user: User who requested password reset
            reset_url: Password reset URL
            
        Returns:
            bool: True if email was sent successfully
        """
        subject = "🔑 Reset Your NewsHub Password"
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': int(settings.PASSWORD_RESET_TIMEOUT / 3600),  # Convert seconds to hours
        }
        
        return cls._send_email(
            subject=subject,
            to_email=user.email,
            template_name='password_reset',
            context=context
        )
    
    @classmethod
    def send_notification_email(cls, notification):
        """
        Send an email notification.
        
        Args:
            notification: Notification instance to send
            
        Returns:
            bool: True if email was sent successfully
        """
        subject = notification.title
        
        context = {
            'user': notification.user,
            'notification': notification,
            'content': notification.message,
            'action_url': notification.url,
        }
        
        return cls._send_email(
            subject=subject,
            to_email=notification.user.email,
            template_name='notification',
            context=context
        )
