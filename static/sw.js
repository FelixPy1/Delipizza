const CACHE_NAME = 'deli-pizza-v3';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/styles.css',
  '/static/icons/icono.jpeg',
  '/static/js/app.js',
  '/static/js/notes.js',
  '/static/manifest.json',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap'
];

// Instalar el Service Worker y guardar en caché
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(ASSETS_TO_CACHE))
      .then(() => self.skipWaiting())
  );
});

// Limpiar cachés antiguos si hay una nueva versión
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Interceptar peticiones
self.addEventListener('fetch', (event) => {
  // Las peticiones a la API no se cachean con esta estrategia
  // (La lógica offline de ventas se manejará directamente en app.js)
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/logout') || 
      event.request.url.includes('/login') ||
      event.request.method !== 'GET') {
    return;
  }

  // Si es una petición de navegación (páginas HTML), usamos: Red primero, luego Caché
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Actualizar caché dinámica si es exitoso
          if (response && response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Si falla la red, intentar buscar en caché
          return caches.match(event.request);
        })
    );
    return;
  }

  // Estrategia para archivos estáticos: Caché primero, luego red
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response; // Devolver desde el caché
        }
        return fetch(event.request).then((fetchResponse) => {
          // Guardar dinámicamente nuevos recursos
          if (fetchResponse && fetchResponse.status === 200) {
            const responseClone = fetchResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return fetchResponse;
        });
      })
  );
});
