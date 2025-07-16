function subscribeUser() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        alert("Your browser doesn't support push notifications.");
        return;
    }

    Notification.requestPermission().then(permission => {
        if (permission !== 'granted') {
            alert("Notification permission denied.");
            return;
        }

        navigator.serviceWorker.register('/static/aggregator/sw.js').then(reg => {
            const vapidPublicKey = "{{ vapid_public_key }}";
            const convertedKey = urlBase64ToUint8Array(vapidPublicKey);

            reg.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedKey
            }).then(subscription => {
                fetch("/webpush/save_information/", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(subscription)
                });
                alert("Push notifications enabled!");
            });
        });
    });
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
    const raw = atob(base64);
    return new Uint8Array([...raw].map(char => char.charCodeAt(0)));
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const part = value.split(`; ${name}=`);
    return part.length === 2 ? part.pop().split(';').shift() : '';
}
