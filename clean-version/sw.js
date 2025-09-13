const CACHE_NAME = 'mikel-coffee-v3.0.0';
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  'https://customer-assets.emergentagent.com/job_0f64345d-2f6b-41c8-af15-208e01ade896/artifacts/fwptedkg_M%C4%B0KEL%20LOGOSU.png'
];

// Install Event
self.addEventListener('install', event => {
  console.log('⚡ PWA installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('✅ Caching files');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('✅ PWA installation complete');
        return self.skipWaiting();
      })
  );
});

// Activate Event
self.addEventListener('activate', event => {
  console.log('⚡ PWA activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('🧹 Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('✅ PWA activation complete');
      return self.clients.claim();
    })
  );
});

// Fetch Event
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        return response || fetch(event.request).then(fetchResponse => {
          // Cache successful responses
          if (fetchResponse.status === 200) {
            const responseClone = fetchResponse.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, responseClone);
            });
          }
          return fetchResponse;
        });
      })
      .catch(() => {
        // Offline fallback
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      })
  );
});

// Push Notification Events
self.addEventListener('push', event => {
  console.log('🔔 Push notification received');
  
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body || 'Yeni bildirim',
      icon: 'https://customer-assets.emergentagent.com/job_0f64345d-2f6b-41c8-af15-208e01ade896/artifacts/fwptedkg_M%C4%B0KEL%20LOGOSU.png',
      badge: 'https://customer-assets.emergentagent.com/job_0f64345d-2f6b-41c8-af15-208e01ade896/artifacts/fwptedkg_M%C4%B0KEL%20LOGOSU.png',
      vibrate: [200, 100, 200],
      data: data,
      actions: [
        { action: 'open', title: 'Aç' },
        { action: 'dismiss', title: 'Kapat' }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'Mikel Coffee', options)
    );
  }
});

self.addEventListener('notificationclick', event => {
  console.log('🔔 Notification clicked');
  event.notification.close();
  
  if (event.action === 'open') {
    event.waitUntil(clients.openWindow('/'));
  }
});