import { readBody } from 'h3'
import { requireUser } from '../../utils/session'
import { hasShopBackend, shopFetch } from '../../utils/backend'

// Переключение автопродления подписки (баланс/провайдер - решает бэкенд).
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{ enabled?: boolean; confirmCancel?: boolean }>(event)
  const res = await shopFetch<{
    ok?: boolean
    auto_renew_enabled?: boolean
    provider?: string
    provider_label?: string
  }>(event, '/api/subscription/auto-renew', {
    method: 'POST',
    body: {
      enabled: Boolean(body?.enabled),
      creator_cancellation_confirmed: Boolean(body?.confirmCancel),
    },
  })
  return {
    ok: Boolean(res.ok),
    enabled: Boolean(res.auto_renew_enabled),
    provider: res.provider ?? '',
    providerLabel: res.provider_label ?? '',
  }
})
