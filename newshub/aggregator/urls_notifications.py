from django.urls import path
from . import views_notifications
from . import api_views

app_name = 'notifications'

urlpatterns = [
    # Notification list and detail views
    path('', views_notifications.notification_list, name='list'),
    path('<int:notification_id>/', views_notifications.notification_detail, name='detail'),
    path('<int:notification_id>/read/', views_notifications.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views_notifications.mark_all_read, name='mark_all_read'),
    
    # Notification preferences
    path('preferences/', views_notifications.notification_preferences, name='preferences'),
    
    # Push notification subscription management
    path('push/subscribe/', views_notifications.save_push_subscription, name='push_subscribe'),
    path('push/unsubscribe/', views_notifications.remove_push_subscription, name='push_unsubscribe_all'),
    path('push/unsubscribe/<int:subscription_id>/', views_notifications.remove_push_subscription, name='push_unsubscribe'),
    
    # API endpoints
    path('api/unread-count/', views_notifications.get_unread_count, name='api_unread_count'),
    
    # Push notification API endpoints
    path('api/push/subscribe/', api_views.subscribe_push, name='api_push_subscribe'),
    path('api/push/unsubscribe/', api_views.unsubscribe_push, name='api_push_unsubscribe'),
    path('api/push/verify/', api_views.verify_subscription, name='api_push_verify'),
    path('api/push/update-subscription/', api_views.update_subscription, name='api_push_update'),
    path('api/push/public-key/', api_views.get_public_key, name='api_push_public_key'),
]
