// Минимальный service worker: нужен только чтобы браузер считал
// приложение installable (PWA -> «Добавить на экран»). Ничего не кэшируем:
// кабинет - live-данные, оффлайн-кэш тут вреден.
self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()))
self.addEventListener('fetch', () => {})
