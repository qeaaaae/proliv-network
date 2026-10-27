import { requireUser } from '../utils/session'
import { hasShopBackend, shopFetch } from '../utils/backend'

// Активация пробного периода. Кнопка "Пробный период" в боте ведёт на
// {MINI_APP}/trial - в стоковом webapp это экран активации, у нас - эта
// страница дергает POST /api/trial -> shop /api/trial/activate.
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const res = await shopFetch<{ activated?: boolean; message_key?: string }>(
    event,
    '/api/trial/activate',
    { method: 'POST', body: {} },
  )
  const me = await shopFetch<{ subscription?: { days_left?: number } }>(event, '/api/me').catch(
    () => null,
  )
  return { ...res, days_left: me?.subscription?.days_left }
})
