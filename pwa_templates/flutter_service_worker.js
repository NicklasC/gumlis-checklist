'use strict';

// Replaced with the app archive content hash during deployment.
const BUILD_VERSION = '__APP_ARCHIVE_HASH__';
const CACHE_PREFIX = 'gumli-';
const CACHE_NAME = `${CACHE_PREFIX}${BUILD_VERSION}`;
const RUNTIME_CDN_HOSTS = new Set([
  'cdn.jsdelivr.net',
  'www.gstatic.com',
  'fonts.gstatic.com'
]);

// Keep installation lightweight. Larger runtimes are cached on first use.
const APP_SHELL = [
  './',
  'index.html',
  'manifest.json',
  'favicon.png',
  'flutter_bootstrap.js',
  'python.js',
  'icons/loading-animation.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names
          .filter((name) => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      ))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (response.ok) {
      try {
        await cache.put(request, response.clone());
      } catch (error) {
        console.warn('[GUMLI CACHE] Response could not be cached', request.url, error);
      }
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request, { ignoreSearch: true });
    if (cached) return cached;
    throw error;
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  if (response.ok) {
    try {
      await cache.put(request, response.clone());
    } catch (error) {
      console.warn('[GUMLI CACHE] Response could not be cached', request.url, error);
    }
  }
  return response;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  const isSameOrigin = url.origin === self.location.origin;
  if (!isSameOrigin && !RUNTIME_CDN_HOSTS.has(url.hostname)) return;

  if (isSameOrigin && (request.mode === 'navigate' || url.pathname.endsWith('/index.html'))) {
    event.respondWith(networkFirst(request));
    return;
  }

  event.respondWith(cacheFirst(request));
});
