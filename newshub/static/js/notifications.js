/**
 * NewsHub Notifications
 * Handles all notification-related functionality including push notifications, UI updates, and interactions
 */

class NotificationManager {
    constructor() {
        this.config = window.notificationConfig || {};
        this.isSubscribed = false;
        this.registration = null;
        this.pushButton = null;
        this.unreadCount = 0;
        
        // Initialize notification manager
        this.initialize();
    }

    /**
     * Initialize the notification manager
     */
    async initialize() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize push notifications if supported and user is authenticated
        if (this.config.user?.isAuthenticated) {
            await this.initializePushNotifications();
        }
        
        // Update UI based on current state
        this.updateUI();
    }
    
    /**
     * Set up event listeners for notification interactions
     */
    setupEventListeners() {
        // Mark notification as read when clicked
        document.addEventListener('click', (e) => {
            const markReadBtn = e.target.closest('[data-mark-read]');
            const deleteBtn = e.target.closest('[data-delete-notification]');
            const markAllReadBtn = e.target.closest('[data-mark-all-read]');
            
            if (markReadBtn) {
                this.markAsRead(markReadBtn.dataset.markRead);
            } else if (deleteBtn) {
                this.deleteNotification(deleteBtn.dataset.deleteNotification);
            } else if (markAllReadBtn) {
                this.markAllAsRead();
            }
        });
        
        // Notification filter form submission
        const filterForm = document.getElementById('notification-filter-form');
        if (filterForm) {
            filterForm.addEventListener('submit', (e) => {
                // Add loading state
                const submitBtn = filterForm.querySelector('button[type="submit"]');
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Filtering...
                `;
                
                // Submit the form
                filterForm.submit();
            });
        }
    }
    
    /**
     * Initialize push notifications
     */
    async initializePushNotifications() {
        // Check for service worker support
        if (!('serviceWorker' in navigator)) {
            console.warn('Service workers are not supported by this browser');
            return;
        }

        // Check for push notification support
        if (!('PushManager' in window)) {
            console.warn('Push notifications are not supported by this browser');
            return;
        }
        
        try {
            // Register service worker
            this.registration = await navigator.serviceWorker.register('/sw.js');
            console.log('ServiceWorker registration successful');
            
            // Check current subscription status
            await this.updatePushSubscriptionStatus();
            
            // Set up push notification button if it exists
            this.setupPushButton();
            
        } catch (error) {
            console.error('ServiceWorker registration failed:', error);
            this.showToast('Failed to initialize push notifications', 'error');
        }
    }
    
    /**
     * Set up the push notification button
     */
    setupPushButton() {
        this.pushButton = document.getElementById('push-subscription-button');
        
        if (!this.pushButton) return;
        
        this.pushButton.addEventListener('click', async () => {
            try {
                if (this.isSubscribed) {
                    await this.unsubscribeFromPush();
                } else {
                    await this.subscribeToPush();
                }
            } catch (error) {
                console.error('Error toggling push subscription:', error);
                this.showToast('Failed to update notification settings', 'error');
            }
        });
        
        this.updatePushButtonState(this.isSubscribed ? 'subscribed' : 'unsubscribed');
    }
    
    /**
     * Update the push subscription status
     */
    async updatePushSubscriptionStatus() {
        if (!this.registration) return false;
        
        try {
            const subscription = await this.registration.pushManager.getSubscription();
            this.isSubscribed = !(subscription === null);
            this.updatePushButtonState(this.isSubscribed ? 'subscribed' : 'unsubscribed');
            return this.isSubscribed;
        } catch (error) {
            console.error('Error checking push subscription status:', error);
            this.updatePushButtonState('error');
            return false;
        }
    }
    
    /**
     * Subscribe to push notifications
     */
    async subscribeToPush() {
        if (this.isSubscribed) return;
        
        this.updatePushButtonState('loading');
        
        try {
            // Request permission for notifications
            const permission = await Notification.requestPermission();
            
            if (permission !== 'granted') {
                throw new Error('Permission not granted for notifications');
            }
            
            // Get the server's public key
            const response = await fetch(this.config.apiEndpoints.getPublicKey);
            if (!response.ok) {
                throw new Error('Failed to get VAPID public key');
            }
            const vapidPublicKey = await response.text();
            
            // Subscribe to push notifications
            const subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(vapidPublicKey)
            });
            
            // Send subscription to server
            const saveResponse = await fetch(this.config.apiEndpoints.subscribe, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(subscription)
            });
            
            if (!saveResponse.ok) {
                throw new Error('Failed to save subscription');
            }
            
            // Update UI
            this.isSubscribed = true;
            this.updatePushButtonState('subscribed');
            this.showToast('Push notifications enabled', 'success');
            
        } catch (error) {
            console.error('Error subscribing to push:', error);
            this.updatePushButtonState('error');
            this.showToast('Failed to enable push notifications', 'error');
        }
    }
    
    /**
     * Unsubscribe from push notifications
     */
    async unsubscribeFromPush() {
        if (!this.isSubscribed) return;
        
        this.updatePushButtonState('loading');
        
        try {
            // Get the current subscription
            const subscription = await this.registration.pushManager.getSubscription();
            
            if (!subscription) {
                this.isSubscribed = false;
                this.updatePushButtonState('unsubscribed');
                return;
            }
            
            // Unsubscribe from push notifications
            await subscription.unsubscribe();
            
            // Notify the server
            const response = await fetch(this.config.apiEndpoints.unsubscribe, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.config.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(subscription.toJSON())
            });
            
            if (!response.ok) {
                throw new Error('Failed to remove subscription');
            }
            
            // Update UI
            this.isSubscribed = false;
            this.updatePushButtonState('unsubscribed');
            this.showToast('Push notifications disabled', 'info');
            
        } catch (error) {
            console.error('Error unsubscribing from push:', error);
            this.updatePushButtonState('error');
            this.showToast('Failed to disable push notifications', 'error');
        }
    }
    
    /**
     * Update the push button state
     * @param {string} state - The state to set (subscribed, unsubscribed, loading, error, unsupported)
     */
    updatePushButtonState(state) {
        if (!this.pushButton) return;
        
        // Reset button state
        this.pushButton.disabled = false;
        this.pushButton.innerHTML = '';
        this.pushButton.className = 'inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors';
        
        switch (state) {
            case 'subscribed':
                this.pushButton.innerHTML = `
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    Disable Push Notifications
                `;
                this.pushButton.classList.add('bg-green-600', 'text-white', 'hover:bg-green-700');
                break;
                
            case 'unsubscribed':
                this.pushButton.innerHTML = `
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                    </svg>
                    Enable Push Notifications
                `;
                this.pushButton.classList.add('bg-blue-600', 'text-white', 'hover:bg-blue-700');
                break;
                
            case 'loading':
                this.pushButton.disabled = true;
                this.pushButton.innerHTML = `
                    <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                `;
                this.pushButton.classList.add('bg-gray-500', 'text-white', 'cursor-not-allowed');
                break;
                
            case 'error':
                this.pushButton.innerHTML = 'Error - Click to Retry';
                this.pushButton.classList.add('bg-red-600', 'text-white', 'hover:bg-red-700');
                break;
                
            case 'unsupported':
                this.pushButton.disabled = true;
                this.pushButton.textContent = 'Push Not Supported';
                this.pushButton.classList.add('bg-gray-400', 'text-gray-700', 'cursor-not-allowed');
                break;
        }
    }
    
    /**
     * Mark a notification as read
     * @param {string} notificationId - The ID of the notification to mark as read
     */
    async markAsRead(notificationId) {
        if (!notificationId) return;
        
        try {
            const response = await fetch(`${this.config.apiEndpoints.markRead}/${notificationId}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.config.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const notificationItem = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.classList.remove('unread');
                    notificationItem.classList.add('read');
                    this.updateUnreadCount();
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error marking notification as read:', error);
            return false;
        }
    }
    
    /**
     * Mark all notifications as read
     */
    async markAllAsRead() {
        try {
            const response = await fetch(this.config.apiEndpoints.markAllRead, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.config.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                document.querySelectorAll('.notification-item.unread').forEach(item => {
                    item.classList.remove('unread');
                    item.classList.add('read');
                });
                this.updateUnreadCount();
                this.showToast('All notifications marked as read', 'success');
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
            this.showToast('Failed to mark all as read', 'error');
            return false;
        }
    }
    
    /**
     * Delete a notification
     * @param {string} notificationId - The ID of the notification to delete
     */
    async deleteNotification(notificationId) {
        if (!notificationId || !confirm('Are you sure you want to delete this notification?')) return;
        
        try {
            const response = await fetch(`${this.config.apiEndpoints.delete}/${notificationId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.config.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const notificationItem = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.style.opacity = '0';
                    setTimeout(() => notificationItem.remove(), 300);
                    this.updateUnreadCount();
                    this.showToast('Notification deleted', 'info');
                }
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error deleting notification:', error);
            this.showToast('Failed to delete notification', 'error');
            return false;
        }
    }
    
    /**
     * Update the unread count in the UI
     */
    updateUnreadCount() {
        const unreadItems = document.querySelectorAll('.notification-item.unread');
        this.unreadCount = unreadItems.length;
        
        // Update the unread count badge in the header
        const unreadBadge = document.getElementById('unread-count-badge');
        if (unreadBadge) {
            unreadBadge.textContent = this.unreadCount > 0 ? this.unreadCount : '';
            unreadBadge.classList.toggle('hidden', this.unreadCount === 0);
        }
        
        // Update the unread count in the menu
        const menuBadge = document.getElementById('menu-unread-count');
        if (menuBadge) {
            menuBadge.textContent = this.unreadCount > 0 ? `(${this.unreadCount})` : '';
        }
        
        // Update the empty state if needed
        this.updateEmptyState();
    }
    
    /**
     * Update the empty state visibility
     */
    updateEmptyState() {
        const notificationList = document.querySelector('.notification-list');
        const emptyState = document.querySelector('.empty-state');
        
        if (!notificationList || !emptyState) return;
        
        const hasNotifications = notificationList.children.length > 0;
        emptyState.classList.toggle('hidden', hasNotifications);
        notificationList.classList.toggle('hidden', !hasNotifications);
    }
    
    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - The type of toast (success, error, info, warning)
     */
    showToast(message, type = 'info') {
        // Check if toast container exists, if not create it
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'fixed bottom-4 right-4 z-50 space-y-2';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `flex items-center p-4 w-full max-w-xs rounded-lg shadow text-white ${this.getToastClass(type)}`;
        toast.role = 'alert';
        
        // Add icon based on type
        let iconPath = '';
        switch (type) {
            case 'success':
                iconPath = 'M5 13l4 4L19 7';
                break;
            case 'error':
                iconPath = 'M6 18L18 6M6 6l12 12';
                break;
            case 'warning':
                iconPath = 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z';
                break;
            default: // info
                iconPath = 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
        }
        
        toast.innerHTML = `
            <div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 rounded-lg">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${iconPath}"></path>
                </svg>
                <span class="sr-only">${type} icon</span>
            </div>
            <div class="ml-3 text-sm font-normal">${message}</div>
            <button type="button" class="ml-auto -mx-1.5 -my-1.5 text-white hover:text-gray-200 rounded-lg p-1.5 inline-flex h-8 w-8" data-dismiss="#toast">
                <span class="sr-only">Close</span>
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
            </button>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Auto-remove after delay
        setTimeout(() => {
            toast.classList.add('opacity-0', 'transition-opacity', 'duration-300');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
        
        // Add click handler to close button
        const closeButton = toast.querySelector('[data-dismiss="#toast"]');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                toast.remove();
            });
        }
    }
    
    /**
     * Get the appropriate CSS class for a toast based on its type
     * @param {string} type - The type of toast
     * @returns {string} - The CSS class
     */
    getToastClass(type) {
        const classes = {
            success: 'bg-green-600',
            error: 'bg-red-600',
            warning: 'bg-yellow-600',
            info: 'bg-blue-600'
        };
        return classes[type] || classes.info;
    }
    
    /**
     * Convert a base64 string to a Uint8Array
     * @param {string} base64String - The base64 string to convert
     * @returns {Uint8Array} - The converted Uint8Array
     */
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
    
    /**
     * Update the UI based on the current state
     */
    updateUI() {
        this.updateUnreadCount();
        this.setupPushButton();
    }
}

// Initialize the notification manager when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
});
