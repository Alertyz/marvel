// ═══════════════════════════════════════════════════════════
//  SERVICE WORKER — Offline-first Comic Reader
// ═══════════════════════════════════════════════════════════

const APP_CACHE = 'marvel-app-v1';
const IMG_CACHE = 'marvel-images-v1';
const API_CACHE = 'marvel-api-v1';

// App shell files to pre-cache
const APP_SHELL = ['/', '/manifest.json'];

// ── Install: cache app shell ──────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(APP_CACHE).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

// ── Activate: clean old caches ────────────────────────────
self.addEventListener('activate', (event) => {
  const keep = new Set([APP_CACHE, IMG_CACHE, API_CACHE]);
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => !keep.has(k)).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch strategy ────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Comic page images: cache-first (large, rarely change)
  if (url.pathname.match(/^\/api\/issues\/\d+\/page\/\d+$/)) {
    event.respondWith(cacheFirst(event.request, IMG_CACHE));
    return;
  }

  // API data (library, stats, etc.): network-first, fallback to cache
  if (url.pathname.startsWith('/api/')) {
    // Don't cache POST requests or sync endpoints writes
    if (event.request.method !== 'GET') return;
    event.respondWith(networkFirst(event.request, API_CACHE));
    return;
  }

  // App shell (HTML, manifest): network-first
  event.respondWith(networkFirst(event.request, APP_CACHE));
});

// ── Cache-first strategy (for images) ─────────────────────
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('', { status: 503, statusText: 'Offline' });
  }
}

// ── Network-first strategy (for API and shell) ────────────
async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(JSON.stringify({ offline: true }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

// ── Message handling for cache management ─────────────────
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CACHE_IMAGES') {
    // Pre-cache a batch of image URLs
    const urls = event.data.urls || [];
    event.waitUntil(
      caches.open(IMG_CACHE).then(async (cache) => {
        let cached = 0;
        for (const url of urls) {
          const exists = await cache.match(url);
          if (!exists) {
            try {
              const resp = await fetch(url);
              if (resp.ok) {
                await cache.put(url, resp);
                cached++;
              }
            } catch { /* skip */ }
          }
        }
        // Report back
        const clients = await self.clients.matchAll();
        clients.forEach((client) =>
          client.postMessage({ type: 'CACHE_PROGRESS', cached, total: urls.length })
        );
      })
    );
  }

  if (event.data && event.data.type === 'GET_CACHE_STATS') {
    event.waitUntil(
      caches.open(IMG_CACHE).then(async (cache) => {
        const keys = await cache.keys();
        const clients = await self.clients.matchAll();
        clients.forEach((client) =>
          client.postMessage({ type: 'CACHE_STATS', count: keys.length })
        );
      })
    );
  }
});
