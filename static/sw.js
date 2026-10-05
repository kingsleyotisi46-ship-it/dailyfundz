// DAILYFUNDZBOOST Service Worker - PWA Support for Android
const CACHE_NAME = 'dailyfundzboost-v2';
const OFFLINE_URL = '/offline/';

// Assets to cache immediately
const PRECACHE_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/manifest.json',
  '/offline/',
  'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install event - cache essential assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app shell');
        return cache.addAll(PRECACHE_ASSETS);
      })
      .then(() => {
        self.skipWaiting();
      })
      .catch((err) => {
        console.log('[SW] Cache failed:', err);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip API requests - always go to network
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/admin/') ||
      event.request.url.includes('/login/') ||
      event.request.url.includes('/register/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          // Return cached version
          return cachedResponse;
        }

        // Not in cache, fetch from network
        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response
            const responseToCache = response.clone();

            // Cache successful responses
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return response;
          })
          .catch(() => {
            // Network failed, return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
          });
      })
  );
});

// Background sync for orders (when back online)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-orders') {
    console.log('[SW] Syncing orders...');
    event.waitUntil(syncOrders());
  }
});

async function syncOrders() {
  // Sync any pending orders when back online
  const pendingOrders = await getFromIndexedDB('pending-orders');
  for (const order of pendingOrders) {
    try {
      await fetch('/api/orders/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(order)
      });
      await removeFromIndexedDB('pending-orders', order.id);
    } catch (err) {
      console.log('[SW] Sync failed for order:', order.id);
    }
  }
}

// Push notifications
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New notification from DAILYFUNDZBOOST',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      { action: 'view', title: 'View', icon: '/static/icons/icon-72x72.png' },
      { action: 'close', title: 'Close', icon: '/static/icons/icon-72x72.png' }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('DAILYFUNDZBOOST', options)
  );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/dashboard/')
    );
  }
});

// Helper functions for IndexedDB (simplified)
function getFromIndexedDB(storeName) {
  return Promise.resolve([]);
}

function removeFromIndexedDB(storeName, id) {
  return Promise.resolve();
}
