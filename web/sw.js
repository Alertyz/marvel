// ═══════════════════════════════════════════════════════════
//  SERVICE WORKER — Offline-first Comic Reader
// ═══════════════════════════════════════════════════════════

const APP_CACHE = 'marvel-app-v4';
const IMG_CACHE = 'marvel-images-v1';
const API_CACHE = 'marvel-api-v4';

// App shell files to pre-cache
const APP_SHELL = ['./', './manifest.json', './icon-192.png', './icon-512.png'];

// Offline fallback HTML page (embedded to avoid extra request)
const OFFLINE_HTML = `<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Marvel Reader — Offline</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0f;color:#e0e0f0;
min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:20px}
.box{max-width:400px}
h1{font-size:2rem;margin-bottom:12px;background:linear-gradient(135deg,#f0c040,#e04060);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
p{color:#8888aa;margin-bottom:16px;line-height:1.5}
.retry{background:linear-gradient(135deg,#f0c040,#e09030);color:#0a0a0f;border:none;border-radius:8px;
padding:10px 24px;font-weight:600;font-size:.9rem;cursor:pointer;font-family:inherit}
.retry:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(240,192,64,.3)}
.offline-icon{font-size:3rem;margin-bottom:16px}
.hint{font-size:.75rem;color:#666;margin-top:20px}
</style></head><body>
<div class="box">
<div class="offline-icon">📡</div>
<h1>Sem Conexão</h1>
<p>O servidor não está acessível no momento.<br>
As edições que você já leu continuam disponíveis no cache.</p>
<button class="retry" onclick="location.reload()">🔄 Tentar Novamente</button>
<p class="hint">Verifique se o servidor está rodando e se você está na mesma rede Wi-Fi.</p>
</div></body></html>`;


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
    ).then(() => self.clients.claim())
  );
});

// ── Fetch strategy ────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Comic page images: cache-first (large, rarely change) — works for both same-origin and cross-origin
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

  // Only cache same-origin requests for app shell
  if (url.origin === self.location.origin) {
    event.respondWith(networkFirst(event.request, APP_CACHE));
  }
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

    // For navigation (HTML) requests, return offline page
    if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
      return new Response(OFFLINE_HTML, {
        status: 503,
        headers: { 'Content-Type': 'text/html; charset=utf-8' },
      });
    }

    return new Response(JSON.stringify({ offline: true }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

// ── Message handling for cache management ─────────────────
self.addEventListener('message', (event) => {
  if (!event.data || !event.data.type) return;

  if (event.data.type === 'CACHE_IMAGES') {
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

  if (event.data.type === 'GET_CACHE_STATS') {
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

  // Detailed cache info: group by issue, estimate sizes
  if (event.data.type === 'GET_CACHE_DETAILS') {
    event.waitUntil(
      caches.open(IMG_CACHE).then(async (cache) => {
        const keys = await cache.keys();
        const issues = {}; // orderNum -> { count, size }
        let totalSize = 0;

        for (const req of keys) {
          const url = new URL(req.url);
          const match = url.pathname.match(/^\/api\/issues\/(\d+)\/page\/(\d+)$/);
          if (match) {
            const orderNum = parseInt(match[1]);
            if (!issues[orderNum]) issues[orderNum] = { count: 0, size: 0 };
            issues[orderNum].count++;
            try {
              const resp = await cache.match(req);
              if (resp) {
                const blob = await resp.clone().blob();
                issues[orderNum].size += blob.size;
                totalSize += blob.size;
              }
            } catch { /* skip size calc */ }
          }
        }

        const clients = await self.clients.matchAll();
        clients.forEach((client) =>
          client.postMessage({
            type: 'CACHE_DETAILS',
            totalCount: keys.length,
            totalSize,
            issues, // { orderNum: { count, size } }
          })
        );
      })
    );
  }

  // Clear all cached images
  if (event.data.type === 'CLEAR_ALL_CACHE') {
    event.waitUntil(
      caches.delete(IMG_CACHE).then(async () => {
        // Recreate empty cache
        await caches.open(IMG_CACHE);
        const clients = await self.clients.matchAll();
        clients.forEach((client) =>
          client.postMessage({ type: 'CACHE_CLEARED' })
        );
      })
    );
  }

  // Batch download: cache images for multiple issues with progress reporting
  if (event.data.type === 'BATCH_CACHE_IMAGES') {
    const issues = event.data.issues || []; // [{ orderNum, totalPages, title }]
    const apiBase = event.data.apiBase || '';
    event.waitUntil(
      caches.open(IMG_CACHE).then(async (cache) => {
        let totalUrls = 0;
        let cachedUrls = 0;
        let skippedUrls = 0;
        for (const iss of issues) {
          totalUrls += iss.totalPages;
        }

        const clients = await self.clients.matchAll();
        const broadcast = (msg) => clients.forEach(c => c.postMessage(msg));

        for (const iss of issues) {
          for (let p = 1; p <= iss.totalPages; p++) {
            const url = apiBase + `/api/issues/${iss.orderNum}/page/${p}`;
            const exists = await cache.match(url);
            if (exists) {
              skippedUrls++;
              cachedUrls++;
            } else {
              try {
                const resp = await fetch(url);
                if (resp.ok) {
                  await cache.put(url, resp);
                  cachedUrls++;
                }
              } catch { /* skip failed */ }
            }
            // Report progress every page
            broadcast({
              type: 'BATCH_CACHE_PROGRESS',
              current: cachedUrls,
              total: totalUrls,
              skipped: skippedUrls,
              currentIssue: iss.title || `#${iss.orderNum}`,
              currentPage: p,
              issuePages: iss.totalPages,
            });
          }
        }
        broadcast({ type: 'BATCH_CACHE_DONE', cached: cachedUrls, total: totalUrls, skipped: skippedUrls });
      })
    );
  }

  // Clear cache for a specific issue
  if (event.data.type === 'CLEAR_ISSUE_CACHE') {
    const orderNum = event.data.orderNum;
    event.waitUntil(
      caches.open(IMG_CACHE).then(async (cache) => {
        const keys = await cache.keys();
        let deleted = 0;
        for (const req of keys) {
          const url = new URL(req.url);
          const match = url.pathname.match(/^\/api\/issues\/(\d+)\/page\/\d+$/);
          if (match && parseInt(match[1]) === orderNum) {
            await cache.delete(req);
            deleted++;
          }
        }
        const clients = await self.clients.matchAll();
        clients.forEach((client) =>
          client.postMessage({ type: 'ISSUE_CACHE_CLEARED', orderNum, deleted })
        );
      })
    );
  }
});
