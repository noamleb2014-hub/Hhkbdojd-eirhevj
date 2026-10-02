/* SkyFinder service worker
 * ---------------------------------------------------------------------------
 * Strategy
 *   navigation  -> network first, fall back to the cached shell (offline launch)
 *   same-origin -> stale-while-revalidate (instant load, refreshed in background)
 *   cross-origin-> stale-while-revalidate (Google Fonts; opaque responses are
 *                  cached so the page keeps its typography offline)
 *
 * Bump CACHE_VERSION on every deploy to roll the old caches over.
 */
var CACHE_VERSION = 'v1.0.0';
var CORE = 'skyfinder-core-' + CACHE_VERSION;
var RUNTIME = 'skyfinder-runtime-' + CACHE_VERSION;

/* The app shell. Everything the page needs to boot with no network. */
var PRECACHE = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
  './icons/apple-touch-icon.png',
  './icons/favicon-32.png',
  './icons/favicon.ico',
  './icons/favicon.svg'
];

/* Never cache these — they must always hit the network. */
var NEVER_CACHE = /(\/sw\.js$|\/manifest\.webmanifest$)/;

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CORE).then(function (cache) {
      // Cache each asset independently so one 404 cannot fail the whole install.
      return Promise.all(
        PRECACHE.map(function (url) {
          return cache.add(new Request(url, { cache: 'reload' })).catch(function () {
            return undefined;
          });
        })
      );
    }).then(function () {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.map(function (key) {
          if (key !== CORE && key !== RUNTIME) return caches.delete(key);
          return undefined;
        })
      );
    }).then(function () {
      return self.clients.claim();
    })
  );
});

/* A manual "update now" escape hatch, e.g. from a future update toast. */
self.addEventListener('message', function (event) {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});

function isCacheable(response) {
  if (!response) return false;
  // Opaque (cross-origin, no-cors) responses are fine to store for our fonts.
  if (response.type === 'opaque') return true;
  return response.status === 200 && response.type === 'basic';
}

/* Network-first, used for page navigations so a deploy is picked up quickly
 * while still working completely offline. */
function networkFirst(request) {
  return fetch(request)
    .then(function (response) {
      if (isCacheable(response)) {
        var copy = response.clone();
        caches.open(CORE).then(function (cache) { cache.put(request, copy); });
      }
      return response;
    })
    .catch(function () {
      return caches.match(request).then(function (hit) {
        if (hit) return hit;
        return caches.match('./index.html').then(function (shell) {
          if (shell) return shell;
          return new Response('Offline', {
            status: 503,
            statusText: 'Offline',
            headers: { 'Content-Type': 'text/plain' }
          });
        });
      });
    });
}

/* Stale-while-revalidate for everything else. */
function staleWhileRevalidate(request) {
  return caches.match(request).then(function (cached) {
    var network = fetch(request)
      .then(function (response) {
        if (isCacheable(response)) {
          var copy = response.clone();
          caches.open(RUNTIME).then(function (cache) { cache.put(request, copy); });
        }
        return response;
      })
      .catch(function () {
        return cached || Response.error();
      });
    return cached || network;
  });
}

self.addEventListener('fetch', function (event) {
  var request = event.request;

  if (request.method !== 'GET') return;

  var url;
  try {
    url = new URL(request.url);
  } catch (e) {
    return;
  }

  // Chrome extension schemes and other non-http requests.
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

  if (NEVER_CACHE.test(url.pathname)) return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
    return;
  }

  if (url.origin === self.location.origin) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  // Cross-origin: only bother with fonts, so we don't hoard third-party junk.
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(staleWhileRevalidate(request));
  }
});
