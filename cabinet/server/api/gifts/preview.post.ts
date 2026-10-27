import { readBody } from 'h3'
import { requireUser } from '../../utils/session'
import { hasShopBackend, shopFetch } from '../../utils/backend'

// Превью подарка по токену из подарочной ссылки (?gift=<token>, 43 chars).
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{ token?: string }>(event)
  const token = (body?.token || '').trim()
  if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
    throw createError({ statusCode: 400, statusMessage: 'Некорректный код подарка' })
  }
  return await shopFetch<Record<string, unknown>>(event, '/api/gifts/preview', {
    method: 'POST',
    body: { token },
  })
})
