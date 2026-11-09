// Регистрация PWA service worker'а (нужен для «Установить приложение»).
// Не в Telegram WebView - там SW бесполезен, а риск перехвата запросов лишний.
export default defineNuxtPlugin(() => {
  if (!('serviceWorker' in navigator)) return
  const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram
  if (tg?.WebApp?.initData) return
  navigator.serviceWorker.register('/sw.js').catch(() => {})
})
