'use strict';

// Persistent Service Worker for Gumli
// Satisfies PWA criteria to allow installing as a standalone app with a home screen icon.

const CACHE_NAME = 'gumli-v2';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Pass-through fetch handler to ensure installability while keeping resources strictly fresh from network
  event.respondWith(fetch(event.request));
});
