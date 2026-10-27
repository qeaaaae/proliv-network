import { readBody } from 'h3'
import { requireUser } from '../utils/session'
import { hasShopBackend, mapSettings, shopFetch, type ShopMe } from '../utils/backend'

// Фронт шлёт только изменённый ключ ({notifyExpiry: bool} и т.п.), а upstream
// принимает полный снимок NotificationPreferencesPatchBody - мержим с текущими.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{ notifyExpiry?: boolean; notifyNews?: boolean; notifySecurity?: boolean }>(event)

  const me = await shopFetch<ShopMe>(event, '/api/me')
  const prefs = me.user?.notification_preferences ?? {}

  const patch = {
    system_telegram: body?.notifyExpiry ?? prefs.system_telegram ?? true,
    marketing_telegram: body?.notifyNews ?? prefs.marketing_telegram ?? true,
    system_email: body?.notifySecurity ?? prefs.system_email ?? true,
    marketing_email: prefs.marketing_email ?? false,
  }

  const res = await shopFetch<{ notification_preferences?: Record<string, boolean> }>(
    event,
    '/api/account/notification-preferences',
    { method: 'POST', body: patch },
  )
  return { ok: true, settings: mapSettings(res.notification_preferences ?? patch) }
})
