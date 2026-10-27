import { createError, getRouterParam } from 'h3'
import { requireUser } from '../../../utils/session'
import { hasShopBackend, mapDevice, shopFetch, type ShopDevice } from '../../../utils/backend'

// Отвязать устройство по HWID (token = id устройства в API)
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const id = getRouterParam(event, 'id')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'No device id' })

  await shopFetch(event, '/api/devices/disconnect', { method: 'POST', body: { token: id } })

  const res = await shopFetch<{ devices?: ShopDevice[] }>(event, '/api/devices').catch(() => null)
  return { ok: true, devices: (res?.devices ?? []).map(mapDevice) }
})
