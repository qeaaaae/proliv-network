import { readBody } from 'h3'
import { getCabinetSession, requireUser, setSession } from '../../../utils/session'
import { shopFetch } from '../../../utils/backend'
import { throwEmailAuthError, type ShopAuthTokenResponse } from '../../../utils/emailAuth'

// Подтверждение привязки почты кодом (upstream POST /api/account/email/verify).
// Upstream при ответе переиздаёт webapp-токен - подхватываем его в сессию.
export default defineEventHandler(async (event) => {
  requireUser(event)
  const body = await readBody<{ email?: string; code?: string }>(event)
  const email = (body?.email || '').trim()
  const code = (body?.code || '').trim()
  if (!email || !code) {
    throw createError({ statusCode: 400, statusMessage: 'Введите email и код' })
  }
  let res: ShopAuthTokenResponse
  try {
    res = await shopFetch<ShopAuthTokenResponse>(event, '/api/account/email/verify', {
      method: 'POST',
      body: { email, code },
    })
  } catch (err) {
    throwEmailAuthError(err, 'Неверный код')
  }
  const session = getCabinetSession(event)
  if (session && res?.token) {
    setSession(event, { ...session, apiToken: res.token, apiCsrf: res.csrf_token || session.apiCsrf })
  }
  return { ok: true }
})
