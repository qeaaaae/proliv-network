import { readBody } from 'h3'
import { requireUser } from '../utils/session'
import { hasShopBackend, shopFetch } from '../utils/backend'

export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{ code?: string }>(event)
  const code = (body?.code || '').trim()
  if (!code) throw createError({ statusCode: 400, statusMessage: 'Введите промокод' })

  const res = await shopFetch<{ ok?: boolean; effect_summary?: string; detail?: string }>(
    event,
    '/api/promo/apply',
    { method: 'POST', body: { code } },
  )
  return { ok: Boolean(res.ok), message: res.effect_summary || 'Промокод применён' }
})
