import { requireUser } from '../../utils/session'
import { hasShopBackend, shopFetch, type ShopTopupOptions } from '../../utils/backend'

// Пакеты докупки HWID-устройств (прорейтированные квоты бэкенда).
// На бэкенде требует MY_DEVICES_SECTION_ENABLED и тарифную подписку.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  return await shopFetch<ShopTopupOptions>(event, '/api/devices/topup-options')
})
