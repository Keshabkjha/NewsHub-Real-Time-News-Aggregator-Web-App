self.addEventListener('push', function(event) {
    const data = event.data.json();
    const title = data.title || "NewsHub Notification";
    const options = {
        body: data.body,
        icon: '/static/aggregator/img/icon.png', // optional
        data: {
            url: data.url || "/"
        }
    };
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
