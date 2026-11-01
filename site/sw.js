// Raqamli Tadqiqot V2 — network-first for public static pages only.
const CACHE_NAME = 'rt-site-v2-2026-11-01';
const OFFLINE_URL = '/offline.html';

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.add(OFFLINE_URL)).catch(() => {}).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(names => Promise.all(names.filter(name => name !== CACHE_NAME).map(name => caches.delete(name))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  // Never cache API, cross-origin, authenticated, or non-GET traffic.
  if (request.method !== 'GET' || url.origin !== self.location.origin ||
      url.pathname.startsWith('/api/') || url.pathname.startsWith('/admin') ||
      url.pathname.startsWith('/activate') || url.pathname.startsWith('/dashboard') ||
      request.headers.has('Authorization')) return;

  event.respondWith(
    fetch(request).then(response => {
      const cacheable = response && response.status === 200 && response.type === 'basic' &&
        !/private|no-store/i.test(response.headers.get('Cache-Control') || '') &&
        !response.headers.has('Set-Cookie');
      if (cacheable) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
      }
      return response;
    }).catch(() => caches.match(request).then(cached => {
      if (cached) return cached;
      if (request.mode === 'navigate') return caches.match(OFFLINE_URL);
      return Response.error();
    }))
  );
});
