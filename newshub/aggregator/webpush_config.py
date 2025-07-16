"""
WebPush configuration for NewsHub.

This module handles the configuration for WebPush notifications, including VAPID keys.
"""

import os
from django.conf import settings
from py_vapid import Vapid

# Default VAPID settings
VAPID_PRIVATE_KEY = getattr(settings, 'VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = getattr(settings, 'VAPID_PUBLIC_KEY', '')
VAPID_CLAIMS = {
    "sub": f"mailto:{getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')}"
}

def get_vapid_credentials():
    """
    Get or generate VAPID credentials.
    
    Returns:
        dict: Dictionary containing VAPID public and private keys.
    """
    global VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY
    
    # If keys are not set in settings, try to load from environment variables
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
        VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
    
    # If still no keys, generate new ones (for development only)
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        if not settings.DEBUG:
            raise ValueError(
                "VAPID keys are required in production. "
                "Please set VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY in your settings or environment variables."
            )
        
        # Generate new VAPID keys for development
        print("Generating new VAPID keys for development...")
        vapid = Vapid()
        vapid.generate_keys()
        VAPID_PRIVATE_KEY = vapid.private_key
        VAPID_PUBLIC_KEY = vapid.public_key
        
        print(f"VAPID Public Key: {VAPID_PUBLIC_KEY}")
        print("Add these to your settings.py for production use:")
        print(f"VAPID_PUBLIC_KEY = '{VAPID_PUBLIC_KEY}'")
        print(f"VAPID_PRIVATE_KEY = '{VAPID_PRIVATE_KEY}'")
    
    return {
        'VAPID_PRIVATE_KEY': VAPID_PRIVATE_KEY,
        'VAPID_PUBLIC_KEY': VAPID_PUBLIC_KEY,
        'VAPID_CLAIMS': VAPID_CLAIMS
    }

# Initialize VAPID credentials when the module is imported
VAPID_CREDENTIALS = get_vapid_credentials()

def get_webpush_settings():
    """
    Get WebPush settings for the application.
    
    Returns:
        dict: WebPush settings dictionary.
    """
    return {
        'VAPID_PUBLIC_KEY': VAPID_CREDENTIALS['VAPID_PUBLIC_KEY'],
        'VAPID_PRIVATE_KEY': VAPID_CREDENTIALS['VAPID_PRIVATE_KEY'],
        'VAPID_ADMIN_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
        'DEFAULT_NOTIFICATION_ICON': getattr(
            settings, 
            'DEFAULT_NOTIFICATION_ICON', 
            f"{settings.STATIC_URL}images/logo-192x192.png"
        ),
        'DEFAULT_NOTIFICATION_BADGE': getattr(
            settings, 
            'DEFAULT_NOTIFICATION_BADGE', 
            f"{settings.STATIC_URL}images/logo-192x192.png"
        ),
        'DEFAULT_NOTIFICATION_IMAGE': getattr(
            settings, 
            'DEFAULT_NOTIFICATION_IMAGE', 
            f"{settings.STATIC_URL}images/logo-512x512.png"
        ),
        'DEFAULT_NOTIFICATION_VIBRATE': [200, 100, 200, 100, 200, 100, 200],
        'DEFAULT_NOTIFICATION_TAG': 'newshub-notification',
        'DEFAULT_NOTIFICATION_RENOTIFY': True,
        'DEFAULT_NOTIFICATION_REQUIRE_INTERACTION': False,
        'DEFAULT_NOTIFICATION_TIMESTAMP': None,
        'DEFAULT_NOTIFICATION_DIR': 'auto',  # 'auto', 'ltr', 'rtl'
        'DEFAULT_NOTIFICATION_LANG': 'en-US',
        'DEFAULT_NOTIFICATION_SILENT': False,
    }
