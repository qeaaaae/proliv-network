import { readBody } from 'h3'
import { requireUser } from '../../../utils/session'
import { shopFetch } from '../../../utils/backend'
import { throwEmailAuthError } from '../../../utils/emailAuth'

// Привязка почты к текущему аккаунту: шлём код на указанный email
// (upstream POST /api/account/email/request).
export default defineEventHandler(async (event) => {
  requireUser(event)
  const body = await readBody<{ email?: string }>(event)
  const email = (body?.email || '').trim()
  if (!email) {
    throw createError({ statusCode: 400, statusMessage: 'Введите email' })
  }
  try {
    return await shopFetch<{ ok?: boolean; already_linked?: boolean }>(
      event,
      '/api/account/email/request',
      { method: 'POST', body: { email } },
    )
  } catch (err) {
    throwEmailAuthError(err, 'Не удалось отправить код')
  }
})
