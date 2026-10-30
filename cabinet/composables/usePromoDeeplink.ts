// Промо-диплинки Mini App: t.me/<bot>?startapp=promo_<code> и кнопка
// «Открыть Mini App» в боте несут код в start_param или в query. Код не
// активируется при открытии - захватываем его до редиректа на /auth и
// ведём на /account с подставленным полем, жмёт юзер сам.
const KEY = 'proliv_promo_pending'
const DONE = 'proliv_promo_consumed'
const CODE_RE = /^[A-Za-z0-9_-]{1,59}$/

export function usePromoDeeplink() {
  function telegramStartParam(): string {
    if (!import.meta.client) return ''
    try {
      return (
        (window as { Telegram?: { WebApp?: { initDataUnsafe?: { start_param?: string } } } }).Telegram
          ?.WebApp?.initDataUnsafe?.start_param || ''
      )
    } catch {
      return ''
    }
  }

  // start_param-носители обязаны иметь префикс promo_ - в них же ездят
  // рефералки и роуты; ?promo=/promo_code= принимаем и голый код.
  function normalize(value: unknown, prefixedOnly: boolean): string {
    const raw = Array.isArray(value) ? value[0] : value
    if (typeof raw !== 'string') return ''
    const trimmed = raw.trim()
    const bare = trimmed.toLowerCase().startsWith('promo_') ? trimmed.slice(6) : trimmed
    if (!bare || !CODE_RE.test(bare)) return ''
    return prefixedOnly && !trimmed.toLowerCase().startsWith('promo_') ? '' : bare
  }

  function capture(query: Record<string, unknown>) {
    if (!import.meta.client) return
    const code =
      normalize(query.startapp, true) ||
      normalize(query.start_param, true) ||
      normalize(query.tgWebAppStartParam, true) ||
      normalize(telegramStartParam(), true) ||
      normalize(query.promo, false) ||
      normalize(query.promo_code, false)
    if (!code || sessionStorage.getItem(DONE) === code) return
    sessionStorage.setItem(KEY, code)
  }

  function code(): string {
    if (!import.meta.client) return ''
    return sessionStorage.getItem(KEY) || ''
  }

  // Помечаем код отработанным: initDataUnsafe.start_param живёт всю сессию
  // WebView, без этого каждый переход по кабинету редиректил бы на /account.
  function consume(): string {
    if (!import.meta.client) return ''
    const pending = code()
    if (pending) {
      sessionStorage.setItem(DONE, pending)
      sessionStorage.removeItem(KEY)
    }
    return pending
  }

  return { capture, code, consume }
}
