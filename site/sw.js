// Release 2026-10-14.1: retire legacy cache-first behavior.
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil((async () => {
  for (const key of await caches.keys()) {
    if (key.startsWith('rt-monitor-')) await caches.delete(key);
  }
  await self.clients.claim();
  await self.registration.unregister();
})()));
