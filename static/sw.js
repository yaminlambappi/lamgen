const CACHE_NAME = 'lamgen-tools-v1';
const STATIC_ASSETS = [
    '/',
    '/tools/',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    
    // Ignore external APIs, ads, and dynamic user routes
    const url = new URL(event.request.url);
    if (url.pathname.startsWith('/tools/api/')) {
        return;
    }
    if (!url.pathname.startsWith('/static/') && !url.pathname.startsWith('/tools/')) {
        return;
    }

    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
                // Return cached immediately, fetch fresh in background (Stale-While-Revalidate)
                fetch(event.request).then(response => {
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(event.request, response);
                    });
                }).catch(() => {});
                return cachedResponse;
            }
            
            return fetch(event.request).then(response => {
                if (!response || response.status !== 200 || response.type !== 'basic') {
                    return response;
                }
                const responseToCache = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseToCache);
                });
                return response;
            });
        })
    );
});
