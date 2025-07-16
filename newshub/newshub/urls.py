"""
URL configuration for newshub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Custom admin site settings
admin.site.site_header = 'NewsHub Admin'
admin.site.site_title = 'NewsHub Administration'
admin.site.index_title = 'Welcome to NewsHub Admin'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Main app URLs
    path('', include('aggregator.urls')),
    
    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
    
    # WebPush
    path('webpush/', include('webpush.urls')),
    
    # Notifications
    path('notifications/', include('aggregator.urls_notifications', namespace='notifications')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
# Add debug toolbar if installed
if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
