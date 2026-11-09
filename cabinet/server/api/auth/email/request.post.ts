import { readBody } from 'h3'
import { ofetch } from 'ofetch'
import { shopApiUrl } from '../../../utils/backend'
import { throwEmailAuthError } from '../../../utils/emailAuth'

// Запрос одноразового кода на почту (upstream POST /api/auth/email/request).
// Письмо отправляет бэкенд через SMTP - ответ может идти несколько секунд.
export default defineEventHandler(async (event) => {
  const base = shopApiUrl(event)
  if (!base) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{
    email?: string
    referralCode?: string
    startParam?: string
  }>(event)
  const email = (body?.email || '').trim()
  if (!email) {
    throw createError({ statusCode: 400, statusMessage: 'Введите email' })
  }

  try {
    return await ofetch(`${base}/api/auth/email/request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'Accept-Encoding': 'identity',
      },
      body: JSON.stringify({
        email,
        language: 'ru',
        referral_code: body?.referralCode || undefined,
        start_param: body?.startParam || undefined,
      }),
      timeout: 30000,
    })
  } catch (err) {
    throwEmailAuthError(err, 'Не удалось отправить код')
  }
})
