// Service Worker for NewsHub
// This service worker handles push notifications and offline functionality

const CACHE_NAME = 'newshub-v1';
const OFFLINE_URL = '/offline/';
const CACHE_URLS = [
    '/',
    '/static/css/styles.css',
    '/static/js/main.js',
    '/static/images/logo-192x192.png',
    '/static/images/logo-512x512.png',
    OFFLINE_URL
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker installing.');
    
    // Create a new cache and add all files to it
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Caching app shell and assets');
                return cache.addAll(CACHE_URLS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating.');
    
    // Remove previous cached data if it exists
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((cacheName) => cacheName !== CACHE_NAME)
                    .map((cacheName) => caches.delete(cacheName))
            );
        })
        .then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache, falling back to network
self.addEventListener('fetch', (event) => {
    // Skip cross-origin requests, like those to Google Fonts or the API
    if (!event.request.url.startsWith(self.location.origin) || 
        event.request.url.includes('/api/')) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached response if found
                if (response) {
                    return response;
                }
                
                // Otherwise, fetch from network
                return fetch(event.request)
                    .then((response) => {
                        // Check if we received a valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clone the response
                        const responseToCache = response.clone();
                        
                        // Cache the response for future use
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });
                        
                        return response;
                    })
                    .catch(() => {
                        // If both cache and network fail, show offline page
                        if (event.request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }
                    });
            })
    );
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
    console.log('Push event received:', event);
    
    let notificationData = { title: 'NewsHub', body: 'You have a new notification' };
    
    // Parse the push message data
    if (event.data) {
        try {
            notificationData = event.data.json();
        } catch (e) {
            console.error('Error parsing push data:', e);
            notificationData.body = event.data.text();
        }
    }
    
    // Ensure we have the required notification permission
    event.waitUntil(
        self.registration.showNotification(notificationData.title, {
            body: notificationData.body,
            icon: notificationData.icon || '/static/images/logo-192x192.png',
            badge: '/static/images/logo-192x192.png',
            image: notificationData.image,
            data: notificationData.data || {},
            vibrate: [200, 100, 200, 100, 200, 100, 200],
            tag: notificationData.tag || 'newshub-notification',
            ...(notificationData.actions ? { actions: notificationData.actions } : {})
        })
    );
});

// Notification click event - handle when a notification is clicked
self.addEventListener('notificationclick', (event) => {
    console.log('Notification click received:', event);
    
    // Close the notification
    event.notification.close();
    
    // Handle the notification click action
    if (event.action) {
        // Handle custom actions if any
        console.log('Notification action:', event.action);
    } else {
        // Default action - open the URL from the notification data or the app
        const url = event.notification.data.url || '/';
        
        // Open or focus the app
        event.waitUntil(
            clients.matchAll({ type: 'window' })
                .then((clientList) => {
                    // Check if there's already a window/tab open with the app
                    for (const client of clientList) {
                        if (client.url === url && 'focus' in client) {
                            return client.focus();
                        }
                    }
                    
                    // If no matching client is found, open a new window
                    if (clients.openWindow) {
                        return clients.openWindow(url);
                    }
                })
        );
    }
});

// Background sync event - handle background sync for offline functionality
self.addEventListener('sync', (event) => {
    console.log('Background sync event:', event.tag);
    
    if (event.tag === 'sync-articles') {
        // Handle article synchronization
        event.waitUntil(syncArticles());
    }
});

// Push subscription change event - handle when the push subscription changes
self.addEventListener('pushsubscriptionchange', (event) => {
    console.log('Push subscription changed:', event);
    
    event.waitUntil(
        Promise.resolve()
            .then(() => {
                if (!event.newSubscription) {
                    // The user has unsubscribed
                    return Promise.resolve();
                }
                
                // Get the subscription details
                return event.newSubscription;
            })
            .then((subscription) => {
                if (!subscription) {
                    return Promise.resolve();
                }
                
                // Send the new subscription to the server
                return fetch('/api/push/update-subscription/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        old_endpoint: event.oldSubscription ? event.oldSubscription.endpoint : null,
                        new_subscription: subscription
                    })
                });
            })
            .catch((error) => {
                console.error('Error handling subscription change:', error);
            })
    );
});

// Helper function to sync articles in the background
function syncArticles() {
    // Implement article synchronization logic here
    console.log('Syncing articles in the background...');
    
    // Return a promise that resolves when the sync is complete
    return Promise.resolve();
}

// Message event - handle messages from the main thread
self.addEventListener('message', (event) => {
    console.log('Message received in service worker:', event.data);
    
    // Handle different types of messages
    switch (event.data.type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'CLEAR_CACHE':
            caches.delete(CACHE_NAME)
                .then(() => {
                    console.log('Cache cleared');
                });
            break;
            
        default:
            console.log('Unknown message type:', event.data.type);
    }
});
