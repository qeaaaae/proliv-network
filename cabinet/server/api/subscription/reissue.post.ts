import { createError } from 'h3'
import { requireUser } from '../../utils/session'
import { hasShopBackend, mapDevice, shopFetch, type ShopDevice, type ShopMe } from '../../utils/backend'

// Перевыпуск ссылки подписки через бэкенд (revoke + новая ссылка,
// устройства сбрасываются на стороне Remnawave)
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }

  await shopFetch(event, '/api/subscription/reissue', { method: 'POST', body: {} })

  const [me, dev] = await Promise.all([
    shopFetch<ShopMe>(event, '/api/me').catch(() => null),
    shopFetch<{ devices?: ShopDevice[] }>(event, '/api/devices').catch(() => null),
  ])

  return {
    ok: true,
    subscriptionUrl: me?.subscription?.config_link || me?.subscription?.connect_url || '',
    devices: (dev?.devices ?? []).map(mapDevice),
  }
})
