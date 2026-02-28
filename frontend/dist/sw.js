const CACHE_VERSION = 'pinprofit-v1';
const STATIC_ASSETS = ['/', '/index.html', '/manifest.json'];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_VERSION).then(cache => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_VERSION).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (e) => {
    const url = new URL(e.request.url);

    // API calls: Network First
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/')) {
        e.respondWith(
            fetch(e.request).catch(() =>
                new Response(JSON.stringify({ error: 'You are offline. Please reconnect.' }), {
                    headers: { 'Content-Type': 'application/json' },
                })
            )
        );
        return;
    }

    // Static assets: Cache First
    e.respondWith(
        caches.match(e.request).then(cached => {
            const fetchFromNetwork = fetch(e.request).then(response => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_VERSION).then(cache => cache.put(e.request, clone));
                }
                return response;
            });
            return cached || fetchFromNetwork;
        }).catch(() =>
            caches.match('/index.html')
        )
    );
});

// Push notifications
self.addEventListener('push', (e) => {
    const data = e.data?.json() || {};
    e.waitUntil(
        self.registration.showNotification(data.title || 'PinProfit', {
            body: data.body || '',
            icon: '/icons/icon-192.png',
            badge: '/icons/icon-192.png',
            tag: data.tag || 'pinprofit',
            data: { url: data.url || '/' },
        })
    );
});

self.addEventListener('notificationclick', (e) => {
    e.notification.close();
    e.waitUntil(
        clients.openWindow(e.notification.data.url || '/')
    );
});

// Background sync for failed API calls
self.addEventListener('sync', (e) => {
    if (e.tag === 'sync-pins') {
        e.waitUntil(syncPendingPins());
    }
});

async function syncPendingPins() {
    // Will be implemented in Phase 5
}
