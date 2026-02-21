const CACHE = 'xbox-ctrl-v1';
const ASSETS = ['/', '/style.css', '/app.js', '/manifest.json'];

self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', e => {
    // Only cache GET requests for same-origin static assets; pass through socket.io
    const url = new URL(e.request.url);
    if (e.request.method !== 'GET' || url.pathname.startsWith('/socket.io')) return;

    e.respondWith(
        caches.match(e.request).then(cached => cached || fetch(e.request))
    );
});
