import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests and their response times.
    """
    def process_request(self, request):
        """
        Store the current time when the request comes in.
        """
        request.start_time = time.time()
        return None

    def process_response(self, request, response):
        """
        Log the request details and response time.
        """
        # Calculate response time
        total_time = time.time() - getattr(request, 'start_time', time.time())
        
        # Log the request details
        log_data = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'response_time': round(total_time * 1000, 2),  # in milliseconds
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self.get_client_ip(request),
            'user': str(getattr(request, 'user', 'Anonymous')),
            'query_params': dict(request.GET),
        }
        
        # Log at different levels based on status code
        if 500 <= response.status_code <= 599:
            logger.error('Server Error', extra=log_data)
        elif 400 <= response.status_code <= 499:
            logger.warning('Client Error', extra=log_data)
        else:
            logger.info('Request processed', extra=log_data)
            
        return response
    
    def process_exception(self, request, exception):
        """
        Log any exceptions that occur during request processing.
        """
        logger.error(
            'Unhandled exception in request processing',
            exc_info=exception,
            extra={
                'path': request.path,
                'method': request.method,
                'user': str(getattr(request, 'user', 'Anonymous')),
                'ip_address': self.get_client_ip(request),
            }
        )
        return None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process the view before it's called.
        """
        # Skip logging for static/media files and admin
        if request.path.startswith(settings.STATIC_URL) or \
           request.path.startswith(settings.MEDIA_URL) or \
           request.path.startswith('/admin/'):
            return None
        return None
    
    @staticmethod
    def get_client_ip(request):
        """
        Get the client's IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class NotificationMiddleware(MiddlewareMixin):
    """
    Middleware to add notification-related context to all requests.
    """
    def process_request(self, request):
        """
        Add notification context to the request.
        """
        # Skip for anonymous users
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
            
        # Add unread notification count to request
        cache_key = f'user_{request.user.id}_unread_count'
        unread_count = cache.get(cache_key)
        
        if unread_count is None:
            from .models import Notification
            unread_count = Notification.objects.filter(
                user=request.user, 
                read=False
            ).count()
            # Cache for 5 minutes
            cache.set(cache_key, unread_count, 300)
            
        request.unread_notification_count = unread_count
        
        # Add notification preferences to request
        if not hasattr(request, 'notification_preferences'):
            from .models import NotificationPreference
            request.notification_preferences = NotificationPreference.get_or_create_preferences(request.user)
        
        return None
    
    def process_template_response(self, request, response):
        """
        Add notification context to template responses.
        """
        # Only process if it's a template response
        if hasattr(response, 'context_data') and response.context_data is not None:
            # Add unread count to all template contexts
            if hasattr(request, 'unread_notification_count'):
                response.context_data['unread_notification_count'] = request.unread_notification_count
            
            # Add notification preferences to template context
            if hasattr(request, 'notification_preferences'):
                response.context_data['notification_preferences'] = request.notification_preferences
                
            # Add VAPID public key for WebPush
            if hasattr(settings, 'WEBPUSH_SETTINGS'):
                response.context_data['vapid_public_key'] = settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY', '')
        
        return response
