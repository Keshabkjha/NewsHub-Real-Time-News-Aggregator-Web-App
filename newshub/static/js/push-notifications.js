/**
 * Push notification handling for NewsHub
 * 
 * This script handles:
 * - Requesting notification permission
 * - Registering a service worker
 * - Subscribing and unsubscribing from push notifications
 * - Handling incoming push notifications
 */

class PushNotificationManager {
    constructor() {
        this.serviceWorkerRegistration = null;
        this.isSubscribed = false;
        this.publicVapidKey = document.querySelector('meta[name="vapid-public-key"]')?.content;
        this.subscribeButton = document.getElementById('enable-push-btn');
        this.unsubscribeButton = document.getElementById('disable-push-btn');
        this.notificationPermission = 'default';
        
        this.initialize();
    }
    
    async initialize() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.warn('Push notifications are not supported in this browser');
            this.updateUIForUnsupported();
            return;
        }
        
        try {
            // Register service worker
            this.serviceWorkerRegistration = await navigator.serviceWorker.register('/sw.js');
            console.log('Service Worker registered');
            
            // Check current subscription status
            await this.checkSubscription();
            
            // Set up UI event listeners
            this.setupEventListeners();
            
            // Listen for push events
            navigator.serviceWorker.addEventListener('message', this.handlePushMessage.bind(this));
            
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            this.updateUIForError('Failed to register service worker');
        }
    }
    
    async checkSubscription() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            this.isSubscribed = !(subscription === null);
            this.updateUIForSubscriptionState();
            
            // If we're subscribed, verify with the server
            if (this.isSubscribed) {
                await this.verifySubscriptionWithServer(subscription);
            }
            
            return this.isSubscribed;
        } catch (error) {
            console.error('Error checking subscription:', error);
            this.updateUIForError('Error checking subscription status');
            return false;
        }
    }
    
    async subscribeToPush() {
        if (!this.publicVapidKey) {
            console.error('No VAPID public key found');
            this.updateUIForError('Server configuration error');
            return false;
        }
        
        try {
            // Request permission for notifications
            this.notificationPermission = await Notification.requestPermission();
            
            if (this.notificationPermission !== 'granted') {
                console.warn('Notification permission denied');
                this.updateUIForPermissionDenied();
                return false;
            }
            
            // Register push subscription
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.publicVapidKey)
            });
            
            // Send subscription to server
            const response = await fetch('/api/push/subscribe/', {
                method: 'POST',
                body: JSON.stringify(subscription),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Failed to save subscription');
            }
            
            this.isSubscribed = true;
            this.updateUIForSubscriptionState();
            console.log('Successfully subscribed to push notifications');
            return true;
            
        } catch (error) {
            console.error('Error subscribing to push notifications:', error);
            this.updateUIForError('Failed to subscribe to notifications');
            return false;
        }
    }
    
    async unsubscribeFromPush() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            if (subscription) {
                // Unsubscribe from push notifications
                const success = await subscription.unsubscribe();
                
                if (success) {
                    // Notify server about unsubscription
                    await fetch('/api/push/unsubscribe/', {
                        method: 'POST',
                        body: JSON.stringify({
                            endpoint: subscription.endpoint
                        }),
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCookie('csrftoken')
                        },
                        credentials: 'same-origin'
                    });
                    
                    this.isSubscribed = false;
                    this.updateUIForSubscriptionState();
                    console.log('Successfully unsubscribed from push notifications');
                    return true;
                }
            }
            
            return false;
            
        } catch (error) {
            console.error('Error unsubscribing from push notifications:', error);
            this.updateUIForError('Failed to unsubscribe from notifications');
            return false;
        }
    }
    
    async verifySubscriptionWithServer(subscription) {
        try {
            const response = await fetch('/api/push/verify/', {
                method: 'POST',
                body: JSON.stringify({
                    endpoint: subscription.endpoint
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                // If verification fails, the subscription might be invalid
                console.warn('Subscription verification failed, unsubscribing...');
                await this.unsubscribeFromPush();
                return false;
            }
            
            return true;
            
        } catch (error) {
            console.error('Error verifying subscription:', error);
            return false;
        }
    }
    
    handlePushMessage(event) {
        // Handle push message received while the app is in the foreground
        console.log('Push message received:', event.data);
        
        // You can customize how to handle the notification here
        const { title, body, icon, data } = event.data.json();
        
        // Show a notification
        if (this.notificationPermission === 'granted') {
            const notificationOptions = {
                body: body,
                icon: icon || '/static/images/logo-192x192.png',
                data: data || {}
            };
            
            // Show notification
            if (this.serviceWorkerRegistration) {
                this.serviceWorkerRegistration.showNotification(title, notificationOptions);
            } else {
                new Notification(title, notificationOptions);
            }
        }
    }
    
    setupEventListeners() {
        if (this.subscribeButton) {
            this.subscribeButton.addEventListener('click', () => this.subscribeToPush());
        }
        
        if (this.unsubscribeButton) {
            this.unsubscribeButton.addEventListener('click', () => this.unsubscribeFromPush());
        }
    }
    
    updateUIForSubscriptionState() {
        if (this.subscribeButton) {
            this.subscribeButton.style.display = this.isSubscribed ? 'none' : 'inline-block';
        }
        
        if (this.unsubscribeButton) {
            this.unsubscribeButton.style.display = this.isSubscribed ? 'inline-block' : 'none';
        }
    }
    
    updateUIForUnsupported() {
        const container = document.getElementById('push-notification-container');
        if (container) {
            container.innerHTML = `
                <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-yellow-700">
                                Push notifications are not supported in your browser. Please try using a modern browser like Chrome, Firefox, or Edge.
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    updateUIForPermissionDenied() {
        const container = document.getElementById('push-notification-container');
        if (container) {
            container.innerHTML = `
                <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-yellow-700">
                                Notification permission was denied. To enable push notifications, please update your browser settings.
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    updateUIForError(message) {
        const container = document.getElementById('push-notification-container');
        if (container) {
            container.innerHTML = `
                <div class="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-red-700">
                                ${message || 'An error occurred while setting up push notifications.'}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    // Helper function to convert base64 string to Uint8Array
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
            
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
    
    // Helper function to get CSRF token from cookies
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize push notification manager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if the push notification container exists
    if (document.getElementById('push-notification-container')) {
        window.pushNotificationManager = new PushNotificationManager();
    }
});
