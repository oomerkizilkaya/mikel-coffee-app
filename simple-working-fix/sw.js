const CACHE_NAME = 'mikel-coffee-pwa-v2.0.0';
const STATIC_CACHE = 'mikel-coffee-static-v2.0.0';
const DYNAMIC_CACHE = 'mikel-coffee-dynamic-v2.0.0';

// Critical files to cache immediately
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  'https://customer-assets.emergentagent.com/job_0f64345d-2f6b-41c8-af15-208e01ade896/artifacts/fwptedkg_M%C4%B0KEL%20LOGOSU.png'
];

// Files to cache on-demand
const DYNAMIC_CACHE_LIMIT = 50;

// Install Event - Cache essential resources
self.addEventListener('install', event => {
  console.log('⚡ PWA installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('✅ PWA caching static files');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('✅ PWA installation complete');
        return self.skipWaiting(); // Force activate
      })
  );
});

// Activate Event - Clean old caches
self.addEventListener('activate', event => {
  console.log('⚡ PWA activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            console.log('🧹 PWA deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('✅ PWA activation complete');
      return self.clients.claim(); // Take control immediately
    })
  );
});

// Fetch Event - Smart caching strategy
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip cross-origin requests that aren't API calls
  if (url.origin !== location.origin && !url.pathname.startsWith('/api')) {
    return;
  }
  
  event.respondWith(
    handleFetch(request)
  );
});

async function handleFetch(request) {
  const url = new URL(request.url);
  
  // API requests - Network first with cache fallback
  if (url.pathname.startsWith('/api')) {
    return networkFirstStrategy(request);
  }
  
  // Static assets - Cache first
  if (url.pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot)$/)) {
    return cacheFirstStrategy(request);
  }
  
  // HTML pages - Network first with cache fallback
  return networkFirstStrategy(request);
}

async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.status === 200) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
      await limitCacheSize(DYNAMIC_CACHE, DYNAMIC_CACHE_LIMIT);
    }
    
    return networkResponse;
  } catch (error) {
    console.log('📱 PWA serving from cache (offline):', request.url);
    const cacheResponse = await caches.match(request);
    
    if (cacheResponse) {
      return cacheResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/');
    }
    
    throw error;
  }
}

async function cacheFirstStrategy(request) {
  const cacheResponse = await caches.match(request);
  
  if (cacheResponse) {
    return cacheResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    const cache = await caches.open(STATIC_CACHE);
    cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    console.log('❌ PWA fetch failed:', request.url);
    throw error;
  }
}

async function limitCacheSize(cacheName, limit) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  
  if (keys.length > limit) {
    // Delete oldest entries
    const deleteCount = keys.length - limit;
    for (let i = 0; i < deleteCount; i++) {
      await cache.delete(keys[i]);
    }
  }
}

// Background sync for offline functionality
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  return Promise.resolve();
}

// Push notifications handler
self.addEventListener('push', event => {
  console.log('📱 PUSH RECEIVED - Push notification received:', event);
  
  let data = {};
  let title = 'Mikel Coffee';
  let body = 'Yeni bildirim var!';
  
  if (event.data) {
    try {
      data = event.data.json();
      title = data.title || 'Mikel Coffee';
      body = data.body || data.message || 'Yeni bildirim var!';
    } catch (e) {
      console.log('📱 PUSH RECEIVED - Using text data:', event.data.text());
      body = event.data.text() || 'Yeni bildirim var!';
    }
  }

  const options = {
    body: body,
    icon: 'https://customer-assets.emergentagent.com/job_0f64345d-2f6b-41c8-af15-208e01ade896/artifacts/fwptedkg_M%C4%B0KEL%20LOGOSU.png',
    badge: 'https://customer-assets.emergentagent.com/job_0f64345d-2f6b-41c8-af15-208e01ade896/artifacts/fwptedkg_M%C4%B0KEL%20LOGOSU.png',
    tag: 'mikel-coffee-notification',
    data: data,
    requireInteraction: true,
    vibrate: [200, 100, 200], // Telefon için titreşim
    actions: [
      {
        action: 'view',
        title: '👀 Görüntüle'
      },
      {
        action: 'dismiss',
        title: '❌ Kapat'
      }
    ]
  };
  
  console.log('📱 PUSH RECEIVED - Showing notification:', title, options);
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification click - telefon için önemli
self.addEventListener('notificationclick', event => {
  console.log('📱 NOTIFICATION CLICKED - Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'view' || !event.action) {
    // Uygulamayı aç
    event.waitUntil(
      clients.matchAll({type: 'window'}).then(clientList => {
        // Zaten açık bir window varsa focus et
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (client.url.includes('baristalink.preview.emergentagent.com') && 'focus' in client) {
            return client.focus();
          }
        }
        // Yoksa yeni window aç
        if (clients.openWindow) {
          return clients.openWindow('https://employee-hub-45.preview.emergentagent.com/');
        }
      })
    );
  }
  // dismiss action için hiçbir şey yapma, sadece kapat
});