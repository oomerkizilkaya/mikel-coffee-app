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
          return clients.openWindow('https://baristalink.preview.emergentagent.com/');
        }
      })
    );
  }
  // dismiss action için hiçbir şey yapma, sadece kapat
});