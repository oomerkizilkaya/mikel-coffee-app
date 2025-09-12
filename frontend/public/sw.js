const CACHE_NAME = 'mikel-coffee-v1.0.0';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/assets/images/icon.png',
  '/assets/images/adaptive-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

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
  console.log('📱 Push notification received:', event);
  
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: 'Mikel Coffee', body: event.data.text() };
    }
  }

  const options = {
    body: data.body || 'Yeni bildirim var!',
    icon: '/assets/images/icon.png',
    badge: '/assets/images/icon.png',
    tag: 'mikel-coffee-notification',
    data: data,
    actions: [
      {
        action: 'view',
        title: 'Görüntüle'
      },
      {
        action: 'dismiss',
        title: 'Kapat'
      }
    ],
    requireInteraction: true
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Mikel Coffee', options)
  );
});

// Handle notification click
self.addEventListener('notificationclick', event => {
  console.log('📱 Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'view' || !event.action) {
    event.waitUntil(
      clients.openWindow('https://baristalink.preview.emergentagent.com/')
    );
  }
});