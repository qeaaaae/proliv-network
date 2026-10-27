import { requireUser } from '../utils/session'
import { hasShopBackend, mapDevice, shopFetch, type ShopDevice } from '../utils/backend'

// Устройства приходят из Remnawave через бэкенд (HWID-устройства)
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }

  const res = await shopFetch<{ devices?: ShopDevice[]; max_devices?: number | null }>(event, '/api/devices')
  return {
    devices: (res.devices ?? []).map(mapDevice),
    deviceLimit: res.max_devices ?? 0,
  }
})
