// Реферальная атрибуция веба: лендинг/партнёрские ссылки ведут на
// /?ref=u<code>. Код сохраняем в localStorage на 30 дней (как заявлено
// в политике) и прикладываем к /api/auth/telegram при входе.
const KEY = 'proliv_ref'
const TTL_MS = 30 * 24 * 3600 * 1000

export function useReferral() {
  function capture(query: Record<string, unknown>) {
    if (!import.meta.client) return
    const raw = query.ref ?? query.start
    const value = Array.isArray(raw) ? raw[0] : raw
    if (typeof value === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(value)) {
      localStorage.setItem(KEY, JSON.stringify({ code: value, ts: Date.now() }))
    }
  }

  function code(): string | null {
    if (!import.meta.client) return null
    try {
      const raw = localStorage.getItem(KEY)
      if (!raw) return null
      const item = JSON.parse(raw) as { code?: string; ts?: number }
      if (!item.code || !item.ts || Date.now() - item.ts > TTL_MS) return null
      return item.code
    } catch {
      return null
    }
  }

  function clear() {
    if (!import.meta.client) return
    localStorage.removeItem(KEY)
  }

  return { capture, code, clear }
}
